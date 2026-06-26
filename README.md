# NVRAM Testing

## Build Requirements

    sudo dnf install guestfs-tools make libvirt qemu-system-x86-core edk2-ovmf
    sudo dnf copr enable rhughes/fwupd
    sudo dnf update fwupd

# Adding Models

 * run `./nvram.py dump` in the parent directory. A new directory in format of VENDOR-FAMILY-MODEL is created
 * enter the new directory
 * Extract the varialbes using `../nvram.py extract`
 * Build some `custom_*.builder.xml` with the certs you want to include in the NVRAM
 * Build a `custom_VARS.fd` by running `../nvram.py build custom_VARS.fd`
 * Run the emulator using `../nvram.py run`
 * Commit the raw only, for instance `git add *.builder.xml PK* KEK* db*`

## DBX

You can get an old DBX from the LVFS using:

    wget https://fwupd.org/downloads/093e6913dfecefbdaa9374a2e1caee7bf7e74c7eda847624e456e344884ba5f6-DBXUpdate-20241101-x64.cab

You'll probably also need to install `gcab` to unpack it:

    gcab -x *DBXUpdate-20241101-x64.cab
