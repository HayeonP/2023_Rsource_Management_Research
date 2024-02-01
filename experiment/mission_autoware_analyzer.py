import os
import yaml





"""
기능: SeqWr를 껏다켰다 하며 analyzer를 동작시킴
"""

HOSTNAME = "192.168.0.11"

class SeqWr:
    def __init__(self, target_bandwidth, target_core):
        self.target_bandwidth = target_bandwidth
        self.target_core = target_core
        
        return
    
    def run(self):
        os.system(f"ssh root@{HOSTNAME} \"taskset -c {self.target_core} /var/lib/lxc/linux1/rootfs/home/root/mg/tools/sequential_write -p -b {self.target_bandwidth} -s 64\"")
        
        return
    
def kill_seqwr_workloads():
    os.system(f"ssh root@{HOSTNAME} \"ps -ax | grep sequential_write > /home/root/sdd/temp.txt\"")
    os.system(f"scp root@{HOSTNAME}:/home/rooot/sdd/temp.txt .")
    with open("temp.txt", "r") as f:
        ps_output = f.read()
    
    ps_output = ps_output.split("\n")
    
    for line in ps_output:
        if "sequential_write" not in line: continue
        elements = line.split(" ")
        elements = [e for e in elements if e != ""]
        pid = elements[0]
        os.system(f"ssh root@{HOSTNAME} \"kill -9 {pid}\"")
    
    return

output_title_list = ["test-adas_only", "test-adas+seqwr2000", "test-adas+seqwr-x3"]
duration_list = [5, 5, 5]
workloads_list = [
    [],
    [SeqWr(2000, 1)],
    [SeqWr(204800, 1), SeqWr(204800, 2), SeqWr(204800, 3)]
]

if len(output_title_list) != len(duration_list) or len(output_title_list) != len(worklaod_list):
    print("[ERROR] Wrong configuration!")
    exit()

for i in range(len(duration_list)):
    output_title = output_title_list[i]
    duration = duration_list[i]
    workload = workloads_list[i]
    
    with open("yaml/autoware_analyzer.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    config["online_profiling"] = True
    config["online_profiling_duration"] = duration
    config["output_title"][0] = output_title
    
    with open("configs/autoware_analyzer.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    os.system("python3 autoware_analyzer")

