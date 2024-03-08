import os
import sys
import matplotlib.pyplot as plt
import yaml
import json
import scripts.autoware_analyzer_lib as aa
import numpy as np

b8000_adas_only_path = 'results/240305/b8000_adas_only/1'
b8000_adas_b3000_seqwr_path = 'results/240305/b8000_adas_b3000_seqwr/1'
b8000_adas_seqwr_path = 'results/240305/b8000_adas_seqwr/2'

if __name__ == '__main__':

    line_width = 10.0

    '''
    ADAS(b8000)
    '''

    center_offset_path = f'{b8000_adas_only_path}/center_offset.csv'
    waypoints = aa.get_waypoints(center_offset_path, 'svl')
    waypoints = waypoints[40:150]

    waypoints_x = []
    waypoints_y = []
    
    for waypoint in waypoints:
        waypoints_x.append(float(waypoint[0]))
        waypoints_y.append(float(waypoint[1]))

    plt.plot(waypoints_x, waypoints_y, color='b', linewidth=line_width)

    '''
    ADAS(b8000) + SeqWr(b3000)
    '''

    center_offset_path = f'{b8000_adas_b3000_seqwr_path}/center_offset.csv'
    waypoints = aa.get_waypoints(center_offset_path, 'svl')
    waypoints = waypoints[40:150]

    waypoints_x = []
    waypoints_y = []
    
    for waypoint in waypoints:
        waypoints_x.append(float(waypoint[0]))
        waypoints_y.append(float(waypoint[1]))

    plt.plot(waypoints_x, waypoints_y, color='g', linewidth=line_width, linestyle='--')


    '''
    ADAS(b8000) + SeqWr
    '''

    center_offset_path = f'{b8000_adas_seqwr_path}/center_offset.csv'
    waypoints = aa.get_waypoints(center_offset_path, 'svl')
    waypoints = waypoints[40:150]

    waypoints_x = []
    waypoints_y = []
    
    for waypoint in waypoints:
        waypoints_x.append(float(waypoint[0]))
        waypoints_y.append(float(waypoint[1]))

    plt.plot(waypoints_x, waypoints_y, color='r', linewidth=line_width)

    plt.savefig('test.png')