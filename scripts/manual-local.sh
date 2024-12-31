#!/bin/bash

dir="/home/ansible/Backups/2024/${MONTH}"

cd "$dir"

if [ -d "${dir}/${day}" ]; then
  if [ -f "${day}.tar.gz" ]; then
    echo "Tarball ${day}.tar.gz already exists." > manual-logs.txt
    echo "Tarball ${day}.tar.gz already exists."
    exit 0
  else
    tar -zcvf "${day}.tar.gz" "${day}/" > /dev/null 
    tar_pid=$!
    wait $tar_pid
    if [ $? -eq 0 ]; then
      echo "Tar command completed successfully." > manual-logs.txt
      echo "Tar command completed successfully." 
      exit 0
    else
      echo "Tar command failed." > manual-logs.txt
      echo "Tar command failed." 
      exit 1
    fi
  fi
else
  echo "Directory ${dir}/${day} does not exist." > manual-logs.txt
  echo "Directory ${dir}/${day} does not exist."
  exit 1
fi
