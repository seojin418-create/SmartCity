import geopandas as gpd

land_zip = r"C:\Users\zhaka\Desktop\Smart5.26\AL_D194_11710_20250814.zip"
df = gpd.read_file(f"zip://{land_zip}", encoding='cp949', ignore_geometry=True).head()
print(df.iloc[0])
