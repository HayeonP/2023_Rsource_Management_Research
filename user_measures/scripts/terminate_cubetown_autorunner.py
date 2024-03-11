import os
import sys

exception_node_list = ['rosmaster', 'rosapi', 'rosbridge', 'rosout', 'svl_sensing', 'svl_camera_top', 'base_link_to_velodyne', 'config_ndt', 'detection/lidar_detector/cluster_detect_visualization_center', 'lidar_euclidean_cluster_detect_center', 'lidar_to_camera', 'map_to_mobility', 'points_map_loader', 'ray_ground_filter_center', 'vector_map_loader', 'voxel_grid_filter', 'world_to_map', 'ndt_matching', 'lane_detector_top']
origin_exception_node_list = ['rosmaster', 'rosapi', 'rosbridge', 'rosout']

target_node_list = origin_exception_node_list

if len(sys.argv) > 1:
    if sys.argv[1] == 'exception':
        target_node_list = exception_node_list

output = str(os.popen('ps ax | grep opt/ros/melodic').read())
output = output.split('\n')
for line in output:
    if all(exception_node not in line for exception_node in target_node_list):
        for v in line.split(' '):
            try:
                pid = str(int(v))
                os.system('kill -9 '+pid)
            except:
                continue
output = str(os.popen('ps ax | grep rubis_ws').read())
output = output.split('\n')
for line in output:
    if all(exception_node not in line for exception_node in target_node_list):
        for v in line.split(' '):
            try:
                pid = str(int(v))
                os.system('kill -9 '+pid)
            except:
                continue
