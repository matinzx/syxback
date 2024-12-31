import paramiko
from assets.notification import send
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import subprocess
import os
import json
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("transfer_log.log"),
        logging.StreamHandler()
    ]
)

FAILED_SERVERS_FILE = "failed_servers.json"
YEAR = datetime.datetime.now().year
MONTH = datetime.datetime.now().month
TODAY = datetime.datetime.now().strftime("%d")  # Ensures zero-padded day (e.g., 01, 02, ...)


def get_remote_filename(ssh, remote_directory):
    """Retrieve the filename matching the day + MD5 + .tar.gz pattern from the remote server."""
    try:
        file_pattern = rf"^{TODAY}-[a-f0-9]{{32}}\.tar\.gz$"
        stdin, stdout, stderr = ssh.exec_command(f"ls {remote_directory}")
        files = stdout.read().decode().strip().split()

        for file in files:
            if re.match(file_pattern, file):
                logging.info(f"Found matching remote file: {file}")
                return file

        raise FileNotFoundError(f"No file matching pattern found in {remote_directory}.")
    except Exception as e:
        raise Exception(f"Error retrieving remote file: {e}")


def transfer_tar_gz(hostname, username, local_base_dir, remote_directory, ssh_key=None):
    """Transfer a .tar.gz file from the remote server to the local directory."""
    try:
        # Prepare local directory for the specific server and date
        local_directory = os.path.join(local_base_dir, hostname, str(YEAR), f"{MONTH:02d}")
        if not os.path.exists(local_directory):
            os.makedirs(local_directory)
            logging.info(f"Created directory: {local_directory}")

        # Establish SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, key_filename=ssh_key, timeout=10)

        # Get the remote file name matching the pattern
        remote_file = get_remote_filename(ssh, remote_directory)
        remote_file_path = os.path.join(remote_directory, remote_file)
        local_file_path = os.path.join(local_directory, remote_file)

        # Transfer the file using rsync
        rsync_command = [
            "rsync",
            "-e", f"ssh -o StrictHostKeyChecking=no -i {ssh_key}",
            f"{username}@{hostname}:{remote_file_path}",
            local_file_path
        ]
        result = subprocess.run(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            raise Exception(f"Rsync failed: {result.stderr.decode().strip()}")

        logging.info(f"Successfully transferred {remote_file} from {hostname} to {local_file_path}.")
        ssh.close()
        return f"Transfer of {remote_file} from {hostname} successful."
    except Exception as e:
        logging.error(f"Error transferring from {hostname}: {e}")
        return f"Error transferring from {hostname}: {e}"


def load_failed_servers():
    """Load previously failed servers from a JSON file."""
    if os.path.exists(FAILED_SERVERS_FILE):
        with open(FAILED_SERVERS_FILE, "r") as f:
            return json.load(f)
    return []


def save_failed_servers(failed_servers):
    """Save failed servers to a JSON file."""
    with open(FAILED_SERVERS_FILE, "w") as f:
        json.dump(failed_servers, f, indent=4)


def main():
    username = "ansible"
    ssh_key = "/home/admin/.ssh/id_ed25519"
    local_base_dir = "/mnt/Backups/Hotback"
    remote_directory = f"/home/ansible/Backups/{YEAR}/{MONTH:02d}/"
    max_connections = 20

    # Load server list
    all_servers = load_failed_servers()
    try:
        with open("/home/admin/syxback/servers.json", "r") as f:
            all_servers.extend(json.load(f))
    except FileNotFoundError:
        logging.error("servers.json file not found.")
        return
    except json.JSONDecodeError:
        logging.error("servers.json is not valid JSON.")
        return

    all_servers = list(set(all_servers))
    failed_servers = []

    # Transfer files from servers in parallel
    with ThreadPoolExecutor(max_connections) as executor:
        futures = {
            executor.submit(
                transfer_tar_gz,
                hostname,
                username,
                local_base_dir,
                remote_directory,
                ssh_key
            ): hostname for hostname in all_servers
        }

        for future in as_completed(futures):
            hostname = futures[future]
            try:
                result = future.result()
                logging.info(result)
                if "Error" in result:
                    failed_servers.append(hostname)
            except Exception as e:
                logging.error(f"Error with {hostname}: {e}")
                failed_servers.append(hostname)

    # Save failed servers for retry
    save_failed_servers(failed_servers)
    if failed_servers:
        logging.warning(f"Failed servers saved to {FAILED_SERVERS_FILE}. Retry later.")
        send(f"Backup Transfer: {len(failed_servers)} servers failed. See {FAILED_SERVERS_FILE} for details.")
    else:
        logging.info("All transfers completed successfully!")
        send("Backup Transfer: All servers transferred successfully.")


if __name__ == "__main__":
    main()
