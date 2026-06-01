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

color_map = {
    '단독주택': '#fcf4a3', '교육연구시설': '#00e5ff', '노유자시설': '#81d4fa',
    '운동시설': '#b39ddb', '업무시설': '#2962ff', '숙박시설': '#f50057',
    '위락시설': '#84ffff', '공동주택': '#ffb300', '자동차관련시설': '#651fff',
    '제1종근린생활시설': '#ffea00', '제2종근린생활시설': '#ffc400', '문화및집회시설': '#8c9eff'
}

z = r"C:\Users\zhaka\Desktop\Smart5.26\AL_D010_11_20260509.zip"
print("Loading data...")
gdf = gpd.read_file(f"zip://{z}", encoding='cp949', ignore_geometry=True)

print("Filtering...")
# A2 is PNU, A8 is Use Code, A14 is Total Floor Area (연면적 - let's use this or A12 for area. A12 is footprint. Image says Area 84772 for 367 parcels... wait 84772/367 = 230. Looks like footprint or 연면적. I'll use A12 footprint)
# Wait, A12 is footprint area (건축면적). Let's use A12.
gdf_songpa = gdf[gdf['A2'].str.startswith('11710')].copy()

gdf_songpa['Category'] = gdf_songpa['A8'].map(code_map).fillna('기타')
gdf_songpa = gdf_songpa[gdf_songpa['Category'].isin(target_categories)]

stats = gdf_songpa.groupby('Category').agg(
    Area=('A12', 'sum'),
    Parcels=('A2', 'nunique') # Unique PNUs to approximate parcel count
).reset_index()

# If order doesn't match perfectly it's fine, we sort by our list
order_map = {cat: i for i, cat in enumerate(target_categories)}
stats['order'] = stats['Category'].map(order_map)
stats = stats.sort_values('order').drop(columns=['order'])

total_area = stats['Area'].sum()
stats['Ratio'] = (stats['Area'] / total_area * 100).round(1)
stats['Area'] = stats['Area'].round(1)

results = stats.to_dict('records')
for r in results:
    r['Color'] = color_map.get(r['Category'], '#cccccc')

out_path = r"C:\Users\zhaka\Desktop\Smart5.26\statistics.json"
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(pd.DataFrame(results))
