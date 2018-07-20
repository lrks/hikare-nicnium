#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <linux/kd.h>
#include <math.h>
#include "pcspkr.h"

static void a2ts(struct timespec *ts, const char *str)
{
	int ms = atoi(str);
	ts->tv_sec = (time_t)(ms / 1000);
	ts->tv_nsec = (ms % 1000) * (1000 * 1000);
}

void pcspkr(void (*led_on)(void *), void (*led_off)(void *), void *arg)
{
	char buf[BUFLEN];

	double freq;
	void (*func)(void *);
	struct timespec req;

	int fd = open(DEVICE_CONSOLE, O_WRONLY);

	while (fgets(buf, BUFLEN, stdin) != NULL) {
		if (strlen(buf) < 7)
			continue;
		buf[5] = '\0';

		freq = atof(buf);
		a2ts(&req, &buf[6]);
		func = (freq == 0.0) ? led_off : led_on;

		(*func)(arg);
		if (freq == 0.0) {
			ioctl(fd, KIOCSOUND, 0);
			fprintf(stderr, "-_-, %ld[s]+%ld[ns]\n", req.tv_sec, req.tv_nsec);
		} else {
			int val = (int)(CLOCK_TICK_RATE / freq);
			ioctl(fd, KIOCSOUND, val);
			fprintf(stderr, "^_^, %d[Hz], %ld[s]+%ld[ns]\n", (int)freq, req.tv_sec, req.tv_nsec);
		}
		nanosleep(&req, NULL);
	}

	ioctl(fd, KIOCSOUND, 0);
	(*led_off)(arg);
}
