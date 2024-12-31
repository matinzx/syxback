from rich.console import Console
from rich.live import Live
from rich.table import Table
import time
import os


LOG_FILE = "transfer_log.log"


def read_log_file(file_path):
    """Read log file and return its lines."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return f.readlines()


def parse_logs(log_lines):
    """Parse log lines into a structured format."""
    table = Table(title="File Transfer Status", style="cyan")
    table.add_column("Timestamp", style="dim", width=25)
    table.add_column("Level", style="bold")
    table.add_column("Message")

    for line in log_lines:
        parts = line.split(" - ", maxsplit=2)
        if len(parts) == 3:
            timestamp, level, message = parts
            table.add_row(timestamp.strip(), level.strip(), message.strip())
    return table


def monitor_logs():
    """Monitor log file and update terminal UI dynamically."""
    console = Console()
    last_size = 0

    with Live(console=console, refresh_per_second=1) as live:
        while True:
            try:
                log_lines = read_log_file(LOG_FILE)
                current_size = len(log_lines)
                if current_size > last_size:
                    live.update(parse_logs(log_lines))
                    last_size = current_size
                time.sleep(1)
            except KeyboardInterrupt:
                console.print("[bold red]Exiting log monitor...[/bold red]")
                break


if __name__ == "__main__":
    monitor_logs()
