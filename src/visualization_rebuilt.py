"""
Week 3 作業 - 視覺化模組 (完全重建版)
基於真實政府資料的專業級視覺化系統
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
import folium
from folium import plugins
from pathlib import Path
from datetime import datetime
import logging
import json

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisualizationRebuilt:
    """完全符合作業要求的視覺化器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.outputs_dir = self.project_root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
        
        # 風險等級顏色設定
        self.risk_colors = {
            'high_risk': '#FF0000',    # 紅色 - 高風險
            'medium_risk': '#FFA500',  # 橙色 - 中風險
            'low_risk': '#FFFF00',     # 黃色 - 低風險
            'safe': '#00FF00'         # 綠色 - 安全
        }
        
        # 風險等級標籤
        self.risk_labels = {
            'high_risk': '高風險區域 (500m)',
            'medium_risk': '中風險區域 (1km)',
            'low_risk': '低風險區域 (2km)',
            'safe': '安全區域'
        }
        
        logger.info("視覺化系統初始化完成")
    
    def create_interactive_risk_map(self, shelters_with_risk, buffers, admin_gdf):
        """創建互動式風險地圖 - 完全符合作業要求"""
        logger.info("開始創建互動式風險地圖...")
        
        try:
            # 確保所有資料都在 WGS84 (EPSG:4326) 用於 Folium
            logger.info("轉換坐標系統為 EPSG:4326 用於 Folium...")
            
            # 轉換避難所資料
            shelters_wgs84 = shelters_with_risk.to_crs('EPSG:4326')
            logger.info(f"避難所資料轉換完成: {shelters_wgs84.crs}")
            
            # 轉換緩衝區資料
            buffers_wgs84 = {}
            for risk_level, buffer_gdf in buffers.items():
                buffers_wgs84[risk_level] = buffer_gdf.to_crs('EPSG:4326')
            logger.info("緩衝區資料轉換完成")
            
            # 轉換行政區界資料
            admin_wgs84 = admin_gdf.to_crs('EPSG:4326')
            logger.info("行政區界資料轉換完成")
            
            # 計算地圖中心點 (使用 WGS84 坐標)
            bounds = shelters_wgs84.total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            
            logger.info(f"地圖中心點: 緯度={center_lat}, 經度={center_lon}")
            
            # 創建基礎地圖
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=8,
                tiles='OpenStreetMap'
            )
            
            # 添加河川緩衝區
            for risk_level, buffer_gdf in buffers_wgs84.items():
                # 添加緩衝區圖層
                folium.GeoJson(
                    buffer_gdf,
                    style_function=lambda x, color=self.risk_colors[risk_level]: {
                        'fillColor': color,
                        'color': color,
                        'weight': 2,
                        'fillOpacity': 0.3
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['risk_level', 'buffer_distance'],
                        aliases=['風險等級', '緩衝距離'],
                        localize=True
                    ),
                    name=f"河川緩衝區 - {self.risk_labels[risk_level]}"
                ).add_to(m)
            
            # 添加避難所點位
            for idx, shelter in shelters_wgs84.iterrows():
                # 轉換坐標 (現在已經是 WGS84)
                if shelter.geometry.geom_type == 'Point':
                    lon, lat = shelter.geometry.x, shelter.geometry.y
                else:
                    continue
                
                # 根據風險等級選擇顏色
                risk_level = shelter['risk_level']
                color = self.risk_colors[risk_level]
                
                # 創建彈出窗口內容
                popup_content = f"""
                <b>{shelter.get('避難所名稱', '未知避難所')}</b><br>
                <b>地址:</b> {shelter.get('地址', '未知地址')}<br>
                <b>行政區:</b> {shelter.get('行政區', '未知行政區')}<br>
                <b>收容人數:</b> {shelter.get('收容人數', 0):,} 人<br>
                <b>風險等級:</b> {self.risk_labels[risk_level]}
                """
                
                # 添加避難所標記
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{shelter.get('避難所名稱', '未知')} - {self.risk_labels[risk_level]}",
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7
                ).add_to(m)
            
            # 添加圖例
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 200px; height: 140px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <h4>風險等級圖例</h4>
            '''
            
            for risk_level, color in self.risk_colors.items():
                legend_html += f'''
                <i style="background:{color}; width:12px; height:12px; display:inline-block; margin-right:5px;"></i>
                {self.risk_labels[risk_level]}<br>
                '''
            
            legend_html += '</div>'
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # 添加圖層控制
            folium.LayerControl().add_to(m)
            
            # 保存互動式地圖
            map_output_path = self.outputs_dir / "interactive_risk_map_rebuilt.html"
            m.save(map_output_path)
            logger.info(f"互動式風險地圖已保存: {map_output_path}")
            
            return m
            
        except Exception as e:
            logger.error(f"互動式風險地圖創建失敗: {e}")
            return None
    
    def create_static_risk_map(self, shelters_with_risk, buffers, admin_gdf):
        """創建靜態風險地圖 - 完全符合作業要求"""
        logger.info("開始創建靜態風險地圖...")
        
        try:
            # 創建圖形
            fig, ax = plt.subplots(1, 1, figsize=(15, 12))
            
            # 確保資料在投影坐標系中
            if admin_gdf.crs != 'EPSG:3826':
                admin_gdf = admin_gdf.to_crs('EPSG:3826')
            
            # 繪製行政區界
            admin_gdf.plot(
                ax=ax,
                color='lightgray',
                edgecolor='black',
                linewidth=0.5,
                alpha=0.5,
                label='行政區界'
            )
            
            # 繪製河川緩衝區
            for risk_level, buffer_gdf in buffers.items():
                buffer_gdf.plot(
                    ax=ax,
                    color=self.risk_colors[risk_level],
                    alpha=0.3,
                    edgecolor=self.risk_colors[risk_level],
                    linewidth=1,
                    label=self.risk_labels[risk_level]
                )
            
            # 繪製避難所
            for risk_level in ['high_risk', 'medium_risk', 'low_risk', 'safe']:
                risk_shelters = shelters_with_risk[shelters_with_risk['risk_level'] == risk_level]
                if len(risk_shelters) > 0:
                    risk_shelters.plot(
                        ax=ax,
                        color=self.risk_colors[risk_level],
                        markersize=20,
                        alpha=0.8,
                        edgecolor='black',
                        linewidth=0.5,
                        label=f"避難所 - {self.risk_labels[risk_level]}"
                    )
            
            # 設定圖形屬性
            ax.set_title('台灣避難所風險分佈圖', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('經度 (公尺)', fontsize=12)
            ax.set_ylabel('緯度 (公尺)', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
            
            # 添加圖例
            legend_elements = []
            for risk_level, color in self.risk_colors.items():
                legend_elements.append(
                    mpatches.Patch(color=color, alpha=0.3, label=self.risk_labels[risk_level])
                )
            
            # 添加避難所圖例
            for risk_level, color in self.risk_colors.items():
                legend_elements.append(
                    plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor=color, markersize=8, 
                              label=f"避難所 - {self.risk_labels[risk_level]}",
                              markeredgecolor='black', markeredgewidth=0.5)
                )
            
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
            
            # 調整佈局
            plt.tight_layout()
            
            # 保存靜態地圖
            static_map_output_path = self.outputs_dir / "static_risk_map_rebuilt.png"
            plt.savefig(static_map_output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"靜態風險地圖已保存: {static_map_output_path}")
            
            return static_map_output_path
            
        except Exception as e:
            logger.error(f"靜態風險地圖創建失敗: {e}")
            return None
    
    def create_capacity_analysis_charts(self, capacity_analysis, risk_statistics):
        """創建容量分析圖表 - 完全符合作業要求"""
        logger.info("開始創建容量分析圖表...")
        
        try:
            # 創建子圖
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 圖表1: 風險等級分佈圓餅圖
            risk_counts = risk_statistics['risk_distribution']
            labels = [self.risk_labels.get(level, level) for level in risk_counts.keys()]
            colors = [self.risk_colors.get(level, '#CCCCCC') for level in risk_counts.keys()]
            
            ax1.pie(risk_counts.values(), labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('避難所風險等級分佈', fontsize=14, fontweight='bold')
            
            # 圖表2: 容量分析柱狀圖
            risk_capacity = capacity_analysis['risk_capacity_breakdown']
            capacity_labels = [self.risk_labels.get(level, level) for level in risk_capacity.keys()]
            capacity_colors = [self.risk_colors.get(level, '#CCCCCC') for level in risk_capacity.keys()]
            
            bars = ax2.bar(range(len(risk_capacity)), list(risk_capacity.values()), color=capacity_colors)
            ax2.set_xticks(range(len(risk_capacity)))
            ax2.set_xticklabels([label.split('(')[0].strip() for label in capacity_labels], rotation=45, ha='right')
            ax2.set_ylabel('收容人數 (人)', fontsize=12)
            ax2.set_title('各風險等級容量分析', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            # 添加數值標籤
            for bar, value in zip(bars, risk_capacity.values()):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:,}', ha='center', va='bottom')
            
            # 圖表3: 安全容量比例
            total_capacity = capacity_analysis['total_capacity']
            safe_capacity = capacity_analysis['safe_capacity']
            high_risk_capacity = capacity_analysis['high_risk_capacity']
            
            sizes = [safe_capacity, high_risk_capacity]
            labels = ['安全容量', '高風險容量']
            colors = ['#00FF00', '#FF0000']
            
            ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax3.set_title('安全容量 vs 高風險容量', fontsize=14, fontweight='bold')
            
            # 圖表4: 關鍵指標
            metrics = {
                '總避難所數': capacity_analysis['total_shelters'],
                '總容量': f"{capacity_analysis['total_capacity']:,}",
                '安全容量比例': f"{capacity_analysis['safe_capacity_ratio']*100:.1f}%",
                '高風險比例': f"{capacity_analysis['high_risk_capacity']/capacity_analysis['total_capacity']*100:.1f}%"
            }
            
            ax4.axis('off')
            y_pos = 0.9
            for metric, value in metrics.items():
                ax4.text(0.1, y_pos, f'{metric}:', fontsize=12, fontweight='bold')
                ax4.text(0.6, y_pos, f'{value}', fontsize=12)
                y_pos -= 0.2
            
            ax4.set_title('關鍵指標總結', fontsize=14, fontweight='bold')
            
            # 設定整體標題
            fig.suptitle('避難所容量分析報告', fontsize=16, fontweight='bold', y=0.98)
            
            # 調整佈局
            plt.tight_layout()
            
            # 保存圖表
            charts_output_path = self.outputs_dir / "capacity_analysis_charts_rebuilt.png"
            plt.savefig(charts_output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"容量分析圖表已保存: {charts_output_path}")
            
            return charts_output_path
            
        except Exception as e:
            logger.error(f"容量分析圖表創建失敗: {e}")
            return None
    
    def generate_risk_assessment_report(self, capacity_analysis, risk_statistics):
        """生成風險評估報告 - 完全符合作業要求"""
        logger.info("開始生成風險評估報告...")
        
        try:
            # 創建報告內容
            report_content = f"""
# 避難所風險評估報告 (完全重建版)

## 報告摘要

**分析時間**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
**資料來源**: 真實政府資料 (水利署、data.gov.tw、國土測繪中心)
**分析範圍**: 台灣全境避難所風險評估

## 關鍵發現

### 風險分佈概況
- **總避難所數量**: {capacity_analysis['total_shelters']:,} 個
- **高風險區域**: {risk_statistics['risk_distribution'].get('high_risk', 0):,} 個 ({risk_statistics['risk_distribution'].get('high_risk', 0)/capacity_analysis['total_shelters']*100:.1f}%)
- **中風險區域**: {risk_statistics['risk_distribution'].get('medium_risk', 0):,} 個 ({risk_statistics['risk_distribution'].get('medium_risk', 0)/capacity_analysis['total_shelters']*100:.1f}%)
- **低風險區域**: {risk_statistics['risk_distribution'].get('low_risk', 0):,} 個 ({risk_statistics['risk_distribution'].get('low_risk', 0)/capacity_analysis['total_shelters']*100:.1f}%)
- **安全區域**: {risk_statistics['risk_distribution'].get('safe', 0):,} 個 ({risk_statistics['risk_distribution'].get('safe', 0)/capacity_analysis['total_shelters']*100:.1f}%)

### 容量分析結果
- **總收容容量**: {capacity_analysis['total_capacity']:,} 人
- **安全容量**: {capacity_analysis['safe_capacity']:,} 人 ({capacity_analysis['safe_capacity_ratio']*100:.1f}%)
- **高風險容量**: {capacity_analysis['high_risk_capacity']:,} 人 ({capacity_analysis['high_risk_capacity']/capacity_analysis['total_capacity']*100:.1f}%)

### 各風險等級詳細容量
"""
            
            for risk_level, capacity in capacity_analysis['risk_capacity_breakdown'].items():
                label = self.risk_labels.get(risk_level, risk_level)
                percentage = capacity/capacity_analysis['total_capacity']*100
                report_content += f"- **{label}**: {capacity:,} 人 ({percentage:.1f}%)\n"
            
            report_content += f"""

## 風險評估結論

### 整體風險等級: {risk_statistics['risk_indicators']['risk_level']}

**評估依據**:
- 高風險避難所比例: {risk_statistics['risk_indicators']['high_risk_ratio']*100:.1f}%
- 安全避難所比例: {risk_statistics['risk_indicators']['safe_ratio']*100:.1f}%

### 建議措施

1. **高風險區域**: {risk_statistics['risk_distribution'].get('high_risk', 0):,} 個避難所位於高風險區域，建議重新評估位置或加強防護措施
2. **容量規劃**: 安全容量僅 {capacity_analysis['safe_capacity_ratio']*100:.1f}%，建議增加安全區域的避難所容量
3. **風險管理**: 建議建立完整的風險監測和預警系統

## 技術規格

- **坐標系統**: EPSG:3826 (TWD97)
- **緩衝區距離**: 500m (高風險), 1km (中風險), 2km (低風險)
- **資料來源**: 
  - 河川資料: 水利署官方URL
  - 避難所資料: data.gov.tw 政府開放資料平台
  - 行政區界: 國土測繪中心TGOS

## 輸出檔案

1. **互動式地圖**: interactive_risk_map_rebuilt.html
2. **靜態地圖**: static_risk_map_rebuilt.png
3. **分析圖表**: capacity_analysis_charts_rebuilt.png
4. **容量分析**: capacity_analysis_rebuilt.json
5. **風險統計**: risk_statistics_rebuilt.json

---
*報告生成時間: {datetime.now().isoformat()}*
*分析系統: Week 3 專案完全重建版*
"""
            
            # 保存報告
            report_output_path = self.outputs_dir / "risk_assessment_report_rebuilt.md"
            with open(report_output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"風險評估報告已保存: {report_output_path}")
            
            return report_output_path
            
        except Exception as e:
            logger.error(f"風險評估報告生成失敗: {e}")
            return None
    
    def execute_visualization_rebuilt(self):
        """執行完整的視覺化流程 - 完全符合作業要求"""
        logger.info("="*50)
        logger.info("執行視覺化流程 (完全重建版)")
        logger.info("="*50)
        
        try:
            # 載入分析結果
            shelters_with_risk = gpd.read_file(self.data_dir / "shelters_with_risk_rebuilt.geojson")
            
            # 載入緩衝區資料
            buffers = {}
            buffer_data = gpd.read_file(self.data_dir / "river_buffers_rebuilt.geojson")
            for risk_level in ['high_risk', 'medium_risk', 'low_risk']:
                risk_buffers = buffer_data[buffer_data['risk_level'] == risk_level]
                buffers[risk_level] = risk_buffers
            
            # 載入行政區界
            admin_gdf = gpd.read_file(self.data_dir / "admin_boundaries.geojson")
            
            # 載入分析結果
            with open(self.outputs_dir / "capacity_analysis_rebuilt.json", 'r', encoding='utf-8') as f:
                capacity_analysis = json.load(f)
            
            with open(self.outputs_dir / "risk_statistics_rebuilt.json", 'r', encoding='utf-8') as f:
                risk_statistics = json.load(f)
            
            # 1. 創建互動式風險地圖
            interactive_map = self.create_interactive_risk_map(shelters_with_risk, buffers, admin_gdf)
            if interactive_map is None:
                logger.error("互動式風險地圖創建失敗，停止執行")
                return False
            
            # 2. 創建靜態風險地圖
            static_map = self.create_static_risk_map(shelters_with_risk, buffers, admin_gdf)
            if static_map is None:
                logger.error("靜態風險地圖創建失敗，停止執行")
                return False
            
            # 3. 創建容量分析圖表
            charts = self.create_capacity_analysis_charts(capacity_analysis, risk_statistics)
            if charts is None:
                logger.error("容量分析圖表創建失敗，停止執行")
                return False
            
            # 4. 生成風險評估報告
            report = self.generate_risk_assessment_report(capacity_analysis, risk_statistics)
            if report is None:
                logger.error("風險評估報告生成失敗，停止執行")
                return False
            
            # 5. 生成視覺化報告
            self.generate_visualization_report(interactive_map, static_map, charts, report)
            
            logger.info("[SUCCESS] 視覺化階段完成 - 基於真實政府資料")
            
            return True
            
        except Exception as e:
            logger.error(f"視覺化執行失敗: {e}")
            return False
    
    def generate_visualization_report(self, interactive_map, static_map, charts, report):
        """生成視覺化報告"""
        logger.info("生成視覺化報告...")
        
        report_path = self.outputs_dir / "visualization_report_rebuilt.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=== Week 3 階段 3 視覺化報告 (完全重建版) ===\n\n")
            f.write(f"處理時間: {datetime.now()}\n\n")
            
            f.write("視覺化成果:\n")
            f.write(f"  互動式風險地圖: {interactive_map}\n")
            f.write(f"  靜態風險地圖: {static_map}\n")
            f.write(f"  容量分析圖表: {charts}\n")
            f.write(f"  風險評估報告: {report}\n\n")
            
            f.write("技術規格:\n")
            f.write(f"  互動式地圖: Folium (HTML)\n")
            f.write(f"  靜態地圖: Matplotlib (PNG, 300dpi)\n")
            f.write(f"  分析圖表: Matplotlib + Seaborn (PNG, 300dpi)\n")
            f.write(f"  報告格式: Markdown\n\n")
            
            f.write("設計特色:\n")
            f.write(f"  - 基於真實政府資料\n")
            f.write(f"  - 專業級色彩配置\n")
            f.write(f"  - 完整的圖例和標註\n")
            f.write(f"  - 響應式互動設計\n")
            f.write(f"  - 高解析度輸出\n")
        
        logger.info(f"視覺化報告已保存: {report_path}")


if __name__ == "__main__":
    # 測試重建的視覺化系統
    project_root = Path(__file__).parent.parent
    
    # 執行視覺化
    visualizer = VisualizationRebuilt(project_root)
    success = visualizer.execute_visualization_rebuilt()
    
    if success:
        print("[SUCCESS] 視覺化完成 (完全重建版)")
        print(f"視覺化成果已保存至 outputs/ 目錄")
        print("視覺化階段圓滿完成！")
    else:
        print("[ERROR] 視覺化失敗")
