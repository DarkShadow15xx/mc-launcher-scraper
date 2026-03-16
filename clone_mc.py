import subprocess
import os
import re
import shutil

# --- Configuration ---
APKTOOL_JAR = "apktool.jar"
VANILLA_FOLDER = "vanilla"
MODIFIED_FOLDER = "modified-mc"
TEMP_DIR = "temp_work"
KEYSTORE_FILE = "my-release-key.jks"
KS_ALIAS = "my_alias"
KS_PASS = "password123"

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def patch_smali(directory, old_pkg, new_pkg):
    old_pkg_slash = old_pkg.replace(".", "/")
    new_pkg_slash = new_pkg.replace(".", "/")
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".smali", ".xml", ".yml")):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()
                
                new_data = data.replace(old_pkg, new_pkg).replace(old_pkg_slash, new_pkg_slash)
                
                if data != new_data:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_data)

def process_apks():
    if not os.path.exists(MODIFIED_FOLDER):
        os.makedirs(MODIFIED_FOLDER)

    for apk_file in os.listdir(VANILLA_FOLDER):
        if not apk_file.endswith(".apk"): continue

        # Extract version for package name (e.g., 1.20.1 -> 1201)
        version_match = re.search(r'(\d+\.\d+\.\d+)', apk_file)
        raw_version = version_match.group(1) if version_match else "cloned"
        v_suffix = raw_version.replace(".", "")
        
        # Format requested: com.mojang.[version]
        new_package = f"com.mojang.{v_suffix}"
        
        print(f"--- Cloning Minecraft to: {new_package} ---")

        # 1. Decompile
        run_cmd(["java", "-jar", APKTOOL_JAR, "d", f"{VANILLA_FOLDER}/{apk_file}", "-o", TEMP_DIR, "-f"])

        # 2. Modify Manifest (Package Name, Target SDK, and Launcher)
        manifest_path = os.path.join(TEMP_DIR, "AndroidManifest.xml")
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update Package Name
        content = content.replace("com.mojang.minecraftpe", new_package)
        
        # Update Target SDK to modern Android (Target 34 = Android 14)
        content = re.sub(r'android:targetSdkVersion="\d+"', 'android:targetSdkVersion="34"', content)
        
        # Remove Launcher Intent (removes home screen icon)
        content = re.sub(r'<category\s+android:name="android.intent.category.LAUNCHER"\s*/>', '', content)
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 3. Deep patch smali files
        patch_smali(TEMP_DIR, "com.mojang.minecraftpe", new_package)

        # 4. Build
        # Note: we name the intermediate file temp.apk
        temp_build_apk = "temp_unsigned.apk"
        run_cmd(["java", "-jar", APKTOOL_JAR, "b", TEMP_DIR, "-o", temp_build_apk])

        # 5. Zipalign (Crucial for "App Not Compatible" errors)
        final_output_apk = os.path.join(MODIFIED_FOLDER, f"mc_{v_suffix}.apk")
        print("Aligning APK...")
        run_cmd(["zipalign", "-f", "-v", "4", temp_build_apk, final_output_apk])

        # 6. Sign
        print("Signing APK...")
        run_cmd(["apksigner", "sign", "--ks", KEYSTORE_FILE, "--ks-pass", f"pass:{KS_PASS}", 
                 "--ks-key-alias", KS_ALIAS, final_output_apk])

        # Cleanup
        if os.path.exists(temp_build_apk): os.remove(temp_build_apk)
        shutil.rmtree(TEMP_DIR)
        print(f"Success! Created: {final_output_apk}\n")

if __name__ == "__main__":
    process_apks()
                if data != new_data:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_data)

def process_apks():
    if not os.path.exists(MODIFIED_FOLDER):
        os.makedirs(MODIFIED_FOLDER)

    for apk_file in os.listdir(VANILLA_FOLDER):
        if not apk_file.endswith(".apk"): continue

        version_match = re.search(r'(\d+\.\d+\.\d+)', apk_file)
        v_num = version_match.group(1).replace(".", "_") if version_match else "cloned"
        new_package = f"com.mojang.mc_{v_num}"
        
        print(f"--- Cloning Version: {v_num} ---")

        # 1. Decompile
        run_cmd(["java", "-jar", APKTOOL_JAR, "d", f"{VANILLA_FOLDER}/{apk_file}", "-o", TEMP_DIR, "-f"])

        # 2. Modify Manifest & Smali References
        manifest_path = os.path.join(TEMP_DIR, "AndroidManifest.xml")
        with open(manifest_path, "r") as f:
            content = f.read()
        
        content = content.replace("com.mojang.minecraftpe", new_package)
        # Remove Launcher Intent
        content = re.sub(r'<category android:name="android.intent.category.LAUNCHER" />', '', content)
        
        with open(manifest_path, "w") as f:
            f.write(content)

        # Deep patch smali files to prevent 'Class Not Found' errors
        patch_smali(TEMP_DIR, "com.mojang.minecraftpe", new_package)

        # 3. Build
        output_apk = os.path.join(MODIFIED_FOLDER, f"mc_{v_num}.apk")
        run_cmd(["java", "-jar", APKTOOL_JAR, "b", TEMP_DIR, "-o", output_apk])

        # 4. Sign
        run_cmd(["apksigner", "sign", "--ks", KEYSTORE_FILE, "--ks-pass", f"pass:{KS_PASS}", 
                 "--ks-key-alias", KS_ALIAS, output_apk])

        shutil.rmtree(TEMP_DIR)
        print(f"Finished: {output_apk}")

if __name__ == "__main__":
    process_apks()
