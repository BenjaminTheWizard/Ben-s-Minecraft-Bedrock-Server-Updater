# Hello, make sure to read the READNE.md to make sure you know how to fully operate this code at: https://github.com/BenjaminTheWizard/Ben-s-Minecraft-Bedrock-Server-Updater/blob/main/README.md

import os
import subprocess
import requests
import warnings
from zipfile import ZipFile, BadZipFile
import shutil
import stat
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    mcurl = input("Put download URL here: ")
    current_path = os.getcwd()

    # Create Temporary directory to store the Minecraft server
    temp_dir = os.path.join(current_path, "mcserverTemp")
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    else:
        logging.warning("The directory 'mcserverTemp' already exists. Please remove the directory.")
        return

    # Download the server file
    zip_path = os.path.join(temp_dir, "mcserver.zip")

    try:
        logging.info("Gathering zip file from the URL...")
        result = requests.get(mcurl)
        result.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(result.content)
        logging.info("Successfully downloaded and created the zip file.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Please check the URL or your internet connection. {e}")
        return
    except IOError as e:
        logging.error(f"Unable to create ZIP file. {e}")
        return

    # Unzipping the contents
    logging.info("Unzipping the contents...")
    try:
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        logging.info("Done unzipping.")
    except (IOError, BadZipFile) as e:
        logging.error(f"Unable to unzip the file. {e}")
        return

    # Path to the server executable
    executable_path = os.path.join(temp_dir, "bedrock_server")

    # Check if the server executable exists
    if not os.path.isfile(executable_path):
        logging.error(f"Server executable not found: {executable_path}")
        return

    # Ensure the executable has proper permissions
    try:
        st = os.stat(executable_path)
        if not (st.st_mode & stat.S_IEXEC):
            os.chmod(executable_path, st.st_mode | stat.S_IEXEC)
    except Exception as e:
        logging.error(f"Error setting permissions for the executable: {e}")
        return

    # Change to the temp directory to ensure correct working directory
    os.chdir(temp_dir)
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Contents of the directory: {os.listdir(temp_dir)}")

    # Attempt to fetch the server.properties file
    serverPropFile = os.path.join(temp_dir, "server.properties")

    # Check if server.properties exists
    if not os.path.isfile(serverPropFile):
        logging.error(f"File not found: {serverPropFile}")
        return
    
    # Ensure the server.properties file has proper permissions
    try:
        st = os.stat(serverPropFile)
        if not (st.st_mode & stat.S_IEXEC):
            os.chmod(serverPropFile, st.st_mode | stat.S_IEXEC)
    except Exception as e:
        logging.error(f"Error setting permissions for the file: {e}")
        return

    # Attempt to read the server.properties file and append each line to a list
    logging.info("Attempting to change the port number in file 'server.properties' to desired port number...")
    serverPropReadList = []

    # Port numbers to change the minecraft server to.
    port = 4131
    v6port = 4132

    try:
        with open(serverPropFile, "r") as f:
            for line in f:
                serverPropReadList.append(line.strip('\n'))
    except Exception as e:
        logging.error(f"Error reading to the file: {e}")
        return
    
    # Change The server.properties file content by altering the list first

    # Change the server ports
    logging.info("Changing the server ports now...")
    changeServerProp = False
    try:
        for pos in range(len(serverPropReadList)-1):
            if serverPropReadList[pos].startswith("server-port"):
                if serverPropReadList[pos].startswith("server-portv6"):
                    serverPropReadList[pos] = "server-portv6="+str(v6port)
                    logging.info(f"Running temporary server on v6port: {str(v6port)}")
                else:
                    serverPropReadList[pos] = "server-port="+str(port)
                    logging.info(f"Running temporary server on port: {str(port)}")
        changeServerProp = True
        logging.info(f"Successfully using altered list.")
    except Exception as e:
        logging.warning(f"Problem querying the list 'serverPropReadList': {e}")
        changeServerProp = False
        logging.info(f"unsuccessfully using altered list")

    # Overwrite the server.properties
    if changeServerProp:
        logging.info(f"Overwrting server.properties...")
        try:
            with open(serverPropFile, "w") as f:
                for pos in range(len(serverPropReadList)-1):
                    f.write(serverPropReadList[pos]+"\n")
            logging.info(f"Successfully overwritten server.properties.")
        except Exception as e:
            logging.error(f"Problem writing to server.properties: {e}")
            return

    # Attempt to run the Minecraft Bedrock Server
    logging.info("Attempting to execute Minecraft Bedrock server...")
    process = None
    try:
        process = subprocess.Popen(
            [executable_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,  # Use stdin to send commands if required
            text=True
        )

        if process is None:
            logging.warning("An error occurred while starting the Minecraft Bedrock server.")
            return

        # Wait until the server has fully loaded
        server_started = False
        for line in process.stdout:
            print(line, end='')
            if "Server started" in line or "Server is listening on port" in line:
                logging.info("Minecraft Bedrock server is fully loaded.")
                server_started = True
                break

        if not server_started:
            logging.warning("Minecraft Bedrock server did not start properly.")
            return

        # Stop the server
        logging.info("Stopping the Minecraft Bedrock server...")
        try:
            if process.stdin:
                process.stdin.write("stop\n")
                process.stdin.flush()
        except (BrokenPipeError, IOError) as e:
            logging.warning(f"Unable to stop the Bedrock server properly. {e}")

        # Wait for the server process to exit
        process.wait()
        logging.info("Minecraft Bedrock server stopped successfully.")
    except Exception as e:
        logging.error(f"An error occurred while managing the Minecraft Bedrock server: {e}")
    finally:
        # Ensure the process is terminated if an error happened
        if process and process.poll() is None:
            logging.info("Terminating the Minecraft Bedrock server process...")
            process.terminate()
            process.wait()
            logging.info("Minecraft Bedrock server process is terminated.")
    
        # Remove the zip file since this is no longer needed
        logging.info("Deleting the 'mcserver.zip' file...")
        file_path = os.path.join(temp_dir, 'mcserver.zip')

        try:
            os.remove(file_path)
            logging.info(f"File '{file_path}' has been deleted successfully.")
        except FileNotFoundError as e:
            logging.warning(f"File '{file_path}' not found. {e}")
        except PermissionError as e:
            logging.warning(f"Permission denied: '{file_path}'. {e}")
        except Exception as e:
            logging.warning(f"Error occurred: {e}")

        # Replace old Bedrock server file with the new one
        NewBedrockFile = os.path.join(temp_dir, 'bedrock_server')
        OldBedrockFile = os.path.join(current_path, 'bedrock_server')
        logging.info("Replacing old Minecraft bedrock server file with newest version file...")
        try:
            shutil.copy(NewBedrockFile, OldBedrockFile)
            logging.info(f"File '{OldBedrockFile}' has been replaced successfully.")
        except FileNotFoundError as e:
            logging.warning(f"File '{OldBedrockFile}' or '{NewBedrockFile}' not found. {e}")
        except PermissionError as e:
            logging.warning(f"Permission denied. {e}")
        except Exception as e:
            logging.warning(f"An error occurred: {e}")

        # Replace essential directories
        toChange = [
            "definitions",
            "resource_packs",
            "treatments",
            "development_behavior_packs",
            "development_resource_packs",
            "development_skin_packs",
            "behavior_packs",
            "config",
            "premium_cache",
            "minecraftpe"
        ]
        
        for directory in toChange:
            new_dir_path = os.path.join(temp_dir, directory)
            old_dir_path = os.path.join(current_path, directory)
            try:
                if os.path.exists(old_dir_path):
                    shutil.rmtree(old_dir_path)
                shutil.copytree(new_dir_path, old_dir_path)
                logging.info(f"Directory '{old_dir_path}' has been replaced successfully.")
            except FileNotFoundError as e:
                logging.warning(f"Directory '{old_dir_path}' or '{new_dir_path}' not found. {e}")
            except PermissionError as e:
                logging.warning(f"Permission denied. {e}")
            except FileExistsError as e:
                logging.warning(f"Directory '{old_dir_path}' already exists. {e}")
            except Exception as e:
                logging.warning(f"An error occurred: {e}")

        # Clean up the temporary directory
        logging.info("Cleaning the temporary directory...")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info("Temporary directory cleaned up.")

if __name__ == "__main__":   
    main()
