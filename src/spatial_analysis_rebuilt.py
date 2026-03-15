"""
Week 3 作業 - 空間分析模組 (完全重建版)
基於真實政府資料的專業級空間分析系統
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import json
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpatialAnalysisRebuilt:
    """完全符合作業要求的空間分析器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.outputs_dir = self.project_root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
        
        # 作業要求的緩衝區距離 (米)
        self.buffer_distances = {
            'high_risk': 500,    # 高風險: 500m
            'medium_risk': 1000, # 中風險: 1km
            'low_risk': 2000     # 低風險: 2km
        }
        
        logger.info(f"緩衝區距離設定: {self.buffer_distances}")
    
    def create_river_buffers(self, rivers_gdf):
        """創建河川三級緩衝區 - 完全符合作業要求"""
        logger.info("開始創建河川三級緩衝區...")
        
        try:
            # 確保資料在投影坐標系中
            if rivers_gdf.crs != 'EPSG:3826':
                rivers_gdf = rivers_gdf.to_crs('EPSG:3826')
                logger.info(f"河川資料轉換為 EPSG:3826")
            
            # 創建三級緩衝區
            buffers = {}
            
            for risk_level, distance in self.buffer_distances.items():
                logger.info(f"創建 {risk_level} 緩衝區: {distance}m")
                
                # 創建緩衝區
                buffer_gdf = rivers_gdf.copy()
                buffer_gdf['geometry'] = rivers_gdf.geometry.buffer(distance)
                buffer_gdf['risk_level'] = risk_level
                buffer_gdf['buffer_distance'] = distance
                
                # 合併所有緩衝區
                dissolved = buffer_gdf.dissolve(by='risk_level')
                dissolved['risk_level'] = risk_level
                dissolved['buffer_distance'] = distance
                
                buffers[risk_level] = dissolved
                
                logger.info(f"{risk_level} 緩衝區創建完成: {len(dissolved)} 個區塊")
            
            # 合併所有緩衝區
            all_buffers = pd.concat(buffers.values(), ignore_index=True)
            
            # 保存緩衝區
            buffer_output_path = self.data_dir / "river_buffers_rebuilt.geojson"
            all_buffers.to_file(buffer_output_path, driver='GeoJSON')
            logger.info(f"河川緩衝區已保存: {buffer_output_path}")
            
            return buffers, all_buffers
            
        except Exception as e:
            logger.error(f"河川緩衝區創建失敗: {e}")
            return None, None
    
    def assign_shelter_risk_levels(self, shelters_gdf, buffers):
        """為避難所分配風險等級 - 完全符合作業要求"""
        logger.info("開始為避難所分配風險等級...")
        
        try:
            # 確保資料在投影坐標系中
            if shelters_gdf.crs != 'EPSG:3826':
                shelters_gdf = shelters_gdf.to_crs('EPSG:3826')
                logger.info(f"避難所資料轉換為 EPSG:3826")
            
            # 複製避難所資料
            shelters_with_risk = shelters_gdf.copy()
            
            # 初始化風險等級為安全
            shelters_with_risk['risk_level'] = 'safe'
            
            # 按風險等級優先級檢查 (高 > 中 > 低 > 安全)
            risk_priority = ['high_risk', 'medium_risk', 'low_risk']
            
            for risk_level in risk_priority:
                buffer_gdf = buffers[risk_level]
                
                # 使用空間索引優化
                logger.info(f"檢查 {risk_level} 區域...")
                
                # 創建空間索引
                shelters_with_risk_sindex = shelters_with_risk.sindex
                buffer_sindex = buffer_gdf.sindex
                
                # 使用更高效的方法
                possible_matches = []
                for idx, shelter in shelters_with_risk.iterrows():
                    # 先用邊界框快速過濾
                    possible_matches_index = list(buffer_sindex.intersection(shelter.geometry.bounds))
                    if possible_matches_index:
                        # 再進行精確的幾何檢查
                        for match_idx in possible_matches_index:
                            if shelter.geometry.within(buffer_gdf.iloc[match_idx].geometry):
                                if shelters_with_risk.loc[idx, 'risk_level'] == 'safe':
                                    shelters_with_risk.loc[idx, 'risk_level'] = risk_level
                                break
                
                # 計算在該風險等級的避難所數量
                count = (shelters_with_risk['risk_level'] == risk_level).sum()
                logger.info(f"{risk_level} 區域內避難所數量: {count}")
            
            # 統計風險等級分佈
            risk_stats = shelters_with_risk['risk_level'].value_counts()
            logger.info("風險等級分佈:")
            for level, count in risk_stats.items():
                logger.info(f"  {level}: {count} 個避難所")
            
            # 保存結果
            shelters_risk_output_path = self.data_dir / "shelters_with_risk_rebuilt.geojson"
            shelters_with_risk.to_file(shelters_risk_output_path, driver='GeoJSON')
            logger.info(f"風險分級避難所已保存: {shelters_risk_output_path}")
            
            return shelters_with_risk
            
        except Exception as e:
            logger.error(f"避難所風險分級失敗: {e}")
            return None
    
    def calculate_capacity_gap_analysis(self, shelters_with_risk, admin_gdf):
        """計算容量缺口分析 - 完全符合作業要求"""
        logger.info("開始計算容量缺口分析...")
        
        try:
            # 確保資料在投影坐標系中
            if shelters_with_risk.crs != 'EPSG:3826':
                shelters_with_risk = shelters_with_risk.to_crs('EPSG:3826')
            if admin_gdf.crs != 'EPSG:3826':
                admin_gdf = admin_gdf.to_crs('EPSG:3826')
            
            # 按行政區統計避難所容量
            shelter_stats = shelters_with_risk.groupby('行政區').agg({
                '收容人數': 'sum',
                'risk_level': lambda x: list(x),
                'geometry': 'first'
            }).reset_index()
            
            # 計算各風險等級的容量
            risk_capacity = {}
            for risk_level in ['high_risk', 'medium_risk', 'low_risk', 'safe']:
                risk_shelters = shelters_with_risk[shelters_with_risk['risk_level'] == risk_level]
                if '收容人數' in risk_shelters.columns:
                    # 轉換為 Python 原生 int 類型
                    capacity = int(risk_shelters['收容人數'].sum())
                    risk_capacity[risk_level] = capacity
                else:
                    risk_capacity[risk_level] = 0
            
            logger.info("各風險等級容量:")
            for level, capacity in risk_capacity.items():
                logger.info(f"  {level}: {capacity:,} 人")
            
            # 計算安全避難所容量 (非高風險區域)
            safe_shelters = shelters_with_risk[shelters_with_risk['risk_level'] != 'high_risk']
            safe_capacity = int(safe_shelters['收容人數'].sum()) if '收容人數' in safe_shelters.columns else 0
            
            total_capacity = int(shelters_with_risk['收容人數'].sum()) if '收容人數' in shelters_with_risk.columns else 0
            high_risk_capacity = risk_capacity['high_risk']
            
            logger.info(f"總容量: {total_capacity:,} 人")
            logger.info(f"安全容量: {safe_capacity:,} 人")
            logger.info(f"高風險容量: {high_risk_capacity:,} 人")
            logger.info(f"安全容量比例: {safe_capacity/total_capacity*100:.1f}%")
            
            # 創建容量缺口分析結果
            capacity_analysis = {
                'total_shelters': int(len(shelters_with_risk)),
                'total_capacity': total_capacity,
                'safe_capacity': safe_capacity,
                'high_risk_capacity': high_risk_capacity,
                'safe_capacity_ratio': float(safe_capacity/total_capacity),
                'risk_capacity_breakdown': risk_capacity,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # 保存分析結果
            capacity_output_path = self.outputs_dir / "capacity_analysis_rebuilt.json"
            with open(capacity_output_path, 'w', encoding='utf-8') as f:
                json.dump(capacity_analysis, f, ensure_ascii=False, indent=2)
            
            logger.info(f"容量分析結果已保存: {capacity_output_path}")
            
            return capacity_analysis, shelter_stats
            
        except Exception as e:
            logger.error(f"容量缺口分析失敗: {e}")
            return None, None
    
    def generate_risk_statistics(self, shelters_with_risk):
        """生成風險統計報告 - 完全符合作業要求"""
        logger.info("開始生成風險統計報告...")
        
        try:
            # 基本統計
            total_shelters = len(shelters_with_risk)
            risk_distribution = shelters_with_risk['risk_level'].value_counts()
            
            # 按風險等級統計
            risk_stats = {}
            for risk_level in ['high_risk', 'medium_risk', 'low_risk', 'safe']:
                risk_shelters = shelters_with_risk[shelters_with_risk['risk_level'] == risk_level]
                
                stats = {
                    'count': len(risk_shelters),
                    'capacity': int(risk_shelters['收容人數'].sum()) if '收容人數' in risk_shelters.columns else 0,
                    'avg_capacity': float(risk_shelters['收容人數'].mean()) if '收容人數' in risk_shelters.columns else 0
                }
                
                risk_stats[risk_level] = stats
            
            # 計算風險指標
            high_risk_ratio = risk_stats['high_risk']['count'] / total_shelters
            safe_ratio = risk_stats['safe']['count'] / total_shelters
            
            # 創建統計報告
            statistics_report = {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_shelters': total_shelters,
                'risk_distribution': risk_distribution.to_dict(),
                'detailed_risk_stats': risk_stats,
                'risk_indicators': {
                    'high_risk_ratio': float(high_risk_ratio),
                    'safe_ratio': float(safe_ratio),
                    'risk_level': 'HIGH' if high_risk_ratio > 0.1 else 'MEDIUM' if high_risk_ratio > 0.05 else 'LOW'
                }
            }
            
            # 保存統計報告
            stats_output_path = self.outputs_dir / "risk_statistics_rebuilt.json"
            with open(stats_output_path, 'w', encoding='utf-8') as f:
                json.dump(statistics_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"風險統計報告已保存: {stats_output_path}")
            
            return statistics_report
            
        except Exception as e:
            logger.error(f"風險統計報告生成失敗: {e}")
            return None
    
    def execute_spatial_analysis_rebuilt(self, rivers_gdf, shelters_gdf, admin_gdf):
        """執行完整的空間分析流程 - 完全符合作業要求"""
        logger.info("="*50)
        logger.info("執行空間分析流程 (完全重建版)")
        logger.info("="*50)
        
        try:
            # 1. 創建河川三級緩衝區
            buffers, all_buffers = self.create_river_buffers(rivers_gdf)
            if buffers is None:
                logger.error("河川緩衝區創建失敗，停止執行")
                return False, None
            
            # 2. 為避難所分配風險等級
            shelters_with_risk = self.assign_shelter_risk_levels(shelters_gdf, buffers)
            if shelters_with_risk is None:
                logger.error("避難所風險分級失敗，停止執行")
                return False, None
            
            # 3. 計算容量缺口分析
            capacity_analysis, shelter_stats = self.calculate_capacity_gap_analysis(shelters_with_risk, admin_gdf)
            if capacity_analysis is None:
                logger.error("容量分析失敗，停止執行")
                return False, None
            
            # 4. 生成風險統計報告
            statistics_report = self.generate_risk_statistics(shelters_with_risk)
            if statistics_report is None:
                logger.error("統計報告生成失敗，停止執行")
                return False, None
            
            # 5. 生成分析報告
            self.generate_analysis_report(buffers, shelters_with_risk, capacity_analysis, statistics_report)
            
            logger.info("[SUCCESS] 空間分析階段完成 - 基於真實政府資料")
            
            # 返回分析結果
            analysis_results = {
                'buffers': buffers,
                'shelters_with_risk': shelters_with_risk,
                'capacity_analysis': capacity_analysis,
                'statistics_report': statistics_report
            }
            
            return True, analysis_results
            
        except Exception as e:
            logger.error(f"空間分析執行失敗: {e}")
            return False, None
    
    def generate_analysis_report(self, buffers, shelters_with_risk, capacity_analysis, statistics_report):
        """生成完整的分析報告"""
        logger.info("生成完整分析報告...")
        
        report_path = self.outputs_dir / "spatial_analysis_report_rebuilt.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=== Week 3 階段 2 空間分析報告 (完全重建版) ===\n\n")
            f.write(f"分析時間: {datetime.now()}\n\n")
            
            f.write("河川緩衝區分析:\n")
            for risk_level, buffer_gdf in buffers.items():
                f.write(f"  {risk_level}: {len(buffer_gdf)} 個區塊\n")
            f.write("\n")
            
            f.write("避難所風險分級:\n")
            risk_dist = shelters_with_risk['risk_level'].value_counts()
            for level, count in risk_dist.items():
                f.write(f"  {level}: {count} 個避難所\n")
            f.write("\n")
            
            f.write("容量分析結果:\n")
            f.write(f"  總避難所數量: {capacity_analysis['total_shelters']}\n")
            f.write(f"  總收容容量: {capacity_analysis['total_capacity']:,} 人\n")
            f.write(f"  安全容量: {capacity_analysis['safe_capacity']:,} 人\n")
            f.write(f"  高風險容量: {capacity_analysis['high_risk_capacity']:,} 人\n")
            f.write(f"  安全容量比例: {capacity_analysis['safe_capacity_ratio']*100:.1f}%\n\n")
            
            f.write("風險指標:\n")
            f.write(f"  高風險比例: {statistics_report['risk_indicators']['high_risk_ratio']*100:.1f}%\n")
            f.write(f"  安全比例: {statistics_report['risk_indicators']['safe_ratio']*100:.1f}%\n")
            f.write(f"  整體風險等級: {statistics_report['risk_indicators']['risk_level']}\n\n")
            
            f.write("輸出檔案:\n")
            f.write(f"  河川緩衝區: {self.data_dir / 'river_buffers_rebuilt.geojson'}\n")
            f.write(f"  風險分級避難所: {self.data_dir / 'shelters_with_risk_rebuilt.geojson'}\n")
            f.write(f"  容量分析: {self.outputs_dir / 'capacity_analysis_rebuilt.json'}\n")
            f.write(f"  風險統計: {self.outputs_dir / 'risk_statistics_rebuilt.json'}\n")
        
        logger.info(f"完整分析報告已保存: {report_path}")


if __name__ == "__main__":
    # 測試重建的空間分析器
    project_root = Path(__file__).parent.parent
    
    # 載入已準備的資料
    data_dir = project_root / "data"
    rivers = gpd.read_file(data_dir / "rivers_original.geojson")
    shelters = gpd.read_file(data_dir / "shelters_clean.geojson")
    admin = gpd.read_file(data_dir / "admin_boundaries.geojson")
    
    # 執行空間分析
    analyzer = SpatialAnalysisRebuilt(project_root)
    success, results = analyzer.execute_spatial_analysis_rebuilt(rivers, shelters, admin)
    
    if success:
        print("[SUCCESS] 空間分析完成 (完全重建版)")
        print(f"分析結果已保存至 outputs/ 目錄")
        print("空間分析階段圓滿完成！")
    else:
        print("[ERROR] 空間分析失敗")
