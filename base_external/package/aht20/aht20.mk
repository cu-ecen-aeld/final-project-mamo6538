
##############################################################
#
# AESDCHAR
#
##############################################################

AHT20_VERSION = 98e03e91105ad77f8e9d0a5b149fffd92f04ee54
AHT20_SITE = git@github.com:cu-ecen-aeld/final-project-mamo6538.git
AHT20_SITE_METHOD = git
AHT20_GIT_SUBMODULES = NO

AHT20_MODULE_SUBDIRS = aht20_driver/
AHT20_MODULE_MAKE_OPTS = KVERSION=$(LINUX_VERSION_PROBED)

$(eval $(kernel-module))

define AHT20_INSTALL_TARGET_CMDS
	$(INSTALL) -m 0755 $(@D)/aht20_driver/aht20_load $(TARGET_DIR)/usr/bin/aht20_load
	$(INSTALL) -m 0755 $(@D)/aht20_driver/aht20_unload $(TARGET_DIR)/usr/bin/aht20_unload
	
endef
$(eval $(generic-package))
