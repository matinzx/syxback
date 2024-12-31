#!/bin/bash

DateFolder=$(date "+%Y/%m/%d/")
YearMonth=$(date "+%Y/%m/")
Day=$(date "+%d")
Folder="/home/ansible/Backups/"
MySqlPassword="mysql123sjb"
MySqlUser="root"
PSqlPassword="bahmanz"
PSqlUser="postgres"
MySqlHost="192.168.0.99"
PsqlfileName=$(date "+%H%M")
MysqlFolder="Mysql/"
PsqlFolder="Psql/"
acc="acc/"
Psqldb="acc"
logs="logs"
bash_history="bash_history"
viminfo="viminfo"
webapps="webapps"

log_file="${Folder}${DateFolder}healtylog.txt"

MySqlHost="`sudo cat /tomcat/webapps/Customs/WEB-INF/classes/hibernate.cfg.xml | grep  "mysql://" | cut -d ":" -f 3 | cut -d "/" -f 3`"
MysqlFileName="backup"

rename_tarball() {
    local tar_file=$1
    local directory=$2

    if [[ -f "${tar_file}" ]]; then
        local hash=$(md5sum "${tar_file}" | awk '{ print $1 }')
        local new_name="${Folder}${YearMonth}${Day}-${hash}.tar.gz"
        mv "${tar_file}" "${new_name}"
        echo "Tarball renamed to: ${new_name}"
    else
        echo "Error: Tarball file '${tar_file}' does not exist." >> "$log_file"
        return 1
    fi
}

# Create backup directories
mysql_backup_path="${Folder}${DateFolder}${MysqlFolder}"
psql_backup_path="${Folder}${DateFolder}${PsqlFolder}"
mkdir -p "$mysql_backup_path"
mkdir -p "$psql_backup_path$acc"
if [[ $? -ne 0 ]]; then
    echo "Error: Failed to create backup directories." >> "$log_file"
    exit 1
fi

# MySQL database backup
databases=$(mysql -u "$MySqlUser" -h "$MySqlHost" -p"$MySqlPassword" -e "SHOW DATABASES;" | grep -Ev "(Database|information_schema|performance_schema|mysql|sys)")
if [[ -z "$databases" ]]; then
    echo "Error: No MySQL databases found to back up." >> "$log_file"
else
    for db in $databases; do
        echo "Backing up database '$db' from MySQL host '$MySqlHost'."
        backup_file="${mysql_backup_path}/${MysqlFileName}_${db}.sql.gz"
        mysqldump -u "$MySqlUser" -h "$MySqlHost" -p"$MySqlPassword" --databases "$db" --flush-logs --add-drop-table --single-transaction | gzip -9 > "$backup_file"
        
        if [[ $? -ne 0 ]]; then
            echo "Error: Failed to back up database '$db'. Check your MySQL credentials or connection." >> "$log_file"
            continue
        fi

        if gunzip -c "$backup_file" | grep -q 'Dump completed'; then
            size=$(du -h "$backup_file" | cut -f1)
            echo "$db / MySQL dump is healthy. Size: $size" >> "$log_file"
        else
            echo "$db / MySQL dump is NOT healthy. Backup may be corrupted." >> "$log_file"
        fi
    done
fi

# PostgreSQL database backup
echo "Backing up PostgreSQL database."

if [ -d "/tomcat/webapps/acc" ]; then

PGPASSWORD="$PSqlPassword" pg_dump -h localhost -U "$PSqlUser" "$Psqldb" | gzip -9 > "${psql_backup_path}${acc}${PsqlfileName}.sql.gz"

    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to back up PostgreSQL database '$acc'. Check your PostgreSQL credentials or connection." >> "$log_file"
    else
        echo  "PSQL dump ${psql_backup_path}${PsqlfileName}.sql.gz finished"
        echo "PSQL dump ${psql_backup_path}${PsqlfileName}.sql.gz finished" >> "$log_file"
    fi

fi

# Copy logs, system files, and webapps
if [ -d "/tomcat" ]; then
    sudo cp  /tomcat/logs/catalina.out $Folder$DateFolder$logs
    sudo cp -r /tomcat/webapps $Folder$DateFolder$webapps
elif [ -d "/opt/tomcat/" ]; then
    sudo cp  /opt/tomcat/logs/catalina.out $Folder$DateFolder$logs
    sudo cp -r /opt/tomcat/webapps $Folder$DateFolder$webapps
else
    echo "Tomcat directory doesn't exist" >> "$log_file"
fi

sudo cp  /var/log/auth.log $Folder$DateFolder$logs
sudo cp  /var/log/mysql/error.log $Folder$DateFolder$logs
sudo cp -r /var/log/btmp.1 $Folder$DateFolder$logs
sudo cp -r /var/log/wtmp.1 $Folder$DateFolder$logs
sudo cp -r /home/ansible/.bash_history $Folder$DateFolder$bash_history
sudo cp -r /home/ansible/.viminfo $Folder$DateFolder$viminfo
sudo cp -r /etc/hosts $Folder$DateFolder

sudo rm -r $Folder$DateFolder/webapps
sudo chown -R ansible:ansible /home/ansible/Backups

tar_file="${Folder}${YearMonth}${Day}.tar.gz"
tar -cvzf "${tar_file}" -C "${Folder}" "${DateFolder}"

if [ $? -eq 0 ]; then
    rename_tarball "${tar_file}" "${Folder}${DateFolder}"
    if [[ $? -eq 0 ]]; then
        rm -rf $Folder$DateFolder
    else
        echo "Error: Failed to rename the tarball." >> "$log_file"
    fi
else
    echo "The tar command failed for last archive ${Day}, the file was not created, or it is empty." >> "$log_file"
fi

echo "All backups processed. Log file: $log_file"
