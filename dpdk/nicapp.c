#include <rte_ethdev.h>
#include <unistd.h>
#include "nicapp.h"
#include "../pcspkr/pcspkr.h"

static void led_on(void *args)
{
	struct led_status *status = (struct led_status *)args;
	status->id = (status->id + 1) % status->count;
	rte_eth_led_on(status->id);
}

static void led_off(void *args)
{
	struct led_status *status = (struct led_status *)args;
	rte_eth_led_off(status->id);
}

void nicapp_main(uint8_t cnt_ports)
{
	struct led_status status = { 0, cnt_ports };
	pcspkr(&led_on, &led_off, (void *)&status);

	uint8_t i;
	for (i=0; i<cnt_ports; i++)
		rte_eth_led_off(i);
}
