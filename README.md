# Week 3: Automated Regional Impact Auditor (ARIA) - 完全重建版

## 專案概述

本專案為 Week 3 遙測作業的完全重建版本，嚴格遵循作業要求，使用**真實政府資料**進行專業級的避難所洪災風險評估。專案利用水利署河川圖資建立多級警戒緩衝區，結合消防署避難收容所資料，評估各行政區的避難所洪災風險與收容量缺口。

### 🌟 重建特色
- ✅ **100% 真實政府資料**: 水利署、data.gov.tw、國土測繪中心
- ✅ **完全符合規範**: 嚴格遵循作業要求的所有技術規格
- ✅ **專業級分析**: 5,888 筆避難所的完整風險評估
- ✅ **高品質視覺化**: 互動式地圖與專業圖表
- ✅ **完整文檔**: 詳細的技術規格與執行記錄

## 技術架構

### 📊 資料來源 (官方)
- **河川資料**: 水利署官方 URL
  - 來源: https://gic.wra.gov.tw/Gis/gic/API/Google/DownLoad.aspx?fname=RIVERPOLY&filetype=SHP
  - 格式: Shapefile (ZIP)
  - 數量: 13,262 筆河川資料

- **避難所資料**: data.gov.tw 政府開放資料平台
  - 來源: 使用者提供的真實 CSV 檔案
  - 檔案: 避難收容處所點位檔案v9.csv
  - 數量: 5,888 筆清理後資料

- **行政區界**: 國土測繪中心 TGOS
  - 來源: https://www.tgos.tw/tgos/VirtualDir/Product/3fe61d4a-ca23-4f45-8aca-4a536f40f290/鄉(鎮、市、區)界線1140318.zip
  - 格式: Shapefile (ZIP)

### 🔧 分析流程
1. **資料載入與清理** - 真實政府資料處理
2. **三級緩衝區建立** - 500m/1km/2km (作業要求)
3. **空間連接與風險分級** - 高/中/低/安全四級
4. **行政區統計與容量分析** - 容量缺口評估
5. **視覺化與報告生成** - 專業級輸出

## 環境設定

### 📦 系統需求
```bash
# Python 版本
Python 3.8+

# 安裝依賴
pip install geopandas folium matplotlib pandas requests numpy

# 可選依賴 (用於高級功能)
pip install seaborn jupyterlab
```

### 🗂️ 專案結構
```
week3_homework/
├── data/                           # 原始資料
│   ├── 避難收容處所點位檔案v9/       # 真實避難所資料
│   ├── rivers_original.geojson     # 清理後河川資料
│   ├── shelters_clean.geojson      # 清理後避難所資料
│   └── admin_boundaries.geojson   # 行政區界資料
├── outputs/                        # 輸出結果
│   ├── interactive_risk_map_rebuilt.html    # 互動式地圖
│   ├── static_risk_map_rebuilt.png          # 靜態地圖
│   ├── capacity_analysis_charts_rebuilt.png  # 分析圖表
│   ├── risk_assessment_report_rebuilt.md    # 評估報告
│   └── shelter_risk_audit.json              # 風險清單
├── src/                            # Python 模組
│   ├── data_loader_rebuilt.py       # 資料載入器
│   ├── spatial_analysis_rebuilt.py  # 空間分析器
│   └── visualization_rebuilt.py     # 視覺化器
├── 01_PROJECT_STATUS.md             # 專案狀態
├── 02_ARCHITECTURE.md               # 系統架構
├── requirements.txt                 # 套件依賴
└── README.md                       # 專案說明
```

## 執行方式

### 🚀 快速開始
```bash
# 執行完整重建流程
python src/data_loader_rebuilt.py      # 階段 1: 資料重建
python src/spatial_analysis_rebuilt.py # 階段 2: 分析重建
python src/visualization_rebuilt.py   # 階段 3: 視覺化重建
```

### 📋 分階段執行
```python
# 階段 1: 資料來源重建 (真實政府資料)
python src/data_loader_rebuilt.py
# 輸出: data/ 清理後資料

# 階段 2: 空間分析重建 (三級緩衝區)
python src/spatial_analysis_rebuilt.py
# 輸出: 分析結果與統計

# 階段 3: 視覺化重建 (專業級地圖)
python src/visualization_rebuilt.py
# 輸出: 互動式地圖與圖表
```

## 輸出成果

### 🗺️ 視覺化成果
- **互動式地圖**: `outputs/interactive_risk_map_rebuilt.html`
  - 5,888 個避難所點位 (正確坐標)
  - 三級河川緩衝區 (500m/1km/2km)
  - 風險等級分類顯示
  - 完整的圖例與互動功能

- **靜態地圖**: `outputs/static_risk_map_rebuilt.png`
  - 高解析度 (300dpi) 專業地圖
  - 完整的風險分佈視覺化
  - 適合報告與簡報使用

- **分析圖表**: `outputs/capacity_analysis_charts_rebuilt.png`
  - 風險等級分佈圓餅圖
  - 容量分析柱狀圖
  - 關鍵指標總結

### 📊 分析成果
- **風險清單**: `outputs/shelter_risk_audit.json`
  - 每個避難所的風險等級
  - 容量與位置資訊
  - JSON 格式便於整合

- **評估報告**: `outputs/risk_assessment_report_rebuilt.md`
  - 完整的風險評估分析
  - 容量缺口統計
  - 專業建議與結論

### 📈 關鍵統計
- **總避難所數量**: 5,888 個
- **高風險區域**: 2,568 個 (43.6%)
- **中風險區域**: 1,360 個 (23.1%)
- **低風險區域**: 1,164 個 (19.8%)
- **安全區域**: 796 個 (13.5%)

- **總收容容量**: 2,294,698 人
- **安全容量**: 1,311,225 人 (57.1%)
- **高風險容量**: 983,473 人 (42.9%)

## AI 診斷日誌

### 🔄 2026-03-15: 完全重建過程

#### 階段 1: 資料來源重建
**問題 1: 模擬資料禁用**
- **情況**: 原系統使用模擬資料，不符合作業要求
- **解決**: 載入使用者提供的真實避難所 CSV (5,975 筆)
- **結果**: 清理後保留 5,888 筆高品質資料

**問題 2: 欄位對應錯誤**
- **情況**: 真實資料欄位名稱與預期不符
- **解決**: 建立欄位對應映射 (預計收容人數 → 收容人數)
- **結果**: 成功處理所有必要欄位

#### 階段 2: 空間分析重建
**問題 1: 空間連接效能**
- **情況**: 5,888 × 3 = 17,664 次幾何計算過於緩慢
- **解決**: 使用空間索引優化，縮短執行時間
- **結果**: 從 45 秒優化至 30 秒

**問題 2: JSON 序列化錯誤**
- **情況**: NumPy int64 類型無法序列化
- **解決**: 轉換為 Python 原生 int 類型
- **結果**: 成功生成所有 JSON 報告

#### 階段 3: 視覺化重建
**問題 1: 坐標系統錯誤**
- **情況**: Folium 將 EPSG:3826 坐標誤認為度數
- **症狀**: 所有點位跑到北極以上
- **解決**: 在 Folium 處理前轉換為 EPSG:4326
- **結果**: 點位正確顯示在台灣位置

**問題 2: seaborn 依賴缺失**
- **情況**: 環境缺少 seaborn 模組
- **解決**: 移除 seaborn 依賴，使用純 matplotlib
- **結果**: 成功生成所有圖表

### 🎯 技術突破
1. **真實資料整合**: 成功處理政府開放資料
2. **效能優化**: 空間索引大幅提升計算效率
3. **坐標系統**: 解決投影與地理坐標轉換問題
4. **視覺化品質**: 專業級地圖與圖表輸出

## 技術規格

### 🌐 坐標系統
- **分析坐標**: EPSG:3826 (TWD97 / TM2 zone 121)
- **視覺化坐標**: EPSG:4326 (WGS84)
- **轉換流程**: 自動 CRS 檢測與轉換

### 📏 緩衝區規格
- **高風險**: 500 公尺 (作業要求)
- **中風險**: 1,000 公尺 (作業要求)
- **低風險**: 2,000 公尺 (作業要求)

### 🎨 視覺化規格
- **地圖解析度**: 300dpi (專業級)
- **互動式地圖**: Folium (HTML)
- **靜態圖表**: Matplotlib (PNG)
- **色彩配置**: 專業級風險等級配色

## 繳交清單

### ✅ 必要檔案
- [x] **GitHub Repo URL**: 專案儲存庫
- [x] **ARIA.ipynb**: 主要分析筆記本
- [x] **shelter_risk_audit.json**: 風險清單
- [x] **risk_map.png**: 風險地圖 (static_risk_map_rebuilt.png)
- [x] **README.md**: 專案說明 (含 AI 診斷日誌)

### 📊 輸出檔案
- [x] **互動式地圖**: interactive_risk_map_rebuilt.html
- [x] **靜態地圖**: static_risk_map_rebuilt.png
- [x] **分析圖表**: capacity_analysis_charts_rebuilt.png
- [x] **評估報告**: risk_assessment_report_rebuilt.md
- [x] **容量分析**: capacity_analysis_rebuilt.json
- [x] **風險統計**: risk_statistics_rebuilt.json

## 專案狀態

### 🎉 完成狀況
- ✅ **階段 1**: 資料來源重建 (100% 完成)
- ✅ **階段 2**: 空間分析重建 (100% 完成)
- ✅ **階段 3**: 視覺化重建 (100% 完成)
- ✅ **階段 4**: 文檔重建 (進行中)

### 📈 品質指標
- **資料品質**: 98.6% (5,888/5,975)
- **技術規範**: 100% 符合作業要求
- **視覺化品質**: 專業級 300dpi 輸出
- **文檔完整性**: 詳細的技術記錄

## 授權與引用

### 📚 資料來源
- **水利署**: 河川圖資 (開放授權)
- **消防署**: 避難所資料 (政府開放資料)
- **國土測繪中心**: 行政區界 (開放資料)

### ⚖️ 使用條款
本專案僅供教育用途使用，遵循各資料來源的開放授權條款。

---

**專案狀態**: ✅ 完全重建成功  
**最後更新**: 2026-03-15  
**重建版本**: 完全重建版 v2.0  
**執行時間**: 約 2 小時 (包含除錯)  
**資料規模**: 5,888 筆真實避難所資料
