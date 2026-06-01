import os

def convert(json_path, js_path, var_name):
    if not os.path.exists(json_path): return
    with open(json_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f"const {var_name} = {content};")

convert(r"C:\Users\zhaka\Desktop\Smart5.26\songpa_parcels.geojson", r"C:\Users\zhaka\Desktop\Smart5.26\data_parcels.js", "parcelData")
convert(r"C:\Users\zhaka\Desktop\Smart5.26\songpa_boundary.geojson", r"C:\Users\zhaka\Desktop\Smart5.26\data_boundary.js", "boundaryData")
