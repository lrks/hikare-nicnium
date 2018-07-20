#include <stdint.h>

struct led_status {
	uint8_t id;
	uint8_t count;
};

void nicapp_main(uint8_t cnt_ports);
