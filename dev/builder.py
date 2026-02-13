import hashlib
import os
import zipfile
import sys

def get_lfs_list(dev_dir):
    lfs_path = os.path.join(dev_dir, "lfs.txt")
    if not os.path.exists(lfs_path):
        return []
    with open(lfs_path, "r") as f:
        return [line.strip().replace("\\", "/") for line in f if line.strip()]

def load_cache(cache_dir, platform):
    cache_file = os.path.join(cache_dir, f"{platform}.manifest.md5")
    cache_data = {}
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            for line in f:
                parts = line.strip().split(" ", 1)
                if len(parts) == 2:
                    cache_data[parts[1]] = parts[0]
    return cache_data, cache_file

def get_file_hash_with_progress(file_path):
    md5 = hashlib.md5()
    file_size = os.path.getsize(file_path)
    processed = 0
    with open(file_path, "rb") as rb:
        while chunk := rb.read(1024 * 1024):
            md5.update(chunk)
            processed += len(chunk)
            percent = int((processed / file_size) * 100)
            sys.stdout.write(f"\rHashing: [{percent}%] {os.path.basename(file_path)}")
            sys.stdout.flush()
    print()
    return md5.hexdigest()

def generate_manifest(target_dir, platform, dev_dir):
    print(f"--- Generating Manifest: {platform} ---")
    cache_dir = os.path.join(dev_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    lfs_files = get_lfs_list(dev_dir)
    cached_hashes, cache_path = load_cache(cache_dir, platform)
    
    exclude_items = {'manifest.md5', '.setup_done', 'update_temp', '__pycache__', '.git', 'output'}
    if platform == "windows":
        exclude_items.add('dependencies')

    target_files = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in exclude_items]
        for file in files:
            if file in exclude_items:
                continue
            target_files.append(os.path.join(root, file))

    output_path = os.path.join(target_dir, "src", "data", "manifest.md5")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    current_manifest_entries = []
    
    for file_path in sorted(target_files):
        clean_path = os.path.relpath(file_path, os.path.dirname(target_dir)).replace("\\", "/")
        platform_rel_path = os.path.relpath(file_path, target_dir).replace("\\", "/")
        
        if clean_path in lfs_files and clean_path in cached_hashes:
            hash_val = cached_hashes[clean_path]
        else:
            if clean_path in lfs_files:
                hash_val = get_file_hash_with_progress(file_path)
                cached_hashes[clean_path] = hash_val
            else:
                md5 = hashlib.md5()
                with open(file_path, "rb") as rb:
                    while chunk := rb.read(8192):
                        md5.update(chunk)
                hash_val = md5.hexdigest()

        current_manifest_entries.append(f"{hash_val} {platform_rel_path}\n")

    with open(output_path, "w") as f:
        f.writelines(current_manifest_entries)

    with open(cache_path, "w") as f:
        for path, h in cached_hashes.items():
            f.write(f"{h} {path}\n")

def create_zip(target_dir, platform, builds_dir):
    zip_name = os.path.join(builds_dir, f"{platform}.zip")
    print(f"--- Zipping: {zip_name} ---")
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(target_dir):
            if any(ex in root.replace("\\", "/") for ex in ['__pycache__', '.git', 'output', 'update_temp']):
                continue
            for file in files:
                if platform == "windows" and "src/dependencies" in root.replace("\\", "/"):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, target_dir)
                zipf.write(file_path, arcname)
    print(f"[OK] Build saved to {zip_name}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    builds_dir = os.path.join(root_dir, "builds")
    os.makedirs(builds_dir, exist_ok=True)

    choice = input("Select platform to build (1: Linux, 2: Windows, 3: Both): ").strip()
    platforms = []
    if choice == "1": platforms.append("linux")
    elif choice == "2": platforms.append("windows")
    elif choice == "3": platforms = ["linux", "windows"]
    else: return print("Invalid choice.")

    for p in platforms:
        target_path = os.path.abspath(os.path.join(root_dir, p))
        if os.path.exists(target_path):
            generate_manifest(target_path, p, script_dir)
            create_zip(target_path, p, builds_dir)
        else:
            print(f"Error: {target_path} not found.")

if __name__ == "__main__":
    main()