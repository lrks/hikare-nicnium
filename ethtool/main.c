#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <linux/sockios.h>
#include <linux/ethtool.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
#include "../pcspkr/pcspkr.h"

#define ETHTOOL_LED_VALUE(arg) ((struct ethtool_led_value *)(arg))

struct ethtool_led_value {
	int fd;
	struct ifreq *ifr;
	int err;
	pthread_t thread;
	int thread_alive;
};

void *ethtool_led_on(void *args)
{
	int oldtype;
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, &oldtype);

	struct ethtool_value edata;
	edata.cmd = ETHTOOL_PHYS_ID;
	edata.data = 0;
	ETHTOOL_LED_VALUE(args)->ifr->ifr_data = (caddr_t)&edata;

	int err = ioctl(ETHTOOL_LED_VALUE(args)->fd, SIOCETHTOOL, ETHTOOL_LED_VALUE(args)->ifr);
	if (err < 0)
		printf("ERROR: do_phys_id, %d\n", err);

	ETHTOOL_LED_VALUE(args)->err = err;
	return args;
}

void led_on(void *args)
{
	if (ETHTOOL_LED_VALUE(args)->thread_alive)
		return;
	pthread_create(&(ETHTOOL_LED_VALUE(args)->thread), NULL, ethtool_led_on, args);
	ETHTOOL_LED_VALUE(args)->thread_alive = 1;
}

void led_off(void *args)
{
	if (!(ETHTOOL_LED_VALUE(args)->thread_alive))
		return;
	pthread_cancel(ETHTOOL_LED_VALUE(args)->thread);
	ETHTOOL_LED_VALUE(args)->thread_alive = 0;
}

int main(int argc, char *argv[])
{
	if (argc != 2) {
		printf("ERROR: argc\n");
		return 1;
	}

	struct ifreq ifr;
	memset(&ifr, 0, sizeof(struct ifreq));
	strncpy(ifr.ifr_name, argv[1], IFNAMSIZ);

	int fd = socket(AF_INET, SOCK_DGRAM, 0);
	if (fd < 0) {
		printf("ERROR: fd\n");
		return 1;
	}

	struct ethtool_led_value args;
	args.fd = fd;
	args.ifr = &ifr;
	args.err = 0;
	//args.thread = ;
	args.thread_alive = 0;
	pcspkr(&led_on, &led_off, (void *)&args);

	close(fd);
	return 0;
}
