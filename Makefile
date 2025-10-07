FWUPDTOOL=fwupdtool
IMAGE_URL=https://download.fedoraproject.org/pub/fedora/linux/releases/42/Server/x86_64/images/Fedora-Server-Guest-Generic-42-1.1.x86_64.qcow2
IMAGE=$(notdir $(IMAGE_URL))

custom_VARS.fd: custom_VARS.builder.xml
	$(FWUPDTOOL) firmware-build custom_VARS.builder.xml custom_VARS.fd
	cp custom_VARS.fd custom_VARS.bak

get_reqs:
	wget -nc -P ../ $(IMAGE_URL)
	cp ../$(IMAGE) .
	wget -nc -P ../ https://fwupd.org/downloads/093e6913dfecefbdaa9374a2e1caee7bf7e74c7eda847624e456e344884ba5f6-DBXUpdate-20241101-x64.cab
	gcab -x ../093e6913dfecefbdaa9374a2e1caee7bf7e74c7eda847624e456e344884ba5f6-DBXUpdate-20241101-x64.cab

run: get_reqs custom_VARS.fd
	qemu-system-x86_64 \
		-cpu host -machine type=q35,accel=kvm -m 4G -smp 4 \
		-nic user,model=virtio \
		-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.secboot.fd \
		-drive if=pflash,format=raw,file=custom_VARS.fd \
		$(IMAGE)

dump:
	dd if=/sys/firmware/efi/efivars/PK-8be4df61-93ca-11d2-aa0d-00e098032b8c of=PK-8be4df61-93ca-11d2-aa0d-00e098032b8c
	dd if=/sys/firmware/efi/efivars/KEK-8be4df61-93ca-11d2-aa0d-00e098032b8c of=KEK-8be4df61-93ca-11d2-aa0d-00e098032b8c
	dd if=/sys/firmware/efi/efivars/db-d719b2cb-3d3a-4596-a3bc-dad00e67656f of=db-d719b2cb-3d3a-4596-a3bc-dad00e67656f
	dd if=/sys/firmware/efi/efivars/dbx-d719b2cb-3d3a-4596-a3bc-dad00e67656f of=dbx-d719b2cb-3d3a-4596-a3bc-dad00e67656f

extract:
	$(FWUPDTOOL) firmware-extract PK-8be4df61-93ca-11d2-aa0d-00e098032b8c efi-signature-list
	$(FWUPDTOOL) firmware-extract KEK-8be4df61-93ca-11d2-aa0d-00e098032b8c efi-signature-list
	$(FWUPDTOOL) firmware-extract db-d719b2cb-3d3a-4596-a3bc-dad00e67656f efi-signature-list

%.siglist: %.builder.xml
	$(FWUPDTOOL) firmware-build $< $@

clean:
	rm -f *.siglist *.fd

compare:
	$(FWUPDTOOL) firmware-export custom_VARS.bak efi-volume > old.txt
	$(FWUPDTOOL) firmware-export custom_VARS.fd efi-volume > new.txt
	diff old.txt new.txt
