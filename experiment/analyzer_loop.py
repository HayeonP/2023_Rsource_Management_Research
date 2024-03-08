import glob
import os

def change_yaml(new_str):

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

# for vel in range(7, 11):

#     for bw in range(1024, 2560, 512):
#         change_yaml(f'230703_BW{bw}_ED_AVOID_LIDAR3_CAM2_v{vel}_456')
#         os.system('python3 autoware_analyzer.py')


vel_list = [8.5, 8.3, 8.0]
obs_list = [57.3, 57.2, 57.1]
bw_list = [3*1024, 5*1024]
recent_list = glob.glob('results/*')


def loop_test():
    # for i in range(start_page_num, 30, -1):
    for velocity in vel_list:
        # change_velocity(velocity)
        for obs in obs_list:
            # change_obstable_x(obs)

            for bw in bw_list:
                # change_bw(f'yaml/svl_auto_experiment_configs.yaml', bw)

                experiment_title = f'230705_obstacle{str(obs)}_BW{str(bw)}_ED_AVOID_LIDAR3_CAM2_v{str(velocity)}_456_new'
                change_yaml(experiment_title)
                os.system('python3 autoware_analyzer.py')
                # experiment_title = 'test'

def loop_analyze():
    for name in recent_list:
        rel_name = name.split('/')[1]
        if '230707' in rel_name:
            # change_yaml(rel_name)
            # os.system('python3 autoware_analyzer.py')
            os.system(f'scp -r -P 2224 {name} lee@147.46.114.230:/home/hayeonp/experience/temp')


if __name__ == "__main__":
    # loop_test()
    loop_analyze()