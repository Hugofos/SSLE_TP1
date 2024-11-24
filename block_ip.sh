#!/bin/bash

IP=$1

if [ -z "$IP" ]; then
    echo "Usage: $0 <IP>"
    exit 1
fi

# Block IP inside the service_a container
#echo $IP
curl -X POST http://10.151.101.11:5000/block_ip -H "Content-Type: application/json" -d '{"ip": "'$IP'"}'
echo "Blocked IP: $IP in service_a container"