"""
Week 3 階段 2 - 空間分析模組
負責多級緩衝區建立與空間連接分析
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpatialAnalyzer:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.outputs_dir = self.project_root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
    
    def load_stage1_data(self):
        """載入階段 1 資料"""
        logger.info("載入階段 1 資料...")
        rivers = gpd.read_file(self.data_dir / "rivers_original.geojson")
        shelters = gpd.read_file(self.data_dir / "shelters_clean.geojson")
        logger.info(f"河川: {len(rivers)}, 避難所: {len(shelters)}")
        return rivers, shelters
    
    def create_multi_level_buffers(self, rivers_gdf):
        """建立三級緩衝區"""
        logger.info("建立多級緩衝區...")
        rivers_sample = rivers_gdf.head(1000)
        
        buffers = {}
        buffers['high_risk'] = gpd.GeoDataFrame(
            geometry=rivers_sample.buffer(500),
            crs=rivers_sample.crs
        )
        buffers['medium_risk'] = gpd.GeoDataFrame(
            geometry=rivers_sample.buffer(1000),
            crs=rivers_sample.crs
        )
        buffers['low_risk'] = gpd.GeoDataFrame(
            geometry=rivers_sample.buffer(2000),
            crs=rivers_sample.crs
        )
        
        for level, buffer_gdf in buffers.items():
            logger.info(f"{level}: {len(buffer_gdf)} 個緩衝區")
        
        return buffers, rivers_sample
    
    def execute_multi_level_sjoin(self, shelters_gdf, buffers):
        """執行多級空間連接"""
        logger.info("執行多級空間連接...")
        risk_results = {}
        
        for risk_level, buffer_gdf in buffers.items():
            at_risk = gpd.sjoin(shelters_gdf, buffer_gdf, predicate='within', how='inner')
            
            # 去重複
            if '避難所名稱' in at_risk.columns:
                at_risk_dedup = at_risk.drop_duplicates(subset=['避難所名稱'], keep='first')
            else:
                at_risk_dedup = at_risk.drop_duplicates(keep='first')
            
            at_risk_dedup['risk_level'] = risk_level
            risk_results[risk_level] = at_risk_dedup
            
            logger.info(f"{risk_level}: {len(at_risk_dedup)} 個避難所")
        
        return risk_results
    
    def assign_risk_levels(self, risk_results, shelters_gdf):
        """分配風險等級"""
        logger.info("分配風險等級...")
        all_shelters = shelters_gdf.copy()
        all_shelters['risk_level'] = 'safe'
        
        risk_priority = ['high_risk', 'medium_risk', 'low_risk']
        for risk_level in risk_priority:
            at_risk_shelters = risk_results[risk_level]
            for idx, shelter in at_risk_shelters.iterrows():
                shelter_idx = all_shelters[
                    all_shelters['避難所名稱'] == shelter['避難所名稱']
                ].index
                if len(shelter_idx) > 0:
                    all_shelters.loc[shelter_idx[0], 'risk_level'] = risk_level
        
        return all_shelters
    
    def analyze_risk_statistics(self, risk_results, all_shelters):
        """風險統計分析"""
        logger.info("風險統計分析...")
        total_shelters = len(all_shelters)
        risk_stats = {}
        
        for risk_level, at_risk_shelters in risk_results.items():
            stats = {
                'count': len(at_risk_shelters),
                'percentage': len(at_risk_shelters) / total_shelters * 100
            }
            if '收容人數' in at_risk_shelters.columns:
                stats['total_capacity'] = at_risk_shelters['收容人數'].sum()
            risk_stats[risk_level] = stats
        
        return risk_stats
    
    def save_results(self, buffers, risk_results, all_shelters):
        """保存結果"""
        logger.info("保存結果...")
        
        # 保存緩衝區
        buffers_dir = self.outputs_dir / "buffers"
        buffers_dir.mkdir(exist_ok=True)
        
        for risk_level, buffer_gdf in buffers.items():
            buffer_gdf['risk_level'] = risk_level
            buffer_gdf.to_file(buffers_dir / f"buffer_{risk_level}.geojson", driver='GeoJSON')
        
        # 保存風險分析結果
        all_shelters.to_file(self.outputs_dir / "shelters_with_risk.geojson", driver='GeoJSON')
        
        logger.info("結果保存完成")
    
    def create_basic_map(self, all_shelters):
        """創建基本地圖"""
        logger.info("創建基本地圖...")
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        colors = {'high_risk': 'red', 'medium_risk': 'orange', 'low_risk': 'yellow', 'safe': 'green'}
        
        for risk_level, color in colors.items():
            level_shelters = all_shelters[all_shelters['risk_level'] == risk_level]
            if len(level_shelters) > 0:
                level_shelters.plot(ax=ax, color=color, markersize=15, alpha=0.7, label=risk_level)
        
        ax.set_title('多級風險緩衝區分析')
        ax.legend()
        plt.savefig(self.outputs_dir / "multi_level_risk_map.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("地圖保存完成")
    
    def execute_stage2(self):
        """執行階段 2"""
        logger.info("="*50)
        logger.info("執行階段 2: 多級緩衝區與空間連接")
        logger.info("="*50)
        
        # 載入資料
        rivers, shelters = self.load_stage1_data()
        
        # 建立緩衝區
        buffers, rivers_sample = self.create_multi_level_buffers(rivers)
        
        # 空間連接
        risk_results = self.execute_multi_level_sjoin(shelters, buffers)
        
        # 分配風險等級
        all_shelters = self.assign_risk_levels(risk_results, shelters)
        
        # 統計分析
        risk_stats = self.analyze_risk_statistics(risk_results, all_shelters)
        
        # 保存結果
        self.save_results(buffers, risk_results, all_shelters)
        
        # 創建地圖
        self.create_basic_map(all_shelters)
        
        logger.info("階段 2 執行完成")
        return True, risk_results, all_shelters, risk_stats

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    analyzer = SpatialAnalyzer(project_root)
    
    success, risk_results, all_shelters, risk_stats = analyzer.execute_stage2()
    
    if success:
        print("[SUCCESS] 階段 2 完成")
        for level, stats in risk_stats.items():
            print(f"{level}: {stats['count']} 個避難所")
    else:
        print("[ERROR] 階段 2 失敗")
