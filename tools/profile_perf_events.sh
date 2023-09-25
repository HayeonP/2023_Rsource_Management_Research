#!/bin/bash

HOSTNAME=192.168.0.11

ssh root@$HOSTNAME "mkdir -p /home/root/sdd/tools/perf_events_log"
scp -r configs root@$HOSTNAME:/home/root/sdd/tools
scp profile_perf_events.py root@$HOSTNAME:/home/root/sdd/tools
ssh root@$HOSTNAME "cd /home/root/sdd/tools && python3 profile_perf_events.py"

# perf stat --timeout $DURATION -C 4-6 -e $BASE_EVENTS,$BUS_EVENTS,$L1D_EVENTS,$L1I_EVENTS,$L2D_EVENTS,$L3D_EVENTS -o log.txt