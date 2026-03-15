import geopandas as gpd
import json

# 載入真實風險分級資料
shelters = gpd.read_file('data/shelters_with_risk_rebuilt.geojson')

# 轉換為 WGS84 坐標
shelters_wgs84 = shelters.to_crs('EPSG:4326')

# 創建風險清單
risk_audit = []
for idx, shelter in shelters_wgs84.iterrows():
    audit_item = {
        'shelter_id': f'shelter_{idx:05d}',
        'name': shelter.get('避難所名稱', f'避難所_{idx}'),
        'risk_level': shelter['risk_level'],
        'capacity': int(shelter.get('收容人數', 0)),
        'longitude': float(shelter.geometry.x),
        'latitude': float(shelter.geometry.y),
        'address': shelter.get('地址', '未知地址'),
        'district': shelter.get('行政區', '未知行政區')
    }
    risk_audit.append(audit_item)

# 保存風險清單
with open('shelter_risk_audit.json', 'w', encoding='utf-8') as f:
    json.dump(risk_audit, f, ensure_ascii=False, indent=2)

print(f'風險清單已更新: {len(risk_audit)} 筆真實避難所資料')
print('前5筆資料:')
for i, item in enumerate(risk_audit[:5]):
    print(f'  {i+1}. {item["name"]} - {item["risk_level"]} ({item["capacity"]}人)')
