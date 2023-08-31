import os

def change_experiment_title(file_path, new_str, new_bw_thr):
    # 파일 읽어들이기
    fr = open(file_path, 'r')
    lines = fr.readlines()
    fr.close()
    
    # old_str -> new_str 치환
    fw = open(file_path, 'w')
    for line in lines:
        if 'experiment_title' in line and not '#' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = new_str
            line = components[0] + ": '" + components[1] + "'\n"
            # print(components)
        if 'bw_thr' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = new_bw_thr
            line = components[0] + ": " + str(components[1]) + "\n"

        fw.write(line)
    fw.close()

bw_list = []

for i in range(5120, 1024, -256):
    bw_list.append(i)

# for i in range(512, 1536, 128):
#     bw_list.append(i)

def loop_test():
    # for i in range(start_page_num, 30, -1):
    for i in bw_list:
        change_experiment_title(f'yaml/svl_auto_experiment_configs.yaml', f'230703_BW{i}_ED_ZIGZAG_LIDAR3_CAM2_v7_5_t1_456', i)
        # change_experiment_title(f'yaml/svl_auto_experiment_configs.yaml', f'test', i)
        
        # change_experiment_title("palloc_yaml/svl_auto_experiment_configs_30.yaml", "230628_BASE_PALLOC_ED_ZIGZAG_LIDAR3_CAM2_v7_5_456_test2")

        os.system('python3 yong_svl_auto_experiment.py')

if __name__ == "__main__":
    loop_test()