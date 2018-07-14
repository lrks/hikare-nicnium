.PHONY: dpdk ethtool

dpdk:
	cd dpdk && make clean && $(MAKE)
	cp dpdk/build/nicnium-dpdk ./

ethtool:
	cd ethtool && $(MAKE)
	cp ethtool/nicnium-ethtool ./
