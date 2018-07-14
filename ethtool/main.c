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

#define ETHTOOL_LED_VALUE(arg) ((struct ethtool_led_value *)(arg))

struct ethtool_led_value {
	int fd;
	struct ifreq *ifr;
	int status;
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

	ETHTOOL_LED_VALUE(args)->status = err;
	return args;
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


	struct timespec req = { 0, 10 * 1000 * 1000 }; // Todo: ドライバとHzから求める
	struct ethtool_led_value args = { fd, &ifr, 0 };
	while (args.status >= 0) {
		pthread_t thread;
		pthread_create(&thread, NULL, ethtool_led_on, (void *)&args);
		nanosleep(&req, NULL);

		int r = pthread_cancel(thread);
		if (r != 0)
			break;
		sleep(1);
	}

	close(fd);
	return 0;
}
