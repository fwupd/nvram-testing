# NVRAM Testing

## Build Requirements

Fedora/CentOS:

    sudo dnf install guestfs-tools make libvirt qemu-system-x86-core edk2-ovmf
    sudo dnf install python3-lxml python3-requests
    sudo dnf copr enable rhughes/fwupd
    sudo dnf update fwupd
    pip install behavex

# Testing

Each hardware model directory is built and booted as a BehaveX scenario. Run
the whole suite with:

    behavex features -D image=Fedora-Server-Guest-Generic-44-1.7.x86_64.qcow2

If `-D image=...` is omitted, the `IMAGE` environment variable is used, then
`Fedora-Server-Guest-Generic-44-1.7.x86_64.qcow2` as a last resort. Model
directories are discovered automatically (any directory with a
`custom_VARS.builder.xml`), so no feature-file changes are needed when adding
a model.

Each `run` step launches an interactive QEMU/VNC session, same as running
`nvram.py run` by hand — close the VM to let the scenario complete. Because
`nvram.py run` hardcodes the VNC display, don't run with
`--parallel-processes` greater than 1.

# Adding Models

 * run `./nvram.py add-current` in the parent directory. A new directory in
    format of VENDOR-FAMILY-MODEL of the current machine is created with EFI
    variables containing PK, KEK and DB certificates and DB exclusion lists
    are created along with `custom_VARS.builder.xml` file. For the time being,
    an old DBX is added without the info gathered from the machine being used
 * Adjust the `custom_VARS.builder.xml` as needed to include the suitable certificates
 * Build a `custom_VARS.fd` by running `../nvram.py build custom_VARS.fd`
 * Run the emulator using `../nvram.py run`
 * Commit the raw only, for instance `git add *.builder.xml PK* KEK* db*`

## DBX

An old DBX is included in the repo but you can get it as well from the LVFS using:

    wget https://fwupd.org/downloads/093e6913dfecefbdaa9374a2e1caee7bf7e74c7eda847624e456e344884ba5f6-DBXUpdate-20241101-x64.cab

You'll probably also need to install `gcab` to unpack it:

    gcab -x *DBXUpdate-20241101-x64.cab
