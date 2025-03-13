from fusepy import FUSE, Operations
import os
import base64
import subprocess

class CertFS(Operations):
    def __init__(self):
        self.pfx_data = os.getenv("MY_ENV_VAR", None)
        if not self.pfx_data:
            raise ValueError("MY_ENV_VAR is not set")
        self.pfx_bytes = base64.b64decode(self.pfx_data)

    def getattr(self, path, fh=None):
        return {'st_mode': 0o444 | 0o100000, 'st_nlink': 1, 'st_size': 4096}

    def read(self, path, size, offset, fh):
        print(f"READ REQUEST: {path}")
        if path not in ("/gcscert.pem", "/gcskey.pem"):
            print(f"INVALID FILE ACCESS: {path}")
            return b""

        # 1. Mount RAMFS
        print("Mounting RAMFS at /mnt/certfs2...")
        os.system("mkdir -p /mnt/certfs2 && mount -t ramfs -o size=10M ramfs /mnt/certfs2 && chmod 700 /mnt/certfs2")

        try:
            # 2. Write PFX to RAMFS
            with open("/mnt/certfs2/cert.pfx", "wb") as tmp_pfx:
                tmp_pfx.write(self.pfx_bytes)

            # 3. Extract the requested data
            print("Writing PFX data to /mnt/certfs2/cert.pfx")
            if path == "/gcscert.pem":
                cmd = ["openssl", "pkcs12", "-in", "/mnt/certfs2/cert.pfx", "-out", "/mnt/certfs2/gcscert.pem", "-nodes", "-nokeys","-passin", "pass:"]
            elif path == "/gcskey.pem":
                cmd = ["openssl", "pkcs12", "-in", "/mnt/certfs2/cert.pfx", "-out", "/mnt/certfs2/gcskey.pem", "-nodes", "-nocerts","-passin", "pass:"]

            print(f"Running OpenSSL: {' '.join(cmd)}")
            subprocess.run(cmd, stderr=subprocess.DEVNULL, check=True)

            # 4. Read and return the extracted content
            with open(f"/mnt/certfs2{path}", "rb") as extracted_file:
                output = extracted_file.read()

            print(f"Successfully read {len(output)} bytes from {extracted_file}")

        except Exception as e:
            output = f"ERROR: {str(e)}".encode()
            print(f"ERROR {str(e)}")

        finally:
            # 5. Secure cleanup
            os.system("shred -u /mnt/certfs2/* && umount /mnt/certfs2 && rmdir /mnt/certfs2")

        return output

# Start the FUSE filesystem at /mnt/kvfs
if __name__ == "__main__":
    FUSE(CertFS(), "/mnt/kvfs", foreground=True, ro=True)from fusepy import FUSE, Operations
import os
import base64
import subprocess

class CertFS(Operations):
    def __init__(self):
        self.pfx_data = os.getenv("MY_ENV_VAR", None)
        if not self.pfx_data:
            raise ValueError("MY_ENV_VAR is not set")
        self.pfx_bytes = base64.b64decode(self.pfx_data)

    def getattr(self, path, fh=None):
        return {'st_mode': 0o444 | 0o100000, 'st_nlink': 1, 'st_size': 4096}

    def read(self, path, size, offset, fh):
        print(f"READ REQUEST: {path}")
        if path not in ("/gcscert.pem", "/gcskey.pem"):
            print(f"INVALID FILE ACCESS: {path}")
            return b""

        # 1. Mount RAMFS
        print("Mounting RAMFS at /mnt/certfs2...")
        os.system("mkdir -p /mnt/certfs2 && mount -t ramfs -o size=10M ramfs /mnt/certfs2 && chmod 700 /mnt/certfs2")

        try:
            # 2. Write PFX to RAMFS
            with open("/mnt/certfs2/cert.pfx", "wb") as tmp_pfx:
                tmp_pfx.write(self.pfx_bytes)

            # 3. Extract the requested data
            print("Writing PFX data to /mnt/certfs2/cert.pfx")
            if path == "/gcscert.pem":
                cmd = ["openssl", "pkcs12", "-in", "/mnt/certfs2/cert.pfx", "-out", "/mnt/certfs2/gcscert.pem", "-nodes", "-nokeys","-passin", "pass:"]
            elif path == "/gcskey.pem":
                cmd = ["openssl", "pkcs12", "-in", "/mnt/certfs2/cert.pfx", "-out", "/mnt/certfs2/gcskey.pem", "-nodes", "-nocerts","-passin", "pass:"]

            print(f"Running OpenSSL: {' '.join(cmd)}")
            subprocess.run(cmd, stderr=subprocess.DEVNULL, check=True)

            # 4. Read and return the extracted content
            with open(f"/mnt/certfs2{path}", "rb") as extracted_file:
                output = extracted_file.read()

            print(f"Successfully read {len(output)} bytes from {extracted_file}")

        except Exception as e:
            output = f"ERROR: {str(e)}".encode()
            print(f"ERROR {str(e)}")

        finally:
            # 5. Secure cleanup
            os.system("shred -u /mnt/certfs2/* && umount /mnt/certfs2 && rmdir /mnt/certfs2")

        return output

# Start the FUSE filesystem at /mnt/kvfs
if __name__ == "__main__":
    FUSE(CertFS(), "/mnt/kvfs", foreground=True, ro=True)
