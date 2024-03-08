import os
import yaml
import subprocess
from tqdm import tqdm

def run_ssh_command(ssh_command, lxc_name="linux1"):
    result = subprocess.run(f"ssh root@192.168.0.11 \'lxc-attach -n linux1 -- {ssh_command}\'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)    
    
    if result.returncode == 0:
        return result.stdout.strip().split("\n")
    else:
        # print(f"Error: {result.stderr}")
        return None
    
def get_ps_info(ps_output_line, condition=""):
    ps_info = {}
    
    ps_output_line = ps_output_line.split(" ")
    ps_output_line = [v for v in ps_output_line if v is not ""]
    
    if int(ps_output_line[1]) < 10:
        return None 
    
    ps_info["pid"] = ps_output_line[1]
    ps_info["tid"] = ps_output_line[2]
    
    return ps_info

def get_node_ps_info(node_names, ps_output):
    node_ps_info = {"others": []}
    for i, ps_output_line in enumerate(ps_output):
        if i == 0: continue
        
        is_others = True
        
        ps_info = get_ps_info(ps_output_line, "__name")        
        
        if ps_info == None:
            continue
        
        for node_name in node_names:
            if node_name not in node_ps_info:
                node_ps_info[node_name] = []
            
            if node_name in ps_output_line:
                node_ps_info[node_name].append(ps_info)
                is_others = False
                break
            
        if is_others:
            node_ps_info["others"].append(ps_info)
            
    return node_ps_info

if __name__ == "__main__":
    with open("yaml/cubetown_autorunner_params.yaml", "r") as f:
        autorunner_params = yaml.load(f, yaml.FullLoader)
    
    ps_output = run_ssh_command(f"ps aux -L")
    node_ps_info = get_node_ps_info(autorunner_params.keys(), ps_output)
        
    for node_name in tqdm(autorunner_params):
        if "affinity" not in autorunner_params[node_name]:
            continue
        
        target_ps_info_list = node_ps_info[node_name]        
        main_affinity = autorunner_params[node_name]["affinity"]["main"]
        child_affinity = autorunner_params[node_name]["affinity"]["child"]
        
        if main_affinity < 0 or child_affinity < 0:
            continue
        
        for target_ps_info in target_ps_info_list:
            # if target_ps_info["pid"] == target_ps_info["tid"]:
            #     run_ssh_command(f"taskset -p -c {main_affinity} {target_ps_info['tid']}")
            # else:
            #     run_ssh_command(f"taskset -p -c {child_affinity} {target_ps_info['tid']}")
            run_ssh_command(f"chrt -f -p 99 {target_ps_info['tid']}")
    