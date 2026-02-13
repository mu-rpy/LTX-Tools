import hashlib
import os
import sys

def check_integrity(manifest_path):
    if not os.path.exists(manifest_path):
        print(f"[ERROR] Manifest {manifest_path} not found.")
        sys.exit(1)

    failed = False
    with open(manifest_path, "r") as f:
        for line in f:
            if not line.strip(): continue
            expected_hash, rel_path = line.split(maxsplit=1)
            rel_path = rel_path.strip().replace("/", os.sep)
            
            if os.path.exists(rel_path):
                md5 = hashlib.md5()
                with open(rel_path, "rb") as f_bin:
                    while chunk := f_bin.read(4096):
                        md5.update(chunk)
                
                if md5.hexdigest() != expected_hash:
                    print(f"[FAIL] {rel_path}")
                    failed = True
                else:
                    print(f"[PASS] {rel_path}")
            else:
                print(f"[MISSING] {rel_path}")
                failed = True
    
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    # Path relative to where start.bat runs
    check_integrity(os.path.join("src", "data", "manifest.md5"))