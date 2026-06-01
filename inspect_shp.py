import geopandas as gpd
import zipfile
import os

zips = [
    r"C:\Users\zhaka\Desktop\Smart5.26\AL_D010_11_20260509.zip",
    r"C:\Users\zhaka\Desktop\Smart5.26\AL_D194_11710_20250814.zip",
    r"C:\Users\zhaka\Desktop\Smart5.26\LSMD_CONT_LDREG_Songpa.zip"
]

for z in zips:
    if os.path.exists(z):
        print(f"\n--- Reading schema from {os.path.basename(z)} ---")
        try:
            # We can read directly from zip with geopandas using zip:// URI
            uri = f"zip://{z}"
            gdf = gpd.read_file(uri, rows=5)
            print("Columns:", gdf.columns.tolist())
            print(gdf.drop(columns='geometry', errors='ignore').head(2))
        except Exception as e:
            print(f"Error reading {z}: {e}")
