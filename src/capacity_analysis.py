"""
Week 3 階段 3 - 容量分析模組
負責行政區統計與容量缺口分析
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CapacityAnalyzer:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.outputs_dir = self.project_root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
    
    def load_administrative_boundaries(self):
        """載入行政區界線資料"""
        logger.info("載入行政區界線資料...")
        
        # 嘗試載入真實的行政區界線資料
        admin_boundaries_path = self.data_dir / "鄉鎮市區界線.shp"
        
        if admin_boundaries_path.exists():
            logger.info("載入真實行政區界線資料...")
            admin_boundaries = gpd.read_file(admin_boundaries_path)
            logger.info(f"載入成功: {len(admin_boundaries)} 個行政區")
            logger.info(f"CRS: {admin_boundaries.crs}")
        else:
            logger.info("行政區界線資料不存在，創建模擬資料...")
            admin_boundaries = self.create_mock_admin_boundaries()
        
        return admin_boundaries
    
    def create_mock_admin_boundaries(self):
        """創建模擬行政區界線資料"""
        logger.info("創建模擬行政區界線資料...")
        
        # 載入避難所資料以確定範圍
        shelters = gpd.read_file(self.outputs_dir / "shelters_with_risk.geojson")
        
        # 計算避難所分佈範圍
        bounds = shelters.total_bounds
        
        # 創建 5 個模擬行政區
        admin_areas = []
        admin_names = ['北區', '中區', '南區', '東區', '西區']
        
        for i, name in enumerate(admin_names):
            # 創建簡單的矩形行政區
            x_min = bounds[0] + (bounds[2] - bounds[0]) * (i % 3) / 3
            x_max = bounds[0] + (bounds[2] - bounds[0]) * ((i % 3) + 1) / 3
            y_min = bounds[1] + (bounds[3] - bounds[1]) * (i // 3) / 2
            y_max = bounds[1] + (bounds[3] - bounds[1]) * ((i // 3) + 1) / 2
            
            polygon = Polygon([
                (x_min, y_min), (x_max, y_min), 
                (x_max, y_max), (x_min, y_max)
            ])
            
            admin_areas.append({
                '行政區名稱': name,
                '行政區代碼': f'{i+1:03d}',
                'geometry': polygon,
                '人口數': np.random.randint(50000, 200000),
                '面積平方公里': (x_max - x_min) * (y_max - y_min) / 1000000  # 轉換為平方公里
            })
        
        admin_gdf = gpd.GeoDataFrame(admin_areas, crs='EPSG:3826')
        logger.info(f"創建模擬行政區: {len(admin_gdf)} 個")
        
        # 保存模擬資料
        admin_gdf.to_file(self.data_dir / "admin_boundaries.geojson", driver='GeoJSON')
        
        return admin_gdf
    
    def clean_admin_boundaries(self, admin_boundaries):
        """清理行政區界線資料"""
        logger.info("清理行政區界線資料...")
        
        # 檢查幾何有效性
        invalid_geoms = ~admin_boundaries.geometry.is_valid
        if invalid_geoms.any():
            logger.warning(f"發現 {invalid_geoms.sum()} 個無效幾何，進行修復...")
            admin_boundaries.geometry = admin_boundaries.geometry.buffer(0)
        
        # 檢查重疊
        logger.info("檢查行政區重疊...")
        overlaps = 0
        for i, poly1 in enumerate(admin_boundaries.geometry):
            for j, poly2 in enumerate(admin_boundaries.geometry):
                if i < j and poly1.intersects(poly2):
                    overlaps += 1
        
        if overlaps > 0:
            logger.warning(f"發現 {overlaps} 對重疊行政區")
        else:
            logger.info("行政區無重疊，資料品質良好")
        
        return admin_boundaries
    
    def assign_shelters_to_districts(self, shelters_gdf, admin_boundaries):
        """將避難所分配到行政區"""
        logger.info("將避難所分配到行政區...")
        
        # 確保 CRS 一致
        if shelters_gdf.crs != admin_boundaries.crs:
            logger.info(f"CRS 不匹配，進行轉換...")
            logger.info(f"避難所 CRS: {shelters_gdf.crs}")
            logger.info(f"行政區 CRS: {admin_boundaries.crs}")
            
            shelters_projected = shelters_gdf.to_crs(admin_boundaries.crs)
        else:
            shelters_projected = shelters_gdf.copy()
        
        # 執行空間連接
        shelters_with_district = gpd.sjoin(
            shelters_projected, 
            admin_boundaries, 
            predicate='within', 
            how='left'
        )
        
        # 檢查未分配的避難所
        unassigned = shelters_with_district['行政區名稱'].isna()
        if unassigned.any():
            logger.warning(f"發現 {unassigned.sum()} 個未分配避難所")
            
            # 為未分配的避難所找最近的行政區
            for idx in shelters_with_district[unassigned].index:
                shelter_point = shelters_with_district.loc[idx, 'geometry']
                
                # 計算到各行政區中心的距離
                min_distance = float('inf')
                closest_district = None
                
                for _, district in admin_boundaries.iterrows():
                    district_center = district.geometry.centroid
                    distance = shelter_point.distance(district_center)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_district = district['行政區名稱']
                
                # 分配到最近的行政區
                shelters_with_district.loc[idx, '行政區名稱'] = closest_district
                shelters_with_district.loc[idx, '行政區代碼'] = admin_boundaries[
                    admin_boundaries['行政區名稱'] == closest_district
                ]['行政區代碼'].iloc[0]
        
        logger.info(f"避難所行政區分配完成: {len(shelters_with_district)} 個")
        
        # 統計各區避難所數量
        district_counts = shelters_with_district['行政區名稱'].value_counts()
        logger.info("各區避難所分佈:")
        for district, count in district_counts.items():
            logger.info(f"  {district}: {count} 個")
        
        return shelters_with_district
    
    def integrate_district_data(self, shelters_with_district, admin_boundaries):
        """整合行政區資料"""
        logger.info("整合行政區資料...")
        
        # 為每個行政區計算統計資料
        district_stats = {}
        
        for district_name in admin_boundaries['行政區名稱'].unique():
            district_shelters = shelters_with_district[
                shelters_with_district['行政區名稱'] == district_name
            ]
            
            # 基本統計
            stats = {
                '避難所總數': len(district_shelters),
                '總收容人數': district_shelters['收容人數'].sum() if '收容人數' in district_shelters.columns else 0,
                '平均收容人數': district_shelters['收容人數'].mean() if '收容人數' in district_shelters.columns else 0,
            }
            
            # 風險分級統計
            for risk_level in ['high_risk', 'medium_risk', 'low_risk', 'safe']:
                risk_shelters = district_shelters[
                    district_shelters['risk_level'] == risk_level
                ]
                stats[f'{risk_level}_count'] = len(risk_shelters)
                stats[f'{risk_level}_capacity'] = risk_shelters['收容人數'].sum() if '收容人數' in risk_shelters.columns else 0
            
            # 計算風險比例
            total_shelters = stats['避難所總數']
            if total_shelters > 0:
                stats['high_risk_percentage'] = (stats['high_risk_count'] / total_shelters) * 100
                stats['medium_risk_percentage'] = (stats['medium_risk_count'] / total_shelters) * 100
                stats['low_risk_percentage'] = (stats['low_risk_count'] / total_shelters) * 100
                stats['safe_percentage'] = (stats['safe_count'] / total_shelters) * 100
            else:
                stats['high_risk_percentage'] = 0
                stats['medium_risk_percentage'] = 0
                stats['low_risk_percentage'] = 0
                stats['safe_percentage'] = 0
            
            district_stats[district_name] = stats
        
        return district_stats
    
    def calculate_capacity_needs(self, district_stats, admin_boundaries):
        """計算各行政區的容量需求"""
        logger.info("計算容量需求...")
        
        for district_name, stats in district_stats.items():
            # 基礎假設：高風險區需要完全疏散，中風險區需要 50% 疏散，低風險區需要 20% 疏散
            evacuation_requirements = {
                'high_risk': 1.0,      # 100% 疏散需求
                'medium_risk': 0.5,    # 50% 疏散需求
                'low_risk': 0.2,       # 20% 疏散需求
                'safe': 0.0            # 無疏散需求
            }
            
            # 計算總疏散需求
            total_evacuation_demand = 0
            for risk_level, requirement in evacuation_requirements.items():
                risk_capacity = stats.get(f'{risk_level}_capacity', 0)
                total_evacuation_demand += risk_capacity * requirement
            
            # 計算安全容量 (安全區的避難所)
            safe_capacity = stats.get('safe_capacity', 0)
            
            # 計算容量缺口
            capacity_gap = safe_capacity - total_evacuation_demand
            
            # 更新統計資料
            stats['疏散需求'] = total_evacuation_demand
            stats['安全容量'] = safe_capacity
            stats['容量缺口'] = capacity_gap
            stats['缺口比例'] = (capacity_gap / total_evacuation_demand * 100) if total_evacuation_demand > 0 else 0
            
            # 風險等級評估
            if capacity_gap >= 0:
                stats['風險等級'] = '低風險'
            elif capacity_gap >= -total_evacuation_demand * 0.2:  # 缺口小於 20%
                stats['風險等級'] = '中風險'
            else:
                stats['風險等級'] = '高風險'
            
            logger.info(f"{district_name}: 疏散需求 {total_evacuation_demand:,}, 安全容量 {safe_capacity:,}, 缺口 {capacity_gap:,}")
        
        return district_stats
    
    def analyze_capacity_gaps(self, district_stats):
        """詳細分析容量缺口"""
        logger.info("詳細分析容量缺口...")
        
        # 整體統計
        total_districts = len(district_stats)
        total_demand = sum(stats['疏散需求'] for stats in district_stats.values())
        total_safe_capacity = sum(stats['安全容量'] for stats in district_stats.values())
        total_gap = sum(stats['容量缺口'] for stats in district_stats.values())
        
        logger.info(f"整體容量分析:")
        logger.info(f"  行政區數量: {total_districts}")
        logger.info(f"  總疏散需求: {total_demand:,}")
        logger.info(f"  總安全容量: {total_safe_capacity:,}")
        logger.info(f"  總容量缺口: {total_gap:,}")
        
        if total_demand > 0:
            logger.info(f"  整體缺口比例: {(total_gap / total_demand * 100):.1f}%")
        
        # 風險分佈
        risk_distribution = {'低風險': 0, '中風險': 0, '高風險': 0}
        for stats in district_stats.values():
            risk_distribution[stats['風險等級']] += 1
        
        logger.info(f"行政區風險分佈:")
        for risk_level, count in risk_distribution.items():
            percentage = (count / total_districts) * 100
            logger.info(f"  {risk_level}: {count} 個區 ({percentage:.1f}%)")
        
        # 找出最需要關注的行政區
        high_risk_districts = [
            (name, stats) for name, stats in district_stats.items() 
            if stats['風險等級'] == '高風險'
        ]
        
        high_risk_districts.sort(key=lambda x: x[1]['容量缺口'])
        
        logger.info(f"高風險行政區 (按缺口排序):")
        for i, (name, stats) in enumerate(high_risk_districts[:5], 1):
            logger.info(f"  {i}. {name}: 缺口 {stats['容量缺口']:,} ({stats['缺口比例']:.1f}%)")
        
        return district_stats, {
            'total_districts': total_districts,
            'total_demand': total_demand,
            'total_safe_capacity': total_safe_capacity,
            'total_gap': total_gap,
            'risk_distribution': risk_distribution,
            'high_risk_districts': high_risk_districts
        }
    
    def create_district_risk_map(self, admin_with_stats, project_root):
        """創建行政區風險地圖"""
        logger.info("創建行政區風險地圖...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 風險等級地圖
        risk_colors = {'低風險': 'green', '中風險': 'orange', '高風險': 'red'}
        color_map = {'低風險': 0, '中風險': 1, '高風險': 2}
        
        admin_with_stats['風險等級數值'] = admin_with_stats['風險等級'].map(color_map)
        
        admin_with_stats.plot(
            column='風險等級數值', 
            ax=axes[0, 0], 
            cmap='RdYlGn_r',
            legend=True,
            edgecolor='black',
            linewidth=0.5
        )
        axes[0, 0].set_title('Administrative District Risk Level Distribution', fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('Longitude')
        axes[0, 0].set_ylabel('Latitude')
        
        # 高風險避難所比例地圖
        admin_with_stats.plot(
            column='high_risk_percentage', 
            ax=axes[0, 1], 
            cmap='Reds',
            legend=True,
            edgecolor='black',
            linewidth=0.5
        )
        axes[0, 1].set_title('High Risk Shelter Percentage (%)', fontsize=14, fontweight='bold')
        axes[0, 1].set_xlabel('Longitude')
        axes[0, 1].set_ylabel('Latitude')
        
        # 容量缺口地圖
        admin_with_stats.plot(
            column='容量缺口', 
            ax=axes[1, 0], 
            cmap='RdBu_r',
            legend=True,
            edgecolor='black',
            linewidth=0.5
        )
        axes[1, 0].set_title('Capacity Gap', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('Longitude')
        axes[1, 0].set_ylabel('Latitude')
        
        # 避難所密度地圖
        admin_with_stats['避難所密度'] = admin_with_stats['避難所總數'] / admin_with_stats['面積平方公里']
        admin_with_stats.plot(
            column='避難所密度', 
            ax=axes[1, 1], 
            cmap='Blues',
            legend=True,
            edgecolor='black',
            linewidth=0.5
        )
        axes[1, 1].set_title('Shelter Density (per km²)', fontsize=14, fontweight='bold')
        axes[1, 1].set_xlabel('Longitude')
        axes[1, 1].set_ylabel('Latitude')
        
        plt.tight_layout()
        
        # 保存地圖
        map_path = project_root / "outputs" / "district_risk_analysis.png"
        plt.savefig(map_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"行政區風險地圖已保存: {map_path}")
        return map_path
    
    def create_capacity_charts(self, district_stats, project_root):
        """創建容量統計圖表"""
        logger.info("創建容量統計圖表...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 準備資料
        districts = list(district_stats.keys())
        high_risk_counts = [stats['high_risk_count'] for stats in district_stats.values()]
        medium_risk_counts = [stats['medium_risk_count'] for stats in district_stats.values()]
        low_risk_counts = [stats['low_risk_count'] for stats in district_stats.values()]
        safe_counts = [stats['safe_count'] for stats in district_stats.values()]
        
        capacity_gaps = [stats['容量缺口'] for stats in district_stats.values()]
        evacuation_demands = [stats['疏散需求'] for stats in district_stats.values()]
        
        # 1. 風險避難所分佈堆疊圖
        width = 0.6
        x = np.arange(len(districts))
        
        axes[0, 0].bar(x, high_risk_counts, width, label='High Risk', color='red', alpha=0.7)
        axes[0, 0].bar(x, medium_risk_counts, width, bottom=high_risk_counts, 
                       label='Medium Risk', color='orange', alpha=0.7)
        axes[0, 0].bar(x, low_risk_counts, width, 
                       bottom=np.array(high_risk_counts) + np.array(medium_risk_counts),
                       label='Low Risk', color='yellow', alpha=0.7)
        axes[0, 0].bar(x, safe_counts, width,
                       bottom=np.array(high_risk_counts) + np.array(medium_risk_counts) + np.array(low_risk_counts),
                       label='Safe', color='green', alpha=0.7)
        
        axes[0, 0].set_xlabel('District')
        axes[0, 0].set_ylabel('Number of Shelters')
        axes[0, 0].set_title('Risk Shelter Distribution by District')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(districts, rotation=45)
        axes[0, 0].legend()
        
        # 2. 容量缺口 vs 疏散需求
        axes[0, 1].scatter(evacuation_demands, capacity_gaps, alpha=0.7, s=100)
        axes[0, 1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
        axes[0, 1].set_xlabel('Evacuation Demand')
        axes[0, 1].set_ylabel('Capacity Gap')
        axes[0, 1].set_title('Capacity Gap vs Evacuation Demand')
        
        # 添加行政區標籤
        for i, district in enumerate(districts):
            axes[0, 1].annotate(district, (evacuation_demands[i], capacity_gaps[i]), 
                               xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 3. 風險等級分佈圓餅圖
        risk_levels = {'低風險': 0, '中風險': 0, '高風險': 0}
        for stats in district_stats.values():
            risk_levels[stats['風險等級']] += 1
        
        colors = ['green', 'orange', 'red']
        axes[1, 0].pie(risk_levels.values(), labels=risk_levels.keys(), colors=colors, autopct='%1.1f%%')
        axes[1, 0].set_title('District Risk Level Distribution')
        
        # 4. 容量缺口排名
        sorted_districts = sorted(district_stats.items(), key=lambda x: x[1]['容量缺口'])
        district_names = [item[0] for item in sorted_districts]
        gaps = [item[1]['容量缺口'] for item in sorted_districts]
        
        colors_bar = ['red' if gap < 0 else 'green' for gap in gaps]
        axes[1, 1].barh(district_names, gaps, color=colors_bar, alpha=0.7)
        axes[1, 1].axvline(x=0, color='black', linestyle='-', alpha=0.5)
        axes[1, 1].set_xlabel('Capacity Gap')
        axes[1, 1].set_title('Capacity Gap Ranking by District')
        
        plt.tight_layout()
        
        # 保存圖表
        chart_path = project_root / "outputs" / "capacity_analysis_charts.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"容量分析圖表已保存: {chart_path}")
        return chart_path
    
    def generate_capacity_analysis_report(self, district_stats, overall_stats, project_root):
        """生成容量分析報告"""
        logger.info("生成容量分析報告...")
        
        report_path = project_root / "outputs" / "stage3_capacity_analysis_report.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=== Week 3 Stage 3 District Statistics & Capacity Analysis Report ===\n\n")
            f.write(f"Processing Time: {datetime.now()}\n\n")
            
            f.write("Overall Analysis Summary:\n")
            f.write(f"  Number of Districts: {overall_stats['total_districts']}\n")
            f.write(f"  Total Evacuation Demand: {overall_stats['total_demand']:,} people\n")
            f.write(f"  Total Safe Capacity: {overall_stats['total_safe_capacity']:,} people\n")
            f.write(f"  Total Capacity Gap: {overall_stats['total_gap']:,} people\n")
            
            if overall_stats['total_demand'] > 0:
                f.write(f"  Overall Gap Percentage: {(overall_stats['total_gap'] / overall_stats['total_demand'] * 100):.1f}%\n")
            
            f.write(f"\nDistrict Risk Distribution:\n")
            for risk_level, count in overall_stats['risk_distribution'].items():
                percentage = (count / overall_stats['total_districts']) * 100
                f.write(f"  {risk_level}: {count} districts ({percentage:.1f}%)\n")
            
            f.write(f"\nDetailed District Statistics:\n")
            f.write("-" * 80 + "\n")
            
            for district_name, stats in district_stats.items():
                f.write(f"\n{district_name}:\n")
                f.write(f"  Total Shelters: {stats['避難所總數']}\n")
                f.write(f"  Total Capacity: {stats['總收容人數']:,}\n")
                f.write(f"  High Risk Shelters: {stats['high_risk_count']} ({stats['high_risk_percentage']:.1f}%)\n")
                f.write(f"  Medium Risk Shelters: {stats['medium_risk_count']} ({stats['medium_risk_percentage']:.1f}%)\n")
                f.write(f"  Low Risk Shelters: {stats['low_risk_count']} ({stats['low_risk_percentage']:.1f}%)\n")
                f.write(f"  Safe Shelters: {stats['safe_count']} ({stats['safe_percentage']:.1f}%)\n")
                f.write(f"  Evacuation Demand: {stats['疏散需求']:,} people\n")
                f.write(f"  Safe Capacity: {stats['安全容量']:,} people\n")
                f.write(f"  Capacity Gap: {stats['容量缺口']:,} people\n")
                f.write(f"  Gap Percentage: {stats['缺口比例']:.1f}%\n")
                f.write(f"  Risk Level: {stats['風險等級']}\n")
            
            f.write(f"\nHigh Risk District Priority Recommendations:\n")
            f.write("-" * 80 + "\n")
            
            high_risk_districts = overall_stats['high_risk_districts']
            for i, (name, stats) in enumerate(high_risk_districts[:5], 1):
                f.write(f"{i}. {name}:\n")
                f.write(f"   Capacity Gap: {stats['容量缺口']:,} people\n")
                f.write(f"   Gap Percentage: {stats['缺口比例']:.1f}%\n")
                f.write(f"   Recommendation: Establish temporary shelters or expand existing facilities\n")
            
            f.write(f"\nTechnical Parameters:\n")
            f.write("  Evacuation Demand Calculation: High Risk 100%, Medium Risk 50%, Low Risk 20%\n")
            f.write("  Spatial Assignment: gpd.sjoin(predicate='within')\n")
            f.write("  Capacity Analysis: Safe Capacity vs Evacuation Demand\n")
            f.write("  Risk Assessment: Based on capacity gap percentage\n")
            
            f.write(f"\nFile Paths:\n")
            f.write("  District Statistics: outputs/admin_boundaries_with_stats.geojson\n")
            f.write("  Analysis Results: outputs/stage3_capacity_analysis_report.txt\n")
            f.write("  Risk Map: outputs/district_risk_analysis.png\n")
            f.write("  Statistical Charts: outputs/capacity_analysis_charts.png\n")
        
        logger.info(f"容量分析報告已保存: {report_path}")
        return report_path
    
    def save_stage3_results(self, admin_with_stats, district_stats, project_root):
        """保存階段 3 分析結果"""
        logger.info("保存階段 3 分析結果...")
        
        # 保存行政區統計資料
        admin_with_stats.to_file(
            project_root / "outputs" / "admin_boundaries_with_stats.geojson", 
            driver='GeoJSON'
        )
        
        # 保存統計資料為 CSV
        stats_df = pd.DataFrame.from_dict(district_stats, orient='index')
        stats_df.to_csv(project_root / "outputs" / "district_capacity_stats.csv", 
                        encoding='utf-8')
        
        logger.info("分析結果保存完成")
    
    def execute_stage3(self):
        """執行階段 3"""
        logger.info("="*50)
        logger.info("執行階段 3: 行政區統計與容量分析")
        logger.info("="*50)
        
        # 載入行政區界線
        admin_boundaries = self.load_administrative_boundaries()
        admin_boundaries = self.clean_admin_boundaries(admin_boundaries)
        
        # 載入避難所資料
        shelters = gpd.read_file(self.outputs_dir / "shelters_with_risk.geojson")
        
        # 分配避難所到行政區
        shelters_with_district = self.assign_shelters_to_districts(shelters, admin_boundaries)
        
        # 整合行政區資料
        district_stats = self.integrate_district_data(shelters_with_district, admin_boundaries)
        
        # 計算容量需求
        district_stats = self.calculate_capacity_needs(district_stats, admin_boundaries)
        
        # 分析容量缺口
        district_stats, overall_stats = self.analyze_capacity_gaps(district_stats)
        
        # 準備視覺化資料
        admin_with_stats = admin_boundaries.copy()
        for district_name, stats in district_stats.items():
            mask = admin_with_stats['行政區名稱'] == district_name
            for key, value in stats.items():
                admin_with_stats.loc[mask, key] = value
        
        # 創建地圖和圖表
        self.create_district_risk_map(admin_with_stats, self.project_root)
        self.create_capacity_charts(district_stats, self.project_root)
        
        # 生成報告
        self.generate_capacity_analysis_report(district_stats, overall_stats, self.project_root)
        
        # 保存結果
        self.save_stage3_results(admin_with_stats, district_stats, self.project_root)
        
        logger.info("階段 3 執行完成")
        return True, district_stats, overall_stats

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    analyzer = CapacityAnalyzer(project_root)
    
    success, district_stats, overall_stats = analyzer.execute_stage3()
    
    if success:
        print("[SUCCESS] 階段 3 完成")
        print(f"行政區數量: {overall_stats['total_districts']}")
        print(f"總容量缺口: {overall_stats['total_gap']:,}")
        print(f"高風險行政區: {overall_stats['risk_distribution']['高風險']} 個")
        
        # 顯示各區統計
        print("\n各區容量分析:")
        for district, stats in district_stats.items():
            print(f"{district}: 缺口 {stats['容量缺口']:,} ({stats['缺口比例']:.1f}%) - {stats['風險等級']}")
    else:
        print("[ERROR] 階段 3 失敗")
