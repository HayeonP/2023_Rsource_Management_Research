import os

def setup_palloc(page_num):
        # os.system(f'cp palloc_yaml/svl_auto_experiment_configs_{i}.yaml yaml/svl_auto_experiment_configs.yaml')
        # print(i)
        os.system(f'ssh root@192.168.0.8 "echo 0x000001f000 > /sys/kernel/debug/palloc/palloc_mask"')
        os.system(f'ssh root@192.168.0.8 "echo 1 > /sys/kernel/debug/palloc/debug_level"')
        os.system(f'ssh root@192.168.0.8 "echo 32 > /sys/kernel/debug/palloc/alloc_balance"')
        os.system(f'ssh root@192.168.0.8 "echo 1 > /sys/kernel/debug/palloc/use_palloc"')
        os.system(f'ssh root@192.168.0.8 "echo 0-{page_num-1} > /sys/fs/cgroup/palloc/lxc.payload.linux1/palloc.bins"')

def change_experiment_title(file_path, new_str):
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

        fw.write(line)
    fw.close()

test_pages = range(20, 32)
test_pages = range(27, 21, -1)


def loop_test(start_page_num):
    # for i in range(start_page_num, 30, -1):
    for i in test_pages:
        setup_palloc(i)
        change_experiment_title(f'yaml/svl_auto_experiment_configs.yaml', f'230713_hyp_BASE_PALLOC{i}_ED_ZIGZAG_LIDAR3_CAM2_v7_5_456')
        # change_experiment_title(f'yaml/svl_auto_experiment_configs.yaml', f'test3')
        
        # 호출: file1.txt 파일에서 comma(,) 없애기
        # change_experiment_title("palloc_yaml/svl_auto_experiment_configs_30.yaml", "230628_BASE_PALLOC_ED_ZIGZAG_LIDAR3_CAM2_v7_5_456_test2")

        os.system('python3 yong_svl_auto_experiment.py')

if __name__ == "__main__":
    loop_test(31)