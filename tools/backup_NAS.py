import os
import paramiko

# NAS 서버 연결 정보
username = "admin"
password = "4542rubis"
nas_server_address = "147.46.114.148"

# 로컬 디렉토리와 NAS 서버 디렉토리 경로
loc_results = "../experiment/results"
loc_analyzation = "../experiment/analyzation"
nas_results = "/volume1/project/Exynos/Experiment/results"
nas_analyzation = "/volume1/project/Exynos/Experiment/analyzation"

# 로컬 디렉토리 리스트 가져오기
loc_results_list = os.listdir(loc_results)
loc_analyzation_list = os.listdir(loc_analyzation)

# NAS 서버 디렉토리 리스트 가져오기
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(nas_server_address, username=username, password=password)

stdin, stdout, stderr = ssh.exec_command(f"ls {nas_results}")
nas_results_list = stdout.read().decode().splitlines()

stdin, stdout, stderr = ssh.exec_command(f"ls {nas_analyzation}")
nas_analyzation_list = stdout.read().decode().splitlines()

# 백업되지 않은 디렉토리 찾기
results_to_backup = [dir for dir in loc_results_list
                         if dir not in nas_results_list]
analyzation_to_backup = [dir for dir in loc_analyzation_list
                         if dir not in nas_analyzation_list]

# SCP로 백업하기
for dir_to_backup in results_to_backup:
    local_path = os.path.join(loc_results, dir_to_backup)
    remote_path = os.path.join(nas_results, dir_to_backup)
    
    command = f"sshpass -p 4542rubis scp -r {local_path} {username}@{nas_server_address}:{remote_path}"
    os.system(command)
    print(f"{dir_to_backup} backed up successfully.")

for dir_to_backup in analyzation_to_backup:
    local_path = os.path.join(loc_analyzation, dir_to_backup)
    remote_path = os.path.join(nas_analyzation, dir_to_backup)
    
    command = f"sshpass -p 4542rubis scp -r {local_path} {username}@{nas_server_address}:{remote_path}"
    os.system(command)
    print(f"{dir_to_backup} backed up successfully.")

ssh.close()
