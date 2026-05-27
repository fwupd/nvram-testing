# Find all subdirectories that contain a custom_VARS.builder.xml
SUBDIRS := $(dir $(wildcard */custom_VARS.builder.xml))

# Targets to forward to subdirectories
TARGETS := build custom_vars run dump extract clean compare

# Required: VM disk image filename, passed to nvram.py as --image.
IMAGE ?=
NVRAM_OPTS = --image "$(IMAGE)"

.PHONY: $(TARGETS) $(foreach target,$(TARGETS),$(addprefix $(target)-,$(SUBDIRS)))

# Define rules for each target
define make-target-rule
$(1):
	@for dir in $(SUBDIRS); do \
		echo "==> Entering $$$$dir"; \
		(cd "$$$$dir" && ../nvram.py $(NVRAM_OPTS) $(1)) || exit 1; \
	done
endef

$(foreach target,$(TARGETS),$(eval $(call make-target-rule,$(target))))

# Also allow running a specific target in a specific directory
# e.g., make build-"ASUSTeK - ROG MAXIMUS Z790 HERO/"
define make-subdir-target-rule
$(1)-$(2):
	@echo "==> Entering $(2)"
	@(cd "$(2)" && ../nvram.py $(NVRAM_OPTS) $(1))
endef

$(foreach target,$(TARGETS),$(foreach subdir,$(SUBDIRS),$(eval $(call make-subdir-target-rule,$(target),$(subdir)))))

# List discovered subdirectories
list:
	@echo "Discovered subdirectories:"
	@for dir in $(SUBDIRS); do echo "  $$dir"; done

# Help target
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Variables:"
	@echo "  IMAGE       Required. VM disk image filename, passed to nvram.py as --image."
	@echo "              Example: make run IMAGE=Fedora-Server-Guest-Generic-44-1.7.x86_64.qcow2"
	@echo ""
	@echo "Available targets:"
	@echo "  build       - Build custom_VARS.fd from custom_VARS.builder.xml"
	@echo "  custom_vars - Alias for build"
	@echo "  run         - Run QEMU with custom firmware"
	@echo "  dump        - Dump EFI variables from system"
	@echo "  extract     - Extract firmware signatures"
	@echo "  clean       - Remove generated files"
	@echo "  compare     - Compare old and new firmware"
	@echo "  list        - List discovered subdirectories"
	@echo ""
	@echo "All targets run in all subdirectories with custom_VARS.builder.xml."
	@echo ""
	@echo "To run a target in a specific subdirectory:"
	@echo "  make <target>-\"<subdir>/\""
	@echo ""
	@echo "Discovered subdirectories:"
	@for dir in $(SUBDIRS); do echo "  $$dir"; done
