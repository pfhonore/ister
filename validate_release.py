#!/usr/bin/python3

import argparse
import ctypes
import json
import os
import pwd
import subprocess
import sys
import tempfile
import time
import urllib.request as request

def handle_options():
    """Setup option parsing
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', default=None,
                        help='More verbose output.')
    parser.add_argument('-b' , '--bios', action='store', default=None,
                        help='Use specified bios file for qemu')
    args = parser.parse_args()

    if args.bios is None:
        print("Error: -b|--bios require")
        # print("{0}").format(parser.usage)
        sys.exit(1)

    return args

def validate_installer(args):

    print(">>> Spinning new installer into ./installer-val.img")
    if os.path.isfile('./installer-val.img'):
        os.remove('./installer-val.img')
    cp = subprocess.run(['qemu-img', 'create', 'installer-val.img', '2G'])
    cp = subprocess.run(['sudo', 'python3', 'ister.py', '-t',
                        'installer-config-vm.json', '-f', 'staging',
                        '-u',
                        'http://clearlinux-sandbox.jf.intel.com/update/'])
    cp.check_returncode()

    print(">>> Configuring installer-val.img to be driven by expect using new ister and gui")
    cp = subprocess.run(['sudo', './update_gui_expect.sh', 'installer-val.img'])
    cp.check_returncode()

    print(">>> Create target image for install")
    if os.path.isfile('installer-target.img'):
        os.remove('./installer-target.img')
    cp = subprocess.run(['qemu-img', 'create', 'installer-target.img', '10G'])
    cp.check_returncode()

    print(">>> Booting installer-val.img against installer-target.img")
    cp = subprocess.run(['sudo', 'qemu-system-x86_64', '-enable-kvm', '-m', '1024', '-vnc', '0.0.0.0:0', '-cpu', 'host', '-drive', 'file=installer-target.img,if=virtio,aio=threads', '-drive', 'file=installer-val.img,if=virtio,aio=threads', '-net', 'nic,model=virtio', '-net', 'user,hostfwd=tcp::2233-:22', '-smp', '2', '-bios', args.bios])
    cp.check_returncode()

    print(">>> Installing boot canary into installer-target.mg")
    cp = subprocess.run(['sudo', './install-canary.sh', 'installer-target.img'])
    cp.check_returncode()

    print(">>> Booting installer-target.img")
    cp = subprocess.run(['sudo', 'qemu-system-x86_64', '-enable-kvm', '-m', '1024', '-vnc', '0.0.0.0:0', '-cpu', 'host', '-drive', 'file=installer-target.img,if=virtio,aio=threads', '-net', 'nic,model=virtio', '-net', 'user,hostfwd=tcp::2233-:22', '-smp', '2', '-bios', args.bios])
    cp.check_returncode()

    # Check for boot canary
    cp = subprocess.run(['sudo', './check-canary.sh', 'installer-target.img'])

    if cp.returncode == 0:
        print(">>> SUCCESS! Boot Canary detected!")
    else:
        print(">>> Failure: installer-target.img failed to boot")


def main():
    """Start the installer
    """
    args = handle_options()
    try:
        validate_installer(args)
    except Exception as exep:
        print("Failed: {}".format(exep))
        sys.exit(-1)

    sys.exit(0)

if __name__ == '__main__':
    main()
