import yaml
import os

version_list = range(6)
repeat_list = [3,3,3,3,3,3]

print(len(version_list))
print(len(repeat_list))
input("arr size check, Enter any key")

for i in range(len(version_list)):
    # Erase log
    os.system("ssh root@192.168.0.11 \'rm -r /var/lib/lxc/linux1/rootfs/home/root/autoware_openplanner_logs/*\'")
    os.system("ssh root@192.168.0.11 \'rm -r /var/lib/lxc/linux1/rootfs/home/root/.ros/*\'")
    
    with open("yaml/svl_auto_experiment_configs.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        
    version = version_list[i]
    repeat = repeat_list[i]
    config["experiment_title"] = config["experiment_title"].split("x")[0] + "x" + str(repeat) + "_v" + str(version)
    config["max_iteration"] = repeat
    
    with open("yaml/svl_auto_experiment_configs.yaml", "w") as f:
        yaml.dump(config, f)
    
    os.system("python3 svl_auto_experiment.py")
    
    with open("yaml/autoware_analyzer.yaml", "r") as f:
        analyzer_config = yaml.load(f, Loader=yaml.FullLoader)
    
    analyzer_config["experiment_title"] = [config["experiment_title"]]
    analyzer_config["output_title"] = [config["experiment_title"]]
    
    with open("yaml/autoware_analyzer.yaml", "w") as f:
        yaml.dump(analyzer_config, f)
        
    os.system("python3 autoware_analyzer.py")
    
    
    

