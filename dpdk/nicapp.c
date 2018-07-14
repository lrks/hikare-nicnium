#include <rte_ethdev.h>
#include <unistd.h>
#include "nicapp.h"
#include "../pcspkr/pcspkr.h"

void led_on(void *args)
{
	uint8_t i, count = (uint8_t)*args;
	for (i=0; i<cnt_ports; i++)
		rte_eth_led_on(i);
}

void led_off(void *args)
{
	uint8_t i, count = (uint8_t)*args;
	for (i=0; i<cnt_ports; i++)
		rte_eth_led_off(id);
}

void nicapp_main(uint8_t cnt_ports)
{
	pcspkr(&led_on, &led_off, (void *)&cnt_ports);
}
