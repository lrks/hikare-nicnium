/*-
 *   BSD LICENSE
 *
 *   Copyright(c) 2015 Intel Corporation. All rights reserved.
 *   All rights reserved.
 *
 *   Redistribution and use in source and binary forms, with or without
 *   modification, are permitted provided that the following conditions
 *   are met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in
 *       the documentation and/or other materials provided with the
 *       distribution.
 *     * Neither the name of Intel Corporation nor the names of its
 *       contributors may be used to endorse or promote products derived
 *       from this software without specific prior written permission.
 *
 *   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 *   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 *   OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 *   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 *   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 *   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 *   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 *   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 *   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
/*-
 *   Original file: dpdk-stable-17.05.2/examples/ethtool/ethtool-app/ethapp.c
 */

#include <rte_ethdev.h>
#include <unistd.h>
#include <time.h>
#include "nicapp.h"

static void get_macaddr(uint8_t port_id)
{
	struct ether_addr mac_addr;

	if (!rte_eth_dev_is_valid_port(port_id)) {
		printf("Error: Invalid port number %i\n", port_id);
		return;
	}

	rte_eth_macaddr_get(port_id, &mac_addr);
	printf(
		"Port %i MAC Address: %02x:%02x:%02x:%02x:%02x:%02x\n",
		port_id,
		mac_addr.addr_bytes[0],
		mac_addr.addr_bytes[1],
		mac_addr.addr_bytes[2],
		mac_addr.addr_bytes[3],
		mac_addr.addr_bytes[4],
		mac_addr.addr_bytes[5]);
}

static void control_led(uint8_t port_id, int flg)
{
	flg ? rte_eth_led_on(port_id) : rte_eth_led_off(port_id);
}

void nicapp_main(uint8_t cnt_ports)
{
	int i;
	uint8_t id;

	for (id=0; id<cnt_ports; id++)
		get_macaddr(id);

	/*
	for (i=0; i<10; i++) {
		for (id=0; id<cnt_ports; id++)
			control_led(id, (id + i) % 2);
		sleep(1);
	}

	for (id=0; id<cnt_ports; id++)
		control_led(id, 0);
	*/

	while (1) {
		struct timespec req = { 0, 10 * 1000 * 1000 };
		rte_eth_led_on(0);
		nanosleep(&req, NULL);
		rte_eth_led_off(0);
		sleep(1);
	}
}
