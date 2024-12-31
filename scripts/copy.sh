#!/bin/bash


SERVERS_FILE="/home/admin/syxback/addresses"  
LOCAL_DIR="/home/admin/syxback/scripts/backups.sh"     
REMOTE_DIR="/home/ansible/scripts/"  


log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}


if [[ ! -f "$SERVERS_FILE" ]]; then
    log "ERROR: Servers file not found at $SERVERS_FILE."
    exit 1
fi

log "Starting the file transfer and remote command execution..."


for ip in "${ADDRESSES[@]}"; do
echo "Starting file transfer..."
scp -rC /mnt/Backups/bk/$ip  admin@172.17.20.209:/mnt/Backups/manual/
cp_pid=$!

echo "Waiting for file transfer to complete..."
wait $scp_pid
if [ $? -eq 0 ]; then
    python3  notification.py "${IP}: successfully moved!"  "status : ${EXIT_STATUS}"
else
    python3 notification.py "${IP}: failed!"  "status : ${EXIT_STATUS}"
    exit 1
fi
done

log "Script execution completed."
