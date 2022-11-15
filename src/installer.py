import os
import shutil
import requests
import urllib.request
import win32com.client

url = 'https://github.com/Frikallo/MISST/releases/latest'
r = requests.get(url)
version = r.url.split('/')[-1]

print("MISST Install Wizard V0.1")
print("This script will install the required dependencies for MISST. As well as install the required files for the server and client.")
default_dir = os.path.expanduser('~') + "\MISST-Bundle"
install_dir = input(f"Enter dir in which to install MISST (defaults to '{default_dir}') ~200mb: ")
if install_dir == "":
    install_dir = default_dir
if os.path.exists(install_dir):
    print("Directory already exists, exiting.")
    exit()
else:
    try:
        os.mkdir(install_dir)
        os.chdir(install_dir)
    except:
        print("Failed to create directory, exiting.")
        exit()
print(f"Installing MISST to {os.path.abspath(install_dir)}")
print("Downloading binaries...")
try:
    urllib.request.urlretrieve(f"https://github.com/Frikallo/MISST/releases/download/{version}/MISSTwin32.zip", "MISST.zip")
except Exception as e:
    print(f"Failed to download binaries, exiting. ({e})")
    print("Failed to download binaries, exiting.")
    exit()

print("Extracting binaries...")
try:
    shutil.unpack_archive("MISST.zip", os.path.expanduser('~'))
except Exception as e:
    print(f"Failed to extract binaries, exiting. ({e})")
    exit()

print("Removing zip...")
try:
    os.remove("MISST.zip")
    os.chdir(os.path.expanduser('~'))
    os.rmdir(install_dir)
except:
    print("Failed to remove zip, exiting.")
    exit()

shortcut_dir = os.path.expanduser('~') + "\Desktop"
shortcut_name = "MISST.lnk"
shortcut_path = os.path.join(shortcut_dir, shortcut_name)
print(f"Creating shortcut on desktop ({shortcut_path})")
try:
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = os.path.abspath(os.path.expanduser('~')) + "\MISST\MISST.exe"
    shortcut.IconLocation = os.path.abspath(os.path.expanduser('~')) + "\MISST\icon.ico"
    shortcut.save()
except:
    print("Failed to create shortcut, exiting.")
    exit()

print("Installation complete!")