while true;do
    wget -T 15 -c -O $1 $2 && break
    echo "I'm sleeping"
    sleep 60
    done
