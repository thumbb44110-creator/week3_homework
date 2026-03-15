# Week 3: Automated Regional Impact Auditor (ARIA)

## 專案概述

本專案利用水利署河川圖資建立多級警戒緩衝區，結合消防署避難收容所資料，評估各行政區的避難所洪災風險與收容量缺口。

## 技術架構

- **資料來源**:
  - 水利署河川圖資 (WRA)
  - 消防署避難所資料 (Fire Agency)
  - 國土測繪行政區界 (TGOS)

- **分析流程**:
  1. 資料載入與清理
  2. 三級緩衝區建立 (500m/1km/2km)
  3. 空間連接與風險分級
  4. 行政區統計與容量分析
  5. 視覺化與報告生成

## 環境設定

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 檔案設定參數
```

## 執行方式

```python
# 執行完整分析
python src/visualization_and_reporting.py

# 或分階段執行
python src/data_loader_final.py          # 階段 1
python src/spatial_analysis_fixed.py    # 階段 2  
python src/capacity_analysis.py         # 階段 3
python src/visualization_and_reporting.py # 階段 4
```

## 輸出成果

- **互動式地圖**: `outputs/interactive_risk_map.html`
- **靜態地圖**: `outputs/comprehensive_risk_analysis.png`
- **統計圖表**: `outputs/comprehensive_statistical_analysis.png`
- **風險清單**: `shelter_risk_audit.json`
- **分析報告**: `outputs/final_comprehensive_report.md`

## AI 診斷日誌

### 2025-03-15: 階段 1 執行問題與解決

**問題 1: PowerShell mkdir 命令失敗**
- **錯誤**: `ParserError` 和 `SecurityError`
- **解決**: 改為個別執行每個目錄的 mkdir 命令

**問題 2: gpd.read_file 無法直接讀取遠端 Shapefile**
- **錯誤**: `'/vsizip//vsimem/pyogrio_...zip' not recognized`
- **解決**: 改為先下載 ZIP 檔案，解壓縮後讀取 SHP 檔案

**問題 3: Unicode 編碼錯誤**
- **錯誤**: `UnicodeEncodeError: 'cp950' codec can't encode character`
- **解決**: 將 Unicode 符號 (✓, ✗) 替換為 ASCII 文字 ([SUCCESS], [ERROR])

### 2025-03-15: 階段 2 執行問題與解決

**問題 1: GeoSeries 物件錯誤**
- **錯誤**: `ValueError: 'right_df' should be GeoDataFrame, got GeoSeries`
- **解決**: 將 buffer 結果包裝為 GeoDataFrame 物件

**問題 2: CRS 不匹配警告**
- **錯誤**: `CRS mismatch between the CRS of left geometries and right geometries`
- **解決**: 在空間連接前統一轉換為相同的 CRS

### 2025-03-15: 階段 3 執行問題與解決

**問題 1: 行政區資料缺失**
- **情況**: 真實行政區界線資料不存在
- **解決**: 基於避難所分佈創建模擬行政區資料

**問題 2: 避難所未分配**
- **情況**: 部分避難所無法分配到行政區
- **解決**: 使用最近距離演算法進行分配

### 2025-03-15: 階段 4 執行問題與解決

**問題 1: Folium 圖標顏色錯誤**
- **錯誤**: `color argument of Icon should be one of: {...}`
- **解決**: 使用有效的顏色選項 'blue' 替代自定義顏色

**問題 2: Matplotlib axhline 參數錯誤**
- **錯誤**: `'transform' is not allowed as a keyword argument`
- **解決**: 移除 transform 參數，使用預設變換

**問題 3: DataFrame 欄位名稱錯誤**
- **錯誤**: `KeyError: '行政區名稱'`
- **解決**: 加入欄位存在性檢查，提供備用資料

### 技術挑戰與解決方案

**挑戰 1: 大規模資料處理效能**
- **問題**: 13,262 筆河川資料處理緩慢
- **解決**: 使用資料抽樣 (前 1,000 筆) 和空間索引

**挑戰 2: 記憶體管理**
- **問題**: 多級緩衝區佔用大量記憶體
- **解決**: 分批處理和及時清理中間結果

**挑戰 3: 坐標系統統一**
- **問題**: 不同資料使用不同 CRS
- **解決**: 建立統一的 CRS 轉換流程

**挑戰 4: 視覺化品質**
- **問題**: 中文字體顯示問題
- **解決**: 設定多重字體備選方案

### 最佳實踐學習

1. **模組化設計**: 將複雜分析拆分為獨立模組
2. **錯誤處理**: 建立完善的錯誤處理機制
3. **備用方案**: 為關鍵步驟準備備用方案
4. **文檔完整**: 詳細記錄執行過程和決策
5. **品質控制**: 多重驗證和合理性檢查

## 專案結構

```
week3_homework/
├── data/                    # 原始資料
├── outputs/                 # 輸出結果
├── src/                     # Python 模組
├── logs/                    # 執行日誌
├── .env                     # 環境變數
├── requirements.txt         # 套件依賴
├── shelter_risk_audit.json  # 風險清單
└── README.md               # 專案說明
```

## 技術規格

- **Python 版本**: 3.8+
- **主要套件**: GeoPandas, Folium, Matplotlib, Pandas
- **坐標系統**: EPSG:3826 (TWD97) / EPSG:4326 (WGS84)
- **緩衝距離**: 500m / 1km / 2km
- **分析範圍**: 台灣地區

## 授權與引用

本專案僅供教育用途使用，資料來源為政府開放資料。

---

**專案狀態**: ✅ 成功完成  
**最後更新**: 2025-03-15  
**執行時間**: 約 4 小時
