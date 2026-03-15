import os
from pathlib import Path

# 檢查必要繳交檔案
required_files = [
    'README.md',
    'shelter_risk_audit.json', 
    'risk_map.png',
    'ARIA.ipynb'
]

print('檢查必要繳交檔案:')
for file in required_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f'  OK {file}: {size/1024:.1f} KB')
    else:
        print(f'  FAIL {file}: 不存在')

print('\n檢查輸出檔案:')
output_files = [
    'outputs/interactive_risk_map_rebuilt.html',
    'outputs/static_risk_map_rebuilt.png',
    'outputs/capacity_analysis_charts_rebuilt.png',
    'outputs/risk_assessment_report_rebuilt.md'
]

for file in output_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f'  OK {file}: {size/1024:.1f} KB')
    else:
        print(f'  FAIL {file}: 不存在')

print('\n檢查風險清單內容:')
if os.path.exists('shelter_risk_audit.json'):
    import json
    with open('shelter_risk_audit.json', 'r', encoding='utf-8') as f:
        risk_audit = json.load(f)
    print(f'  OK 風險清單: {len(risk_audit)} 筆記錄')
    
    # 檢查風險分佈
    risk_levels = {}
    for item in risk_audit:
        level = item['risk_level']
        risk_levels[level] = risk_levels.get(level, 0) + 1
    
    print('  風險分佈:')
    for level, count in risk_levels.items():
        print(f'    {level}: {count} 個')
else:
    print('  FAIL 風險清單: 不存在')

print('\n檢查README.md內容:')
if os.path.exists('README.md'):
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'AI 診斷日誌' in content:
        print('  OK README.md: 包含 AI 診斷日誌')
    else:
        print('  FAIL README.md: 缺少 AI 診斷日誌')
    
    if '完全重建版' in content:
        print('  OK README.md: 包含重建版本標記')
    else:
        print('  FAIL README.md: 缺少重建版本標記')
else:
    print('  FAIL README.md: 不存在')
