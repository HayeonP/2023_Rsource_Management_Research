#include <stdio.h>
#include <unistd.h>
// #include <sys/times.h>
// #include <sys/types.h>
#include <time.h>

#define L3_CACHE_SIZE (2*1024*1024)
#define CACHE_LINE_SIZE 64
#define TARGET_BANDWIDTH_MBs (15*1024)

#define ARRAY_SIZE_B (32 * L3_CACHE_SIZE)
#define ARRAY_SIZE_MB (ARRAY_SIZE_B / 1024 / 1024)

#define ARRAY_SIZE (ARRAY_SIZE_B / sizeof(int))
#define STRIDE_SIZE (CACHE_LINE_SIZE / sizeof(int))

#define SLEEP_TIME_US 1000

int x[ARRAY_SIZE]; /* array going to stride through */ 
long clk_tck;
struct timespec task_start_time_;
struct timespec task_end_time_;



int main() {
    int register index, stride, limit, target_elapsed_us;
    long elapsed;
    double sec0, sec;

    stride = STRIDE_SIZE;
    limit = ARRAY_SIZE - STRIDE_SIZE + 1; /* cache size this loop */
    target_elapsed_us = ARRAY_SIZE_MB * 1e6 / TARGET_BANDWIDTH_MBs;
    printf("target elapsed: %d \n", target_elapsed_us);

	while(1){
        clock_gettime(CLOCK_MONOTONIC, &task_start_time_);
        
        for (index=0; index < limit; index=index+stride) {
            x[index] = x[index] + 1; /* cache access */
        }

        clock_gettime(CLOCK_MONOTONIC, &task_end_time_);
        sec = (task_end_time_.tv_sec - task_start_time_.tv_sec) * 1e6 + (task_end_time_.tv_nsec - task_start_time_.tv_nsec) * 1e-3;
	    usleep(target_elapsed_us - sec);

        clock_gettime(CLOCK_MONOTONIC, &task_end_time_);
        sec = (task_end_time_.tv_sec - task_start_time_.tv_sec) + (task_end_time_.tv_nsec - task_start_time_.tv_nsec) * 1e-9;
	    printf("Size: %7ld Stride: %7ld elapsed: %7f \n",
	       ARRAY_SIZE*sizeof(int), stride*sizeof(int), sec);
	
	};
}

