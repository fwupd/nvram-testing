# Find all subdirectories that contain a custom_VARS.builder.xml
SUBDIRS := $(dir $(wildcard */custom_VARS.builder.xml))

# Targets to forward to subdirectories
TARGETS := build custom_vars get_reqs run dump extract clean compare

# Optional: passed to nvram.py as --image-url (affects get_reqs, run). Empty = script default.
IMAGE_URL ?=
# Optional: passed to nvram.py as --copy-in (get_reqs only). Empty = omit. Format: hostpath:guestdir (virt-customize).
COPY_IN ?=
NVRAM_OPTS = $(strip $(if $(strip $(IMAGE_URL)),--image-url "$(IMAGE_URL)") $(if $(strip $(COPY_IN)),--copy-in "$(COPY_IN)"))

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
	@echo "  IMAGE_URL   If set, passed to nvram.py as --image-url (for get_reqs and run)."
	@echo "              Example: make get_reqs IMAGE_URL=https://example.com/disk.qcow2"
	@echo "  COPY_IN     If set, passed to nvram.py as --copy-in (for get_reqs). hostpath:guestdir"
	@echo "              Example: make get_reqs COPY_IN=./extra.conf:/etc/"
	@echo ""
	@echo "Available targets:"
	@echo "  build       - Build custom_VARS.fd from custom_VARS.builder.xml"
	@echo "  custom_vars - Alias for build"
	@echo "  get_reqs    - Download requirements and customize VM image"
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
