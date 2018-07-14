#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include "pcspkr.h"

void a2ts(struct timespec *ts, const char *str)
{
	int ms = atoi(str);
	ts->tv_sec = (time_t)(ms / 1000);
	ts->tv_nsec = (ms % 1000) * (1000 * 1000);
}

void pcspkr(void (*led_on)(void *), void (*led_off)(void *), void *arg)
{
	char buf[BUFLEN];

	int note;
	void (*func)(void *);
	struct timespec req;

	int fd = open(DEVICE_CONSOLE, O_WRONLY);

	while (fgets(buf, BUFLEN, stdin) != NULL) {
		switch (buf[0]) {
		case '0':
			note = 0;
			func = led_off;
			a2ts(&req, &buf[1]);
			break;
		case '1:'
			a2ts(&req, &buf[4]);
			func = led_on;
			buf[4] = '\0';
			note = atoi(&buf[2]);
			break;
		default:
			continue;
		}

		(*func)(arg);
		if (note == 0) {
			ioctl(fd, KIOCSOUND, 0);
		} else {
			double freq = 440 * pow(2, (double)(note - 69) / (double)12);
			int val = (int)(CLOCK_TICK_RATE / freq);
			ioctl(fd, KIOCSOUND, val);
		}
		nanosleep(&req, NULL);
	}
}