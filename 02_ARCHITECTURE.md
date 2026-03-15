# Week 3 作業系統架構

## 系統架構
```
week3_homework/
├── data/                    # 原始資料
│   ├── rivers_original.geojson
│   ├── shelters_clean.geojson
│   └── districts_clean.geojson
├── outputs/                 # 輸出結果
│   ├── risk_maps/
│   ├── statistics/
│   └── reports/
├── notebooks/               # Jupyter Notebook
│   ├── 01_data_preparation.ipynb
│   ├── 02_spatial_analysis.ipynb
│   ├── 03_capacity_analysis.ipynb
│   └── 04_visualization.ipynb
├── src/                     # Python 模組
│   ├── data_loader.py
│   ├── spatial_analysis.py
│   └── visualization.py
└── logs/                    # 執行日誌
```

## API 介面
- 水利署河川資料 API
- 消防署避難所資料 CSV
- 國土測繪行政區界 Shapefile

## 版本組織控管
- Python 3.8+
- GeoPandas 0.13+
- Jupyter Notebook 6.0+

## 技術棧依賴
- 核心套件: geopandas, pandas, folium
- 視覺化: matplotlib, mapclassify
- 環境管理: python-dotenv
- 版本控制: Git
