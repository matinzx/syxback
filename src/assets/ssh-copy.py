import os
import paramiko
from notification import send

current_dir = os.path.dirname(os.path.abspath(__file__))
addresses_path = os.path.abspath(os.path.join(current_dir, "../../addresses"))
pathssh = os.path.dirname("/home/admin/.ssh/")

puBkeyPath = pathssh + "/id_ed25519.pub"

# Array to store failed IPs
failed_ips = []


def ssh_copy_id(host, username, password, key, port=22):
    try:
        with open(key, 'r') as f:
            public_key = f.read().strip()
    except FileNotFoundError:
        print(f"Public key not found at {key}. Run 'ssh-keygen' first.")
        failed_ips.append(host)
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port, username, password)

        ssh.exec_command('mkdir -p ~/.ssh && chmod 700 ~/.ssh')
        ssh.exec_command(f'echo "{public_key}" >> ~/.ssh/authorized_keys')
        ssh.exec_command('chmod 600 ~/.ssh/authorized_keys')

        print(f"Public key copied successfully to {host}!")
    except paramiko.AuthenticationException:
        print(f"Authentication failed for {host}. Check username/password.")
        failed_ips.append(host)
    except Exception as e:
        print(f"Error with {host}: {e}")
        failed_ips.append(host)
    finally:
        ssh.close()


with open(addresses_path, "r") as file:
    items = file.read().split()

for item in items:
    try:
        send(ip=item, message="Attempting to copy SSH Key")
        ssh_copy_id(host=item, username="ansible", password="Anzaln@213", key=puBkeyPath)
        send(ip=item, message="SSH Key Copied Successfully")
    except Exception as e:
        print(f"Failed to send notification for {item}: {e}")
        failed_ips.append(item)

# Send notification with all failed IPs after the script finishes
if failed_ips:
    failed_message = f"The following IPs failed: {', '.join(failed_ips)}"
    try:
        send(ip="admin", message=failed_message)  # Sending to admin or a central address
        print(f"Notification sent for failed IPs: {failed_message}")
    except Exception as e:
        print(f"Failed to send notification for failed IPs: {e}")
else:
    print("All IPs processed successfully. No failures.")

