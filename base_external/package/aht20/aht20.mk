
##############################################################
#
# AESDCHAR
#
##############################################################

AESDCHAR_VERSION = c92a6c9c02d5001c498d9937329d0daaaf9c9c05
AESDCHAR_SITE = git@github.com:cu-ecen-aeld/final-project-mamo6538.git
AESDCHAR_SITE_METHOD = git
AESD_ASSIGNMENTS_GIT_SUBMODULES = YES

AESDCHAR_MODULE_SUBDIRS = aht20_driver/
AESDCHAR_MODULE_MAKE_OPTS = KVERSION=$(LINUX_VERSION_PROBED)

$(eval $(kernel-module))

define AESDCHAR_INSTALL_TARGET_CMDS
	$(INSTALL) -m 0755 $(@D)/aht20_driver/aht20_load $(TARGET_DIR)/usr/bin/aht20_load
	$(INSTALL) -m 0755 $(@D)/aht20_driver/aht20_unload $(TARGET_DIR)/usr/bin/aht20_unload
	
endef
$(eval $(generic-package))
