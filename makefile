ifeq ($(EFFRHY_DIR),)
$(info The 'EFFRHY_DIR' environment variable must point to the root path of \
	the efficient rhythms repository.)
else

.PHONY: all clean

all: er_web/constants.py

er_web/constants.py: scripts/get_constants.py \
		$(EFFRHY_DIR)/efficient_rhythms/er_constants.py
	python3 $<

endif