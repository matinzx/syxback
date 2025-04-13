#!/bin/bash

# === Function: Banner ba design ghashang ===
show_banner() {
  echo ""
  echo "#######################################"
  echo "#                                     #"
  echo "#         🚀🚀  KATIN  🚀🚀            #"
  echo "#                                     #"
  echo "#######################################"
  echo ""
}

# Seda kardan banner dar avval script
show_banner

# === Config ===
PORT=8080                                 # Port Tomcat
THRESHOLD_CONNECTIONS=500                 # Hade aksar connections mojaz
TOMCAT_SERVICE="tomcat"                   # Name service Tomcat
CHECK_URL="http://127.0.0.1:8080/buildDate"       # URL baraye health check
MAX_RETRIES=2                             # Tedad talash baraye health check
SLEEP_BETWEEN_RETRIES=5                   # Zamane entezaar bein retries (be sanie)

# === Tarikh va zaman ===
timestamp=$(date "+%Y-%m-%d %H:%M:%S")

# === Function: Restart Tomcat ba pak kardan cache ===
restart_tomcat() {
  echo "⛔️ Stopping Tomcat..."
  sudo service "$TOMCAT_SERVICE" stop
  echo "$timestamp - Tomcat stop shod."

  echo "🧹 Cache system ro pak mikonim..."
  sudo bash -c 'echo 3 > /proc/sys/vm/drop_caches'
  echo "$timestamp - Cache system pak shod."

  echo "🚀 Starting Tomcat..."
  sudo service "$TOMCAT_SERVICE" start
  echo "$timestamp - Tomcat start shod."

  # === Health check ba curl (20 sanie sabr) ===
  for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "⏳ Talash $i baraye check Tomcat..."
    response=$(curl -s --max-time 20 "$CHECK_URL")

    if [[ $response == *"2025-"* ]]; then
      echo "✅ Tomcat ba movafaghiat bala amad. Pasokh: $response"
      show_banner
      return 0
    else
      echo "⚠️ Tomcat hanuz response nemide. Sabr mikonim..."
      sleep "$SLEEP_BETWEEN_RETRIES"
    fi
  done

  echo "❌ Tomcat ba'd az $MAX_RETRIES talash hanuz response nadad!"
  return 1
}

# === Check tedad active connection ha (ba netstat) ===
active_connections=$(netstat -anp 2>/dev/null | grep ":$PORT" | grep ESTABLISHED | wc -l)
echo "$timestamp - Active connections: $active_connections"

# === Check curl be URL ===
curl_response=$(curl -s --max-time 20 "$CHECK_URL")

# === Decision making ===
if [[ "$active_connections" -ge "$THRESHOLD_CONNECTIONS" ]] || [[ ! "$curl_response" == *"2025-"* ]]; then
  echo "$timestamp - 🚨 Shart restart bargharar shod! (Connections: $active_connections, Curl: ${curl_response:-"No Response"})"
  restart_tomcat
else
  echo "✅ Hame chiz normal-e. Connections: $active_connections, Curl: $curl_response"
fi
