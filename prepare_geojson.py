import geopandas as gpd
import pandas as pd
import json

code_map = {
    '01000': '단독주택', '02000': '공동주택', '03000': '제1종근린생활시설', '04000': '제2종근린생활시설',
    '05000': '문화및집회시설', '06000': '종교시설', '07000': '판매시설', '08000': '운수시설',
    '09000': '의료시설', '10000': '교육연구시설', '11000': '노유자시설', '12000': '수련시설',
    '13000': '운동시설', '14000': '업무시설', '15000': '숙박시설', '16000': '위락시설',
    '17000': '공장', '18000': '창고시설', '19000': '위험물저장및처리시설', '20000': '자동차관련시설'
}

target_categories = [
    '단독주택', '교육연구시설', '노유자시설', '운동시설', '업무시설', 
    '숙박시설', '위락시설', '공동주택', '자동차관련시설', 
    '제1종근린생활시설', '제2종근린생활시설', '문화및집회시설'
]

print("Loading Cadastral data...")
cadastral_zip = r"C:\Users\zhaka\Desktop\Smart5.26\LSMD_CONT_LDREG_Songpa.zip"
gdf_cad = gpd.read_file(f"zip://{cadastral_zip}", encoding='cp949')
print(f"Cadastral rows: {len(gdf_cad)}")

print("Loading Building data...")
bldg_zip = r"C:\Users\zhaka\Desktop\Smart5.26\AL_D010_11_20260509.zip"
df_bldg = gpd.read_file(f"zip://{bldg_zip}", encoding='cp949', ignore_geometry=True)
df_songpa_bldg = df_bldg[df_bldg['A2'].str.startswith('11710')].copy()

# A2: PNU, A8: Use Code, A14: Total Floor Area, A4: Dong Name
df_songpa_bldg['Category'] = df_songpa_bldg['A8'].map(code_map).fillna('기타')
# Filter target categories
df_songpa_bldg = df_songpa_bldg[df_songpa_bldg['Category'].isin(target_categories)]

# Aggregate by PNU (sum area, take first category if multiple)
# We want the primary use. If a parcel has multiple buildings, maybe sort by area and take the largest?
df_songpa_bldg = df_songpa_bldg.sort_values('A14', ascending=False)
agg_bldg = df_songpa_bldg.groupby('A2').agg(
    Area=('A14', 'sum'),
    Category=('Category', 'first'),
    Dong=('A4', 'first')
).reset_index()

print(f"Building aggregated rows: {len(agg_bldg)}")

print("Merging...")
# Merge Cadastral (gdf_cad) and Buildings (agg_bldg)
# Left join on PNU
gdf_merged = gdf_cad.merge(agg_bldg, left_on='PNU', right_on='A2', how='inner')
print(f"Merged rows: {len(gdf_merged)}")

# To keep GeoJSON small (~14MB), simplify geometries and drop unnecessary columns
print("Simplifying geometry...")
if gdf_merged.crs is None:
    gdf_merged.set_crs(epsg=5174, inplace=True)
gdf_merged.to_crs(epsg=4326, inplace=True)

# Simplify with a small tolerance (e.g., 0.00005 degrees ~ 5m)
gdf_merged['geometry'] = gdf_merged['geometry'].simplify(tolerance=0.00002, preserve_topology=True)

# Keep only needed columns
gdf_final = gdf_merged[['PNU', 'Category', 'Area', 'Dong', 'geometry']]

# Save to GeoJSON
out_geojson = r"C:\Users\zhaka\Desktop\Smart5.26\songpa_parcels.geojson"
print("Saving GeoJSON...")
gdf_final.to_file(out_geojson, driver="GeoJSON")
print("Done!")
