#!/bin/bash

DURATION=3000 #(ms)

BASE_EVENTS=cpu-cycles,cycles,instructions
BUS_EVENTS=bus_access,bus_access_rd,bus_access_wr,bus_cycles
L1D_EVENTS=l1d_cache,l1d_cache_refill,l1d_cache_refill_rd,l1d_cache_refill_wr,l1d_cache_wb
L1I_EVENTS=l1i_cache,l1i_cache_refill
L2D_EVENTS=l2d_cache,l2d_cache_refill,l2d_cache_refill_rd,l2d_cache_refill_wr,l2d_cache_wb
L3D_EVENTS=l3d_cache,l3d_cache_rd,l3d_cache_refill,armv8_pmuv3/l3d_cache_wb/

perf stat --timeout $DURATION -C 4-6 -e $BASE_EVENTS,$BUS_EVENTS,$L1D_EVENTS,$L1I_EVENTS,$L2D_EVENTS,$L3D_EVENTS -o log.txt



