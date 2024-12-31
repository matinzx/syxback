#!/bin/bash

send_message() {
    local message="$1" 
    local bot_token="9icwJq1SNWyWlWOUegXX3DrRpCqsC4eivkC5GdwscMGo7pMfOVFdjtwQRtPwoGrk6yWnciNjUxyJhv3wraljrg==" 
    local channel_id="2e20d9f2-b32a-4303-98af-4a5446b00cdf" 
    local url="https://api.wemessenger.ir/v2/${bot_token}/sendMessage"
    local payload=$(cat <<EOF
{
    "to": {
        "category": "CHANNEL",
        "node": "${channel_id}",
        "session_id": "*"
    },
    "text": {
        "text": "${message}"
    }
}
EOF
)
    
    curl --location --request POST "$url" \
        --header 'Content-Type: application/json' \
        --data-raw "$payload"
}

ADDRESSES=($(cat /home/admin/syxback/addresses))
LOCAL_FILE="/mnt/Seagate/Backups/bk/"
REMOTE="/mnt/Backups/manual/"

for IP in "${ADDRESSES[@]}"; do
    echo "Starting file transfer..."
    scp -rC admin@172.17.20.14:$LOCAL_FILE$IP $REMOTE
    scp_pid=$!

    echo "Waiting for file transfer to complete..."
    wait $scp_pid
    if [ $? -eq 0 ]; then
        # Call the function to send a success message
        send_message "data ${IP} transfer completed successfully."
    else
        # Call the function to send a failure message
        send_message "data ${IP} transfer failed."
        exit 1
    fi
done

