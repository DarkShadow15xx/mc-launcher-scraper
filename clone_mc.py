import os
import zipfile
import shutil
import glob
import subprocess

# Your repository folders
VANILLA_DIR = 'Vanilla'
MODIFIED_DIR = 'mc-modified'

def process_apks():
    # Make sure the output folder exists
    os.makedirs(MODIFIED_DIR, exist_ok=True)

    # Find all APKs in the Vanilla folder
    apk_files = glob.glob(os.path.join(VANILLA_DIR, '*.apk'))
    
    if not apk_files:
        print("No APKs found in the Vanilla folder.")
        return

    for apk_path in apk_files:
        # Extract the version number from the filename (e.g., "1.20.10.apk" -> "1.20.10")
        filename = os.path.basename(apk_path)
        version = filename.replace('.apk', '')
        
        output_path = os.path.join(MODIFIED_DIR, version)
        zip_name = f"{version}_engine.zip"
        zip_path = os.path.join(MODIFIED_DIR, zip_name)
        
        os.makedirs(output_path, exist_ok=True)
        
        print(f"[{version}] Extracting core engine and assets...")

        # Open the APK (which is just a fancy ZIP file)
        with zipfile.ZipFile(apk_path, 'r') as apk:
            for file_info in apk.infolist():
                # We ONLY want the assets folder and the 64-bit C++ engine
                if file_info.filename.startswith('assets/') or 'arm64-v8a/libminecraftpe.so' in file_info.filename:
                    apk.extract(file_info, output_path)

        print(f"[{version}] Reorganizing files...")
        
        # The C++ script expects libminecraftpe.so to be right next to the assets folder.
        so_file_path = os.path.join(output_path, 'lib', 'arm64-v8a', 'libminecraftpe.so')
        if os.path.exists(so_file_path):
            shutil.move(so_file_path, os.path.join(output_path, 'libminecraftpe.so'))
            
            # Clean up the empty 'lib' folder
            shutil.rmtree(os.path.join(output_path, 'lib'))

        print(f"[{version}] Compressing for download...")
        shutil.make_archive(os.path.join(MODIFIED_DIR, f"{version}_engine"), 'zip', output_path)
        
        # Clean up the raw extracted folder to save space
        shutil.rmtree(output_path)
        
        print(f"[{version}] Sending to GitHub Releases...")
        # Use GitHub CLI to create a release and attach the ZIP
        try:
            subprocess.run([
                "gh", "release", "create", version, 
                zip_path, 
                "--title", f"Engine {version}", 
                "--notes", f"Automated extraction for EmpireX Launcher"
            ], check=True)
            print(f"[{version}] Successfully uploaded to Releases!")
        except subprocess.CalledProcessError:
            print(f"[{version}] Release might already exist or CLI failed. Continuing...")

        print(f"[{version}] Done! Ready for Launcher.\n")

if __name__ == "__main__":
    process_apks()
