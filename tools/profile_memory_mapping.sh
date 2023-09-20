#!/bin/bash

HOSTNAME=192.168.0.11

ssh root@$HOSTNAME "mkdir -p /home/root/sdd/tools"
scp -r configs root@$HOSTNAME:/home/root/sdd/tools
scp profile_memory_mapping.py root@$HOSTNAME:/home/root/sdd/tools
ssh root@$HOSTNAME "cd /home/root/sdd/tools && python3 profile_memory_mapping.py"