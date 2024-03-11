import os
import sys


exception_node_list = ['rosmaster', 'rosapi', 'rosbridge', 'rosout']

sensing_node_list = ['_cubetown_autorunner_1_sensing', 'static_transform_publisher', 'vector_map_loader', 'points_map_loader', 'image_transport/republish', 'svl_sensing']
localization_node_list = ['_cubetown_autorunner_2_localization', 'voxel_grid_filter', 'ndt_matching', '/config/ndt']
detection_node_list = ['_cubetown_autorunner_3_detection', 'ray_ground_filter', 'lidar_euclidean_cluster_detect', 'visualize_detected_objects', 'lane_detector']


if len(sys.argv) > 1:
    if sys.argv[1] == 'exception':
        exception_node_list.extend(sensing_node_list)
        exception_node_list.extend(localization_node_list)
        exception_node_list.extend(detection_node_list)

output = str(os.popen('ps ax | grep opt/ros/melodic').read())
output = output.split('\n')
for line in output:
    if all(exception_node not in line for exception_node in exception_node_list):
        for v in line.split(' '):
            try:
                pid = str(int(v))
                os.system('kill -9 '+pid)
            except:
                continue
output = str(os.popen('ps ax | grep rubis_ws').read())
output = output.split('\n')
for line in output:
    if all(exception_node not in line for exception_node in exception_node_list):
        for v in line.split(' '):
            try:
                pid = str(int(v))
                os.system('kill -9 '+pid)
            except:
                continue
