import os
import sys
import time
import subprocess



core4_start_time_list = []
core5_start_time_list = []
start_time_diff_list = []


for i in range(100):
    with open(f'clguard_time_test/it{i}_clguard_config_start.txt') as f:
        lines = f.readlines()
        for line in lines:
            if 'Core4 hrtimer start time' in line:
                core4_hrtimer_start_time = int(line.replace(' ', '').split(':')[-1])
            if 'Core5 hrtimer start time' in line:
                core5_hrtimer_start_time = int(line.replace(' ', '').split(':')[-1])

        core4_start_time_list.append(core4_hrtimer_start_time)
        core5_start_time_list.append(core5_hrtimer_start_time)

        time_diff = core4_hrtimer_start_time - core5_hrtimer_start_time
        time_diff /= 1000
        start_time_diff_list.append(time_diff)

print(start_time_diff_list)

