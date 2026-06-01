import geopandas as gpd
import pandas as pd
import json

# 1. Load Cadastral (for Geometry)
print("Loading Cadastral data...")
cadastral_zip = r"C:\Users\zhaka\Desktop\Smart5.26\LSMD_CONT_LDREG_Songpa.zip"
gdf_cad = gpd.read_file(f"zip://{cadastral_zip}", encoding='cp949')

# 2. Load D194 (Land attributes)
print("Loading D194 (Land) data...")
land_zip = r"C:\Users\zhaka\Desktop\Smart5.26\AL_D194_11710_20250814.zip"
df_land = gpd.read_file(f"zip://{land_zip}", encoding='cp949', ignore_geometry=True)
# A1: PNU, A11: LandCategory (지목), A14: Zoning (용도지역)
df_land_sub = df_land[['A1', 'A11', 'A14']].rename(columns={
    'A1': 'PNU',
    'A11': 'LandCategory',
    'A14': 'Zoning'
})

# Drop duplicates just in case
df_land_sub = df_land_sub.drop_duplicates(subset=['PNU'])

# 3. Load D010 (Building attributes)
print("Loading D010 (Building) data...")
bldg_zip = r"C:\Users\zhaka\Desktop\Smart5.26\AL_D010_11_20260509.zip"
df_bldg = gpd.read_file(f"zip://{bldg_zip}", encoding='cp949', ignore_geometry=True)
df_songpa_bldg = df_bldg[df_bldg['A2'].str.startswith('11710')].copy()

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
df_songpa_bldg['Category'] = df_songpa_bldg['A8'].map(code_map).fillna('기타')
df_songpa_bldg = df_songpa_bldg[df_songpa_bldg['Category'].isin(target_categories)]

# Aggregate Building Data
df_songpa_bldg = df_songpa_bldg.sort_values('A14', ascending=False)
agg_bldg = df_songpa_bldg.groupby('A2').agg(
    Area=('A14', 'sum'),
    Category=('Category', 'first'),
    Dong=('A4', 'first')
).reset_index()

# 4. Merge all together
print("Merging Cadastral, Land, and Building data...")
gdf_merged = gdf_cad.merge(df_land_sub, on='PNU', how='inner')
gdf_merged = gdf_merged.merge(agg_bldg, left_on='PNU', right_on='A2', how='inner')

print(f"Merged rows: {len(gdf_merged)}")

# Fill missing
gdf_merged['LandCategory'] = gdf_merged['LandCategory'].fillna('미상')
gdf_merged['Zoning'] = gdf_merged['Zoning'].fillna('미지정')

# Clean up empty strings
gdf_merged.loc[gdf_merged['LandCategory'] == '', 'LandCategory'] = '미상'
gdf_merged.loc[gdf_merged['Zoning'] == '', 'Zoning'] = '미지정'

print("Simplifying geometry...")
if gdf_merged.crs is None:
    gdf_merged.set_crs(epsg=5174, inplace=True)
gdf_merged.to_crs(epsg=4326, inplace=True)
gdf_merged['geometry'] = gdf_merged['geometry'].simplify(tolerance=0.00002, preserve_topology=True)

# 5. Export JS
print("Exporting to JS...")
gdf_final = gdf_merged[['PNU', 'Category', 'Area', 'Dong', 'LandCategory', 'Zoning', 'geometry']]
geojson_dict = json.loads(gdf_final.to_json())

js_content = "const parcelData = " + json.dumps(geojson_dict) + ";"
out_js = r"C:\Users\zhaka\Desktop\Smart5.26\data_parcels.js"
with open(out_js, 'w', encoding='utf-8') as f:
    f.write(js_content)

print("Saved to data_parcels.js successfully!")
