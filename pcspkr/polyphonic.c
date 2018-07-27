#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <linux/kd.h>
#include <string.h>
#include <unistd.h>
#include "pcspkr.h"


void polyphonic(char *time, char *argv[], int argc)
{
	struct timespec duration;
	duration.tv_sec = 0;
	duration.tv_nsec = atoi(time);

	int i;
	int *values = (int *)malloc(sizeof(int) * argc);
	for (i=0; i<argc; i++) {
		double freq = atoi(argv[i]);
		values[i] = (int)(CLOCK_TICK_RATE / freq);
	}


	int fd = open(DEVICE_CONSOLE, O_WRONLY);
	while (1) {
		for (i=0; i<argc; i++) {
			ioctl(fd, KIOCSOUND, values[i]);
			nanosleep(&duration, NULL);
		}
	}
	ioctl(fd, KIOCSOUND, 0);
	close(fd);
}

int main(int argc, char *argv[])
{
	// $ ./polyphonic duration f1 f2 f3 ...
	if (argc < 3)
		return 1;

	polyphonic(argv[1], &argv[2], argc - 2);
	return 0;
}
