import paramiko
import logging
import os
import time
from notification import send


KEY_PATH = "/home/admin/.ssh/id_ed25519"
DISK_USAGE_THRESHOLD = 80
node_id="2e20d9f2-b32a-4303-98af-4a5446b00cdf"
ADDRESSES_FILE = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../addresses")
)


logging.basicConfig(level=logging.INFO)


report = {
    "timeouts": [],
    "failures": [],
    "disk_usage": []
}


def load_server_addresses(file_path):
    """
    Load server addresses from a file.
    """
    try:
        with open(file_path, "r") as file:
            return file.read().split()
    except FileNotFoundError:
        logging.error(f"Address file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading addresses file: {e}")
        raise


def ssh_connect(ip, private_key_path):
    """
    Establish an SSH connection and return the SSH client.
    """
    try:
        private_key = paramiko.Ed25519Key(filename=private_key_path)
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=ip, port=22, username='ansible', pkey=private_key)
        return ssh_client
    except paramiko.AuthenticationException:
        message = f"Authentication failed for {ip}. Please check credentials."
        report["failures"].append({"ip": ip, "reason": message})
        send(ip=ip, message=message,node_id=node_id)
        logging.error(message)
    except paramiko.SSHException as e:
        message = f"SSH connection failed for {ip}: {e}"
        report["failures"].append({"ip": ip, "reason": message})
        send(ip=ip, message=message,node_id=node_id)
        logging.error(message)
    except Exception as e:
        message = f"An unexpected error occurred for {ip}: {e}"
        report["failures"].append({"ip": ip, "reason": message})
        send(ip=ip, message=message,node_id=node_id)
        logging.error(message)
    return None


def execute_command(ssh_client, command):
    """
    Execute a command on the SSH client and return its output.
    """
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=10)
        return stdout.read().decode(), stderr.read().decode()
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}")


def check_root_disk_usage(ip):
    """
    Check the root filesystem disk usage using `df -h | awk '$NF=="/" {print $5}'`.
    """
    ssh_client = ssh_connect(ip, KEY_PATH)
    if ssh_client:
        try:
            
            command = "df -h | awk '$NF==\"/\" {print $5}'"
            output, error_output = execute_command(ssh_client, command)

            if error_output:
                message = f"STDERR from {ip}: {error_output}"
                report["failures"].append({"ip": ip, "reason": message})
                send(ip=ip, message=message)
                logging.error(message)
                return

            if output.strip():
                usage_percent = int(output.strip().replace('%', ''))  
                report["disk_usage"].append({"ip": ip, "usage": usage_percent})

                if usage_percent > DISK_USAGE_THRESHOLD:
                    alert_message = (
                        f"ALERT: Root filesystem usage on {ip} is {usage_percent}%, "
                        f"which exceeds the threshold of {DISK_USAGE_THRESHOLD}%."
                    )
                    logging.warning(alert_message)
                    send(ip=ip, message=alert_message,node_id=node_id)
                    time.sleep(2)
                else:
                    logging.info(f"Root filesystem usage on {ip} is within the limit: {usage_percent}%.")
            else:
                message = f"Could not retrieve root filesystem usage for {ip}."
                report["failures"].append({"ip": ip, "reason": message})
                send(ip=ip, message=message,node_id=node_id)
                logging.error(message)

        except RuntimeError as e:
            message = f"Timeout or command execution error for {ip}: {e}"
            report["timeouts"].append(ip)
            logging.error(message)
            send(ip=ip, message=message,node_id=node_id)
        finally:
            ssh_client.close()


def send_summary_report():
    """
    Send a summary report of timeouts, failures, and disk usage.
    """
    summary_message = (
        f"Disk Usage Report:\n"
        f"=================\n\n"
        f"Timeouts:\n{[ip for ip in report['timeouts']]}\n\n"
        f"Failures:\n"
        + "\n".join(f"{item['ip']}: {item['reason']}" for item in report["failures"])
        + "\n\n"
        f"Disk Usage:\n"
        + "\n".join(f"{item['ip']}: {item['usage']}%" for item in report["disk_usage"])
    )

    logging.info("Summary Report:\n" + summary_message)
    send(ip="all", message=summary_message,node_id=node_id)  


def main():
    """
    Main function to orchestrate the disk usage checks.
    """
    try:
        server_addresses = load_server_addresses(ADDRESSES_FILE)
        for ip in server_addresses:
            try:
                check_root_disk_usage(ip)
            except Exception as e:
                error_message = f"Failed to check disk usage for {ip}: {e}"
                logging.error(error_message)
                report["failures"].append({"ip": ip, "reason": error_message})
        send_summary_report()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
