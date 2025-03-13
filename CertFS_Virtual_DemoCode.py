# NOTE THAT THIS CODE IS COMPLETELY UNTESTED AND IS AI-Generated

import os
import base64
import subprocess
import requests
from fusepy import FUSE, Operations

# Azure IMDS and Key Vault configuration
IMDS_ENDPOINT = "http://169.254.169.254/metadata/identity/oauth2/token"
KV_URL = os.getenv("KV_URL")  # Set this as an environment variable

if not KV_URL:
    raise ValueError("KV_URL environment variable is not set.")

class CertFS(Operations):
    def __init__(self):
        self.token = self.get_msi_token()

    def get_msi_token(self):
        """Get MSI token from IMDS"""
        try:
            response = requests.get(
                IMDS_ENDPOINT,
                params={
                    "api-version": "2019-08-01",
                    "resource": "https://vault.azure.net"
                },
                headers={"Metadata": "true"},
                timeout=5
            )
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get MSI token: {e}")

    def get_secret_from_kv(self, secret_name):
        """Fetch the PFX secret from Azure Key Vault"""
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        secret_url = f"{KV_URL}/secrets/{secret_name}?api-version=7.2"

        try:
            response = requests.get(secret_url, headers=headers, timeout=5)
            response.raise_for_status()
            return base64.b64decode(response.json()["value"])  # Decode PFX from Base64
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch secret {secret_name}: {e}")

    def getattr(self, path, fh=None):
        return {'st_mode': 0o444 | 0o100000, 'st_nlink': 1, 'st_size': 4096}

    def read(self, path, size, offset, fh):
        """Dynamically fetch the certificate and return its content"""
        secret_name = path.lstrip("/")  # Filename is used as secret name

        print(f"Fetching secret: {secret_name} from Key Vault...")
        try:
            pfx_bytes = self.get_secret_from_kv(secret_name)
        except RuntimeError as e:
            return f"ERROR: {e}".encode()

        # 1. Mount RAMFS at /mnt/certfs2
        os.system("mkdir -p /mnt/certfs2 && mount -t ramfs -o size=10M ramfs /mnt/certfs2 && chmod 700 /mnt/certfs2")

        extracted_path = ""
        try:
            # 2. Write PFX to RAMFS
            pfx_path = "/mnt/certfs2/cert.pfx"
            with open(pfx_path, "wb") as tmp_pfx:
                tmp_pfx.write(pfx_bytes)

            # 3. Determine extraction command
            if path == "/gcscert.pem":
                extracted_path = "/mnt/certfs2/gcscert.pem"
                cmd = ["openssl", "pkcs12", "-in", pfx_path, "-out", extracted_path, "-nodes", "-nokeys", "-passin", "pass:"]
            elif path == "/gcskey.pem":
                extracted_path = "/mnt/certfs2/gcskey.pem"
                cmd = ["openssl", "pkcs12", "-in", pfx_path, "-out", extracted_path, "-nodes", "-nocerts", "-passin", "pass:"]
            else:
                return f"ERROR: Unknown file request {path}".encode()

            print(f"Running OpenSSL: {' '.join(cmd)}")
            subprocess.run(cmd, stderr=subprocess.PIPE, check=True)

            # 4. Read extracted file
            if not os.path.exists(extracted_path):
                return b"ERROR: Extraction failed."

            with open(extracted_path, "rb") as extracted_file:
                output = extracted_file.read()

        except Exception as e:
            output = f"ERROR: {str(e)}".encode()
        finally:
            # 5. Secure cleanup
            os.system("shred -u /mnt/certfs2/* && umount /mnt/certfs2 && rmdir /mnt/certfs2")

        return output

if __name__ == "__main__":
    # Ensure FUSE mount point exists
    if not os.path.exists("/mnt/kvfs"):
        os.mkdir("/mnt/kvfs")

    print("Starting FUSE filesystem at /mnt/kvfs...")
    FUSE(CertFS(), "/mnt/kvfs", foreground=True, ro=True)
