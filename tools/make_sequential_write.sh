#!/bin/bash

ssh root@192.168.0.11 "mkdir -p /home/root/sdd/tools"
scp sequential_write.c root@192.168.0.11:/home/root/sdd/tools
ssh root@192.168.0.11 "cd /home/root/sdd/tools && gcc sequential_write.c"
# ssh root@192.168.0.11 "cd /home/root/sdd/tools && taskset -c $target_core ./a.out"