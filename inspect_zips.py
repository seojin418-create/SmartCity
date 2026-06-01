import zipfile
import os

zips = [
    r"C:\Users\zhaka\Desktop\Smart5.26\AL_D010_11_20260509.zip",
    r"C:\Users\zhaka\Desktop\Smart5.26\AL_D194_11710_20250814.zip",
    r"C:\Users\zhaka\Desktop\Smart5.26\LSMD_CONT_LDREG_Songpa.zip"
]

for z in zips:
    if os.path.exists(z):
        print(f"--- Contents of {os.path.basename(z)} ---")
        try:
            with zipfile.ZipFile(z, 'r') as zf:
                for info in zf.infolist():
                    print(f"  {info.filename} ({info.file_size} bytes)")
        except Exception as e:
            print(f"Error reading {z}: {e}")
    else:
        print(f"File not found: {z}")
