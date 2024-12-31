import paramiko
import os
from scp import SCPClient  # Install with `pip install scp`
import logging

# Constants
KEY_PATH = "/home/admin/.ssh/id_ed25519"
USERNAME = "ansible"
SERVERS_FILE = "/home/admin/syxback/"  # File containing the list of server IPs
LOCAL_DIR = "/path/to/local/directory"  # Path to the directory you want to copy
REMOTE_DIR = "/path/to/remote/destination"  # Remote directory to copy to
REMOTE_COMMAND = f"ls -l {REMOTE_DIR}"  # Command to execute on the remote server

# Logging setup
logging.basicConfig(level=logging.INFO)


def load_servers(file_path):
    """
    Load server addresses from a file.
    """
    try:
        with open(file_path, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        logging.error(f"Servers file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading servers file: {e}")
        raise


def create_ssh_client(ip):
    """
    Create and return an SSH client connected to the specified IP.
    """
    try:
        private_key = paramiko.Ed25519Key(filename=KEY_PATH)
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=ip, username=USERNAME, pkey=private_key)
        return ssh_client
    except paramiko.AuthenticationException:
        logging.error(f"Authentication failed for {ip}. Please check credentials.")
    except paramiko.SSHException as e:
        logging.error(f"SSH connection failed for {ip}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred for {ip}: {e}")
    return None


def copy_directory(ssh_client, local_dir, remote_dir):
    """
    Copy a directory from local to remote server using SCP.
    """
    try:
        with SCPClient(ssh_client.get_transport()) as scp:
            logging.info(f"Copying {local_dir} to {remote_dir}...")
            scp.put(local_dir, remote_path=remote_dir, recursive=True)
            logging.info("File transfer completed successfully!")
    except Exception as e:
        logging.error(f"File transfer failed: {e}")
        raise


def execute_remote_command(ssh_client, command):
    """
    Execute a remote command and log the output.
    """
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        if output:
            logging.info(f"Command output:\n{output}")
        if error:
            logging.warning(f"Command error:\n{error}")
    except Exception as e:
        logging.error(f"Error executing remote command: {e}")
        raise


def main():
    """
    Main function to copy a directory to all servers and execute a command.
    """
    try:
        servers = load_servers(SERVERS_FILE)
        for server_ip in servers:
            logging.info(f"Processing server: {server_ip}")
            ssh_client = create_ssh_client(server_ip)
            if ssh_client:
                try:
                    # Copy directory
                    copy_directory(ssh_client, LOCAL_DIR, REMOTE_DIR)
                    # Execute remote command
                    execute_remote_command(ssh_client, REMOTE_COMMAND)
                except Exception as e:
                    logging.error(f"Error during operations for {server_ip}: {e}")
                finally:
                    ssh_client.close()
            else:
                logging.error(f"Skipping server {server_ip} due to connection issues.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
