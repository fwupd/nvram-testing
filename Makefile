FWUPDTOOL=fwupdtool

custom_VARS.fd: custom_VARS.builder.xml custom_PK.siglist custom_KEK.siglist custom_db.siglist custom_dbx.siglist
	$(FWUPDTOOL) firmware-build custom_VARS.builder.xml custom_VARS.fd
	cp custom_VARS.fd custom_VARS.bak

Fedora-Server-Guest-Generic-42-1.1.x86_64.qcow2:
	wget https://download.fedoraproject.org/pub/fedora/linux/releases/42/Server/x86_64/images/Fedora-Server-Guest-Generic-42-1.1.x86_64.qcow2

run: Fedora-Server-Guest-Generic-42-1.1.x86_64.qcow2 custom_VARS.fd
	qemu-system-x86_64 \
		-cpu host -machine type=q35,accel=kvm -m 4G -smp 4 \
		-nic user,model=virtio \
		-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.secboot.fd \
		-drive if=pflash,format=raw,file=custom_VARS.fd \
		Fedora-Server-Guest-Generic-42-1.1.x86_64.qcow2

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
	$(FWUPDTOOL) firmware-extract custom_VARS.fd efi-volume
	echo "extracting"
	$(FWUPDTOOL) firmware-parse custom_PK.siglist efi-signature-list &> PK.bak
	$(FWUPDTOOL) firmware-parse id-PK.fw efi-signature-list &> PK.txt
	diff PK.bak PK.txt
	$(FWUPDTOOL) firmware-parse custom_KEK.siglist efi-signature-list &> KEK.bak
	$(FWUPDTOOL) firmware-parse id-KEK.fw efi-signature-list &> KEK.txt
	diff KEK.bak KEK.txt
	$(FWUPDTOOL) firmware-parse custom_dbx.siglist efi-signature-list &> dbx.bak
	$(FWUPDTOOL) firmware-parse id-dbx.fw efi-signature-list &> dbx.txt
	diff dbx.bak dbx.txt
	$(FWUPDTOOL) firmware-parse custom_db.siglist efi-signature-list &> db.bak
	$(FWUPDTOOL) firmware-parse id-db.fw efi-signature-list &> db.txt
	diff db.bak db.txt
