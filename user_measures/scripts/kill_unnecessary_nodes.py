import subprocess
import os

def parse_ps_with_grep(grep_str):
    ps_info_list = []
    result = subprocess.run(f"ssh root@192.168.0.11 \"ps ax | grep {grep_str}\"", shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
    result = result.split("\n")
    for line in result:
        print(line)
        if line == "": continue
        ps_info = line.split(" ")
        ps_info = [v for v in ps_info if v != '']
        ps_info_list.append(ps_info)
    return ps_info_list

def kill_processes_with_grep(grep_str):
    ps_info_list = parse_ps_with_grep(grep_str)

    for ps_info in ps_info_list:
        if len(ps_info) == 0: continue
        pid = ps_info[0]
        os.system(f"ssh root@192.168.0.11 \"kill -9 {pid}\"")
        print(pid)

if __name__ == '__main__':
    kill_processes_with_grep("ros")



