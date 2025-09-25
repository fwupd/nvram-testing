# NVRAM Testing

## Build Requirements

    sudo dnf install qemu-system-x86-core edk2-ovmf
    sudo dnf copr enable rhughes/fwupd
    sudo dnf update fwupd

# Adding Models

 * Create a new directory, with the format `Vendor - Model`.
 * Dump the UEFI variables using `make dump`.
 * Extract them using `make -C ../ extract`
 * Build some `custom_*.builder.xml` with the certs you want to include in the NVRAM
 * Build a `custom_VARS.fd` by running `make custom_VARS.fd`
 * Run the emulator using `make run`
 * Commit the raw only, for instance `git add *.builder.xml PK* KEK* db*`

## DBX

You can get an old DBX from the LVFS using:

    wget https://fwupd.org/downloads/093e6913dfecefbdaa9374a2e1caee7bf7e74c7eda847624e456e344884ba5f6-DBXUpdate-20241101-x64.cab
    gcab -x *DBXUpdate-20241101-x64.cab
