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


for IP in "${ADDRESSES[@]}"; do


    #ssh ansible@${IP} "rm /home/ansible/Backups/2024/12/*.tar.gz"
    #ssh ansible@$IP 'crontab -l | { cat; echo "30 18 * * * bash /home/ansible/scripts/backup.sh"; } | crontab -' 
    ssh ansible@$IP 'crontab -l | grep -v "^30 18 \* \* \* bash /home/ansible/scripts/backup.sh$" | { cat; echo "0 19 * * * bash /home/ansible/scripts/backup.sh"; } | crontab -'


    echo "Waiting for removing  to complete..."


    if [ $? -eq 0 ]; then
        
        send_message "removing  ${IP} tar.gz successfully."
    else
        
        send_message "removing ${IP} tar.gz failed."
        
    fi

done
