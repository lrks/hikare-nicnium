#define BUFLEN 256
#define	DEVICE_CONSOLE "/dev/tty0"
#define CLOCK_TICK_RATE 1193180

void pcspkr(void (*led_on)(void *), void (*led_off)(void *), void *arg);
