"""
Week 3 作業 - 資料載入模組
負責下載和載入各種資料來源
"""

import geopandas as gpd
import pandas as pd
import requests
import os
from pathlib import Path
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLoader:
    """資料載入器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.data_dir.mkdir(exist_ok=True)
        
    def download_river_data(self):
        """下載水利署河川資料"""
        logger.info("開始下載水利署河川資料...")
        
        try:
            # 直接讀取水利署 URL
            rivers = gpd.read_file(
                'https://gic.wra.gov.tw/Gis/gic/API/Google/DownLoad.aspx?fname=RIVERPOLY&filetype=SHP'
            )
            
            logger.info(f"河川資料下載成功: {len(rivers)} 筆")
            logger.info(f"CRS: {rivers.crs}")
            logger.info(f"幾何類型: {rivers.geom_type.unique()}")
            
            # 保存原始資料
            output_path = self.data_dir / "rivers_original.geojson"
            rivers.to_file(output_path, driver='GeoJSON')
            logger.info(f"河川資料已保存: {output_path}")
            
            return rivers
            
        except Exception as e:
            logger.error(f"河川資料下載失敗: {e}")
            return None
    
    def load_shelter_data(self):
        """載入消防署避難所資料"""
        logger.info("開始載入消防署避難所資料...")
        
        # 檢查檔案是否存在
        shelter_csv_path = self.data_dir / "避難收容處所.csv"
        
        if not shelter_csv_path.exists():
            logger.warning("避難所資料檔案不存在，請手動下載")
            logger.info("下載連結: https://data.gov.tw/dataset/73242")
            logger.info("請下載後放置於 data/避難收容處所.csv")
            return None
        
        try:
            # 嘗試 UTF-8 編碼
            shelters_df = pd.read_csv(shelter_csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            # 嘗試 Big5 編碼
            shelters_df = pd.read_csv(shelter_csv_path, encoding='big5')
        
        logger.info(f"避難所資料載入成功: {len(shelters_df)} 筆")
        logger.info(f"欄位: {list(shelters_df.columns)}")
        
        return shelters_df
    
    def clean_shelter_data(self, shelters_df):
        """清理避難所資料"""
        logger.info("開始清理避難所資料...")
        
        # 記錄原始統計
        original_count = len(shelters_df)
        logger.info(f"原始資料筆數: {original_count}")
        
        # 1. 移除重複記錄
        shelters_clean = shelters_df.drop_duplicates()
        duplicates_removed = original_count - len(shelters_clean)
        logger.info(f"移除重複記錄: {duplicates_removed}")
        
        # 2. 檢查必要欄位
        required_columns = ['經度', '緯度', '收容人數']
        missing_columns = [col for col in required_columns if col not in shelters_clean.columns]
        
        if missing_columns:
            logger.error(f"缺少必要欄位: {missing_columns}")
            return None
        
        # 3. 坐標範圍檢查
        before_coord_check = len(shelters_clean)
        
        shelters_clean = shelters_clean[
            (shelters_clean['經度'] >= 119) & 
            (shelters_clean['經度'] <= 122) &
            (shelters_clean['緯度'] >= 21) & 
            (shelters_clean['緯度'] <= 26)
        ]
        
        coord_removed = before_coord_check - len(shelters_clean)
        logger.info(f"移除坐標異常: {coord_removed}")
        
        # 4. 移除空值
        before_null_check = len(shelters_clean)
        shelters_clean = shelters_clean.dropna(subset=['經度', '緯度', '收容人數'])
        null_removed = before_null_check - len(shelters_clean)
        logger.info(f"移除空值: {null_removed}")
        
        # 5. 檢查經緯度是否反置
        swapped_count = 0
        for idx, row in shelters_clean.iterrows():
            lon, lat = row['經度'], row['緯度']
            
            # 如果經度在緯度範圍內，緯度在經度範圍內，可能反置
            if 21 <= lon <= 26 and 119 <= lat <= 122:
                swapped_count += 1
                shelters_clean.loc[idx, '經度'] = lat
                shelters_clean.loc[idx, '緯度'] = lon
        
        logger.info(f"修正經緯度反置: {swapped_count}")
        
        # 6. 創建 GeoDataFrame
        shelters_gdf = gpd.GeoDataFrame(
            shelters_clean,
            geometry=gpd.points_from_xy(shelters_clean['經度'], shelters_clean['緯度']),
            crs='EPSG:4326'
        )
        
        # 7. 幾何圖形有效性檢查
        invalid_geoms = ~shelters_gdf.geometry.is_valid
        if invalid_geoms.any():
            logger.warning(f"發現無效幾何圖形: {invalid_geoms.sum()}")
            shelters_gdf = shelters_gdf[shelters_gdf.geometry.is_valid]
        
        # 統計最終結果
        final_count = len(shelters_gdf)
        total_removed = original_count - final_count
        
        logger.info(f"清理完成統計:")
        logger.info(f"  原始筆數: {original_count}")
        logger.info(f"  最終筆數: {final_count}")
        logger.info(f"  移除總數: {total_removed} ({total_removed/original_count*100:.1f}%)")
        logger.info(f"  CRS: {shelters_gdf.crs}")
        
        # 保存清理後資料
        output_path = self.data_dir / "shelters_clean.geojson"
        shelters_gdf.to_file(output_path, driver='GeoJSON')
        logger.info(f"清理後資料已保存: {output_path}")
        
        return shelters_gdf
    
    def check_and_align_crs(self, rivers_gdf, shelters_gdf):
        """檢查並對齊坐標系統"""
        logger.info("開始 CRS 檢查與對齊...")
        
        logger.info(f"河川資料 CRS: {rivers_gdf.crs}")
        logger.info(f"避難所資料 CRS: {shelters_gdf.crs}")
        
        # 檢查是否需要轉換
        if rivers_gdf.crs != shelters_gdf.crs:
            logger.info("檢測到 CRS 不匹配，需要轉換")
            
            # 將避難所轉換為河川的 CRS
            shelters_projected = shelters_gdf.to_crs(rivers_gdf.crs)
            logger.info(f"避難所已轉換為: {shelters_projected.crs}")
            
            return rivers_gdf, shelters_projected
        else:
            logger.info("CRS 已經對齊，無需轉換")
            return rivers_gdf, shelters_gdf
    
    def validate_spatial_extent(self, rivers_gdf, shelters_gdf):
        """驗證空間範圍合理性"""
        logger.info("驗證空間範圍...")
        
        # 計算空間範圍
        rivers_bounds = rivers_gdf.total_bounds
        shelters_bounds = shelters_gdf.total_bounds
        
        logger.info(f"河川範圍: X[{rivers_bounds[0]:.2f}, {rivers_bounds[2]:.2f}], "
                  f"Y[{rivers_bounds[1]:.2f}, {rivers_bounds[3]:.2f}]")
        logger.info(f"避難所範圍: X[{shelters_bounds[0]:.2f}, {shelters_bounds[2]:.2f}], "
                  f"Y[{shelters_bounds[1]:.2f}, {shelters_bounds[3]:.2f}]")
        
        # 檢查是否有重疊
        x_overlap = not (rivers_bounds[2] < shelters_bounds[0] or 
                       rivers_bounds[0] > shelters_bounds[2])
        y_overlap = not (rivers_bounds[3] < shelters_bounds[1] or 
                       rivers_bounds[1] > shelters_bounds[3])
        
        if x_overlap and y_overlap:
            logger.info("✓ 空間範圍有重疊，適合進行空間分析")
            return True
        else:
            logger.warning("✗ 空間範圍無重疊，需要檢查資料")
            return False
    
    def execute_data_preparation(self):
        """執行完整的資料準備流程"""
        logger.info("="*50)
        logger.info("執行資料準備流程")
        logger.info("="*50)
        
        # 1. 下載河川資料
        rivers_gdf = self.download_river_data()
        if rivers_gdf is None:
            logger.error("河川資料下載失敗，停止執行")
            return False
        
        # 2. 載入避難所資料
        shelters_df = self.load_shelter_data()
        if shelters_df is None:
            logger.error("避難所資料載入失敗，停止執行")
            return False
        
        # 3. 清理避難所資料
        shelters_gdf = self.clean_shelter_data(shelters_df)
        if shelters_gdf is None:
            logger.error("避難所資料清理失敗，停止執行")
            return False
        
        # 4. CRS 檢查與對齊
        rivers_aligned, shelters_aligned = self.check_and_align_crs(rivers_gdf, shelters_gdf)
        
        # 5. 空間範圍驗證
        spatial_valid = self.validate_spatial_extent(rivers_aligned, shelters_aligned)
        
        if spatial_valid:
            logger.info("✓ 資料準備階段完成")
            return True, rivers_aligned, shelters_aligned
        else:
            logger.error("✗ 空間範圍驗證失敗")
            return False, None, None


if __name__ == "__main__":
    # 測試資料載入器
    project_root = Path(__file__).parent.parent
    loader = DataLoader(project_root)
    
    success, rivers, shelters = loader.execute_data_preparation()
    
    if success:
        print("✓ 資料準備完成")
        print(f"河川資料: {len(rivers)} 筆")
        print(f"避難所資料: {len(shelters)} 筆")
    else:
        print("✗ 資料準備失敗")
