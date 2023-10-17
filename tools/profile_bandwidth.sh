#!/bin/bash

HOSTNAME=192.168.0.11

ssh root@$HOSTNAME "mkdir -p /home/root/sdd/tools/bw_profiler"
scp -r configs root@$HOSTNAME:/home/root/sdd/tools
scp profile_bandwidth.py root@$HOSTNAME:/home/root/sdd/tools
ssh root@$HOSTNAME "cd /home/root/sdd/tools && python3 profile_bandwidth.py"
python3 analyze_bandwidth.py