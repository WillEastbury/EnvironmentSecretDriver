#!/bin/bash

set -e  # Exit on error

# Required packages
PACKAGES=("fuse3" "python3-fusepy" "openssl")

echo "Checking dependencies..."
for pkg in "${PACKAGES[@]}"; do
    if ! dpkg -l | grep -qw "$pkg"; then
        echo "Installing missing package: $pkg"
        sudo apt update && sudo apt install -y "$pkg"
    fi
done

# Ensure MY_ENV_VAR is set
CERT_FILE="/mnt/c/source/cert.pfx"
if [ -f "$CERT_FILE" ]; then
    export MY_ENV_VAR=$(base64 -w 0 "$CERT_FILE")
    echo "MY_ENV_VAR set from $CERT_FILE"
else
    echo "Warning: $CERT_FILE not found. MY_ENV_VAR not set."
fi

# Create and mount the RAM-backed filesystem
MOUNT_POINT="/mnt/certfs"
if ! mount | grep -q "$MOUNT_POINT"; then
    echo "Setting up RAM-based filesystem at $MOUNT_POINT..."
    sudo mkdir -p "$MOUNT_POINT"
    sudo mount -t tmpfs -o size=10M tmpfs "$MOUNT_POINT"
    sudo chmod 700 "$MOUNT_POINT"
else
    echo "$MOUNT_POINT already mounted."
fi

# Ensure script exists before launching
FUSE_SCRIPT="/mnt/c/source/fusefs.py"
if [ ! -f "$FUSE_SCRIPT" ]; then
    echo "Error: $FUSE_SCRIPT not found!"
    exit 1
fi

# Launch the FUSE script
echo "Starting FUSE script..."
sudo -E nohup python3 "$FUSE_SCRIPT" > /var/log/fusefs.log 2>&1 &

echo "FUSE filesystem is now running. Logs available at /var/log/fusefs.log."
