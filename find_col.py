import geopandas as gpd

z = r"C:\Users\zhaka\Desktop\Smart5.26\AL_D010_11_20260509.zip"
uri = f"zip://{z}"
gdf = gpd.read_file(uri, rows=100, encoding='cp949')

for col in gdf.columns:
    unique_vals = gdf[col].dropna().unique()
    if len(unique_vals) > 0:
        print(f"{col}: {unique_vals[:5]}")
