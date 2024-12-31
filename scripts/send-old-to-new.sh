#!/bin/bash


ADDRESSES=($(cat /home/admin/syxback/addresses))
LOCALfILE="/home/admin/syxback/scripts/backup.sh"
REMOTE="/home/ansible/scripts/"



for IP in "${ADDRESSES[@]}"; do
echo "Starting file transfer..."
scp -rC $LOCAL  "ansible@${IP}:${REMOTE}"
cp_pid=$!

echo "Waiting for file transfer to complete..."
wait $scp_pid
if [ $? -eq 0 ]; then
    echo "${IP}: successfully moved!"  "status : ${EXIT_STATUS}"
else
    echo  "${IP}: failed!"  "status : ${EXIT_STATUS}"
    exit 1
fi
done


