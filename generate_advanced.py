import geopandas as gpd
import pandas as pd
import json
import os

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

color_map = {
    '단독주택': '#fcf4a3', '교육연구시설': '#00e5ff', '노유자시설': '#81d4fa',
    '운동시설': '#b39ddb', '업무시설': '#2962ff', '숙박시설': '#f50057',
    '위락시설': '#84ffff', '공동주택': '#ffb300', '자동차관련시설': '#651fff',
    '제1종근린생활시설': '#ffea00', '제2종근린생활시설': '#ffc400', '문화및집회시설': '#8c9eff'
}

# 1. Extract boundary
cadastral_zip = r"C:\Users\zhaka\Desktop\Smart5.26\LSMD_CONT_LDREG_Songpa.zip"
print("Loading Cadastral data to generate boundary...")
# We only need the geometry
gdf_cadastral = gpd.read_file(f"zip://{cadastral_zip}", encoding='cp949')
print("Dissolving boundary...")
# Simplify geometry to make dissolve faster and GeoJSON smaller (tolerance 1 meter if projected, but it's likely EPSG:5174 or EPSG:5186)
# Actually, let's just create a convex hull or unary union. 
# Dissolve all into one single feature
boundary = gdf_cadastral.dissolve()
# Reproject to WGS84 for Leaflet (EPSG:4326)
print("Current CRS:", boundary.crs)
# Let's assume it has a valid CRS. If not, we might need to set it.
# Standard Korean cadastral maps from LX are usually EPSG:5174. 
# Let's check if CRS is empty.
if boundary.crs is None:
    print("CRS is missing, assuming EPSG:5174")
    boundary.set_crs(epsg=5174, inplace=True)

try:
    boundary_wgs84 = boundary.to_crs(epsg=4326)
except Exception as e:
    print(f"Error reprojecting: {e}, assuming EPSG:5174 and forcing...")
    boundary.set_crs(epsg=5174, allow_override=True, inplace=True)
    boundary_wgs84 = boundary.to_crs(epsg=4326)

# Save as GeoJSON
boundary_wgs84.to_file(r"C:\Users\zhaka\Desktop\Smart5.26\songpa_boundary.geojson", driver="GeoJSON")
print("Saved Songpa boundary geojson.")

# 2. Process Stats by Dong
bldg_zip = r"C:\Users\zhaka\Desktop\Smart5.26\AL_D010_11_20260509.zip"
print("Loading Building data for stats...")
gdf_bldg = gpd.read_file(f"zip://{bldg_zip}", encoding='cp949', ignore_geometry=True)
gdf_songpa = gdf_bldg[gdf_bldg['A2'].str.startswith('11710')].copy()

# A4 is 법정동명 (Legal Dong Name). e.g., '잠실동', '송파동'
# A8 is Use Code, A12 is Building Area
gdf_songpa['Category'] = gdf_songpa['A8'].map(code_map).fillna('기타')
gdf_songpa = gdf_songpa[gdf_songpa['Category'].isin(target_categories)]

# Make a function to format stats
def format_stats(df):
    stats = df.groupby('Category').agg(
        Area=('A12', 'sum'),
        Parcels=('A2', 'nunique')
    ).reset_index()
    
    order_map = {cat: i for i, cat in enumerate(target_categories)}
    stats['order'] = stats['Category'].map(order_map)
    stats = stats.sort_values('order').drop(columns=['order'])
    
    total_area = stats['Area'].sum()
    stats['Ratio'] = (stats['Area'] / total_area * 100).round(1) if total_area > 0 else 0
    stats['Area'] = stats['Area'].round(1)
    
    results = stats.to_dict('records')
    for r in results:
        r['Color'] = color_map.get(r['Category'], '#cccccc')
    return results

# Overall stats
overall_stats = format_stats(gdf_songpa)

# Stats by Dong
dong_stats = {}
dongs = gdf_songpa['A4'].unique()
for dong in dongs:
    if pd.isna(dong): continue
    df_dong = gdf_songpa[gdf_songpa['A4'] == dong]
    dong_stats[dong] = format_stats(df_dong)

final_data = {
    "전체": overall_stats,
    **dong_stats
}

out_path = r"C:\Users\zhaka\Desktop\Smart5.26\statistics_by_dong.json"
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print("Saved statistics_by_dong.json.")
