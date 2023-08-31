import os


def change_experiment_title(file_path, new_str):
    fr = open(file_path, 'r')
    lines = fr.readlines()
    fr.close()
    
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

def change_velocity(new_vel, file_path='yaml/cubetown_autorunner_params.yaml'):
    fr = open('yaml/cubetown_autorunner_params.yaml', 'r')
    lines = fr.readlines()
    fr.close()
    
    # old_str -> new_str 치환
    fw = open(file_path, 'w')
    for line in lines:
        if 'maxVelocity' in line and not '#' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = str(new_vel)
            line = components[0] + ": " + components[1] + "\n"
        if 'maxAcceleration' in line and not '#' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = str(new_vel)
            line = components[0] + ": " + components[1] + "\n"
        if 'maxDeceleration' in line and not '#' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = '-' + str(new_vel)
            line = components[0] + ": " + components[1] + "\n"

        fw.write(line)
    fw.close()

    os.system('scp -r yaml/cubetown_autorunner_params.yaml root@192.168.0.8:/var/lib/lxc/linux1/rootfs/home/root/rubis_ws/src/rubis_autorunner/cfg/cubetown_autorunner')

def change_analyzer(new_str):

    fr = open('yaml/autoware_analyzer.yaml', 'r')
    lines = fr.readlines()
    fr.close()

    # old_str -> new_str 치환
    fw = open('yaml/autoware_analyzer.yaml', 'w')
    for line in lines:
        if 'experiment_title' in line and not '#' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = new_str
            line = components[0] + ": ['" + components[1] + "']\n"
            # print(components)
        if 'output_title' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = new_str
            line = components[0] + ":     ['" + components[1] + "']\n"

        fw.write(line)
    fw.close()

def change_bw(file_path, new_bw_thr):
    # 파일 읽어들이기
    fr = open(file_path, 'r')
    lines = fr.readlines()
    fr.close()
    
    # old_str -> new_str 치환
    fw = open(file_path, 'w')
    for line in lines:
        if 'bw_thr' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = new_bw_thr
            line = components[0] + ": " + str(components[1]) + "\n"

        fw.write(line)
    fw.close()

def change_obstable_x(new_x, file_path='yaml/svl_scenario.yaml'):
    # 파일 읽어들이기
    fr = open(file_path, 'r')
    lines = fr.readlines()
    fr.close()
    
    # old_str -> new_str 치환
    fw = open(file_path, 'w')
    for line in lines:
        if 'forward' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = new_x
            line = components[0] + ": " + str(components[1]) + "\n"

        fw.write(line)
    fw.close()

def change_zigzag_obstable_x(new_right, new_forward=52, file_path='yaml/svl_scenario.yaml'):
    # 파일 읽어들이기
    fr = open(file_path, 'r')
    lines = fr.readlines()
    fr.close()
    
    # old_str -> new_str 치환
    fw = open(file_path, 'w')
    i = 0
    for line in lines:
        if 'right' in line:
            if i == 2:
                line.replace(' ', '')
                components = line.split(':')
                components[1] = new_right
                line = components[0] + ": " + str(components[1]) + "\n"
            i += 1

        fw.write(line)
    fw.close()

vel_list = [7.5]
obs_list = [58, 57.7]
second_obs_list = [0.5, -0.5, 1, -1]
bw_list = [1*1024]

def zigzag_test():
    for bw in bw_list:
        # bw = 5*1024
        # change_zigzag_obstable_x(second_obs)
        change_bw(f'yaml/svl_auto_experiment_configs.yaml', bw)
        # obs_name = str(second_obs).replace('.', '_')
        # obs_name = obs_name.replace('-', '_')

        experiment_title = f'230710_hayp_3obs_BW{str(bw)}_ED_ZIGZAG_LIDAR3_CAM2_v{str(7.5).replace(".", "_")}_t100_456'
        # experiment_title = 'test'

        change_experiment_title(f'yaml/svl_auto_experiment_configs.yaml', experiment_title)

        os.system('python3 yong_svl_auto_experiment.py')



def loop_test():
    # for i in range(start_page_num, 30, -1):
    for velocity in vel_list:
        change_velocity(velocity)
        for obs in obs_list:
            change_obstable_x(obs)

            for bw in bw_list:
                change_bw(f'yaml/svl_auto_experiment_configs.yaml', bw)

                experiment_title = f'230705_obstacle{str(obs).replace(".", "_")}_BW{str(bw)}_ED_AVOID_LIDAR3_CAM2_v{str(velocity).replace(".", "_")}_t100_456'
                experiment_title.replace('.', '_')
                # experiment_title = 'test'

                change_experiment_title(f'yaml/svl_auto_experiment_configs.yaml', experiment_title)
        
                os.system('python3 yong_svl_auto_experiment.py')

            # change_analyzer(experiment_title)
            # os.system('python3 autoware_analyzer.py')
    velocity = 8.7
    obs = 57.5
    bw = 5*1024
    change_velocity(velocity)
    change_obstable_x(obs)
    change_bw(f'yaml/svl_auto_experiment_configs.yaml', bw)
    experiment_title = f'230705_obstacle{str(obs).replace(".", "_")}_BW{str(bw)}_ED_AVOID_LIDAR3_CAM2_v{str(velocity).replace(".", "_")}_t100_456'
    change_experiment_title(f'yaml/svl_auto_experiment_configs.yaml', experiment_title)
    os.system('python3 svl_auto_experiment.py')       


if __name__ == "__main__":
    zigzag_test()
    # loop_test()
    # change_obstable_x(55)
    # experiment_title = f'230705_obstacle{str(57.2)}_BW{str(3072)}_ED_AVOID_LIDAR3_CAM2_v{str(8.3)}_t100_456'
    # experiment_title.replace('.', '_')
    # print(f'{str(57.2).replace(".", "_")}')
    # print(str(57.2).replace('.','_'))
    # print(experiment_title)
