"""
图表可视化生成器
生成五行分布饼图、十神分布图、大运走势图等
"""
import matplotlib
matplotlib.use('QtAgg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.patches import FancyBboxPatch
import os


# 中文字体配置
def setup_chinese_font():
    """配置中文字体"""
    font_candidates = [
        'Microsoft YaHei',
        'SimHei',
        'SimSun',
        'KaiTi',
        'FangSong',
        'Arial Unicode MS',
        'PingFang SC',
        'Noto Sans CJK SC',
        'WenQuanYi Micro Hei'
    ]
    
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    for font in font_candidates:
        if font in available_fonts:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            return font
    
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    return None


# 五行配色
WUXING_COLORS = {
    '木': '#2E8B57',
    '火': '#DC143C',
    '土': '#DAA520',
    '金': '#C0C0C0',
    '水': '#4169E1'
}

# 十神配色
SHISHEN_COLORS = {
    '比肩': '#5B9BD5',
    '劫财': '#ED7D31',
    '食神': '#70AD47',
    '伤官': '#FFC000',
    '正财': '#4472C4',
    '偏财': '#7030A0',
    '正官': '#264478',
    '七杀': '#9E480E',
    '正印': '#63A94C',
    '偏印': '#AE3838'
}

# 背景色
BACKGROUND_COLOR = '#FAF8F5'
CARD_COLOR = '#FFFFFF'
TEXT_COLOR = '#2D2D2D'
SECONDARY_TEXT_COLOR = '#666666'


class ChartGenerator:
    """图表生成器"""

    def __init__(self):
        self.font = setup_chinese_font()
        self._setup_style()

    def _setup_style(self):
        """设置图表样式"""
        plt.rcParams['figure.facecolor'] = BACKGROUND_COLOR
        plt.rcParams['axes.facecolor'] = CARD_COLOR
        plt.rcParams['text.color'] = TEXT_COLOR
        plt.rcParams['axes.labelcolor'] = TEXT_COLOR
        plt.rcParams['xtick.color'] = SECONDARY_TEXT_COLOR
        plt.rcParams['ytick.color'] = SECONDARY_TEXT_COLOR
        plt.rcParams['axes.edgecolor'] = '#E0E0E0'
        plt.rcParams['grid.color'] = '#F0F0F0'
        plt.rcParams['grid.linestyle'] = '--'
        plt.rcParams['grid.alpha'] = 0.7

    # ==================== 五行分布饼图 ====================

    def create_wuxing_pie_chart(self, wuxing_result, title='五行分布', 
                                 figsize=(6, 5), save_path=None):
        """
        生成五行分布饼图
        
        Args:
            wuxing_result: 五行分析结果字典
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径（可选）
            
        Returns:
            matplotlib figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        ax.set_facecolor(CARD_COLOR)
        
        wuxing_names = ['木', '火', '土', '金', '水']
        values = []
        colors = []
        labels = []
        
        for name in wuxing_names:
            wx_data = wuxing_result.get(name, {})
            count = wx_data.get('count', 0)
            percentage = wx_data.get('percentage', 0)
            if count > 0:
                values.append(count)
                colors.append(WUXING_COLORS.get(name, '#999999'))
                labels.append(f'{name}\n{percentage:.1f}%')
        
        if not values:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
                    fontsize=14, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return fig
        
        # 绘制饼图
        wedges, texts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            startangle=90,
            counterclock=False,
            labeldistance=1.15,
            wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2),
            textprops=dict(fontsize=10, color=TEXT_COLOR, ha='center')
        )
        
        # 中心圆（环形图效果）
        centre_circle = plt.Circle((0, 0), 0.35, fc=CARD_COLOR, ec='none')
        ax.add_artist(centre_circle)
        
        # 中心文字
        total = sum(values)
        ax.text(0, 0.08, f'{total:.1f}', ha='center', va='center', 
                fontsize=18, fontweight='bold', color=TEXT_COLOR)
        ax.text(0, -0.12, '五行总数', ha='center', va='center', 
                fontsize=9, color=SECONDARY_TEXT_COLOR)
        
        # 标题
        ax.set_title(title, fontsize=14, fontweight='bold', 
                     color=TEXT_COLOR, pad=15)
        
        ax.axis('equal')
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                        facecolor=BACKGROUND_COLOR)
        
        return fig

    # ==================== 十神分布柱状图 ====================

    def create_shishen_bar_chart(self, shishen_result, title='十神分布',
                                  figsize=(8, 5), save_path=None):
        """
        生成十神分布柱状图
        
        Args:
            shishen_result: 十神分析结果字典
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径（可选）
            
        Returns:
            matplotlib figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        ax.set_facecolor(CARD_COLOR)
        
        summary = shishen_result.get('summary', {})
        shishen_order = ['比肩', '劫财', '食神', '伤官', '正财', 
                         '偏财', '正官', '七杀', '正印', '偏印']
        
        names = []
        values = []
        colors = []
        
        for name in shishen_order:
            count = summary.get(name, 0)
            names.append(name)
            values.append(count)
            colors.append(SHISHEN_COLORS.get(name, '#999999'))
        
        if not any(values):
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                    fontsize=14, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return fig
        
        # 绘制柱状图
        bars = ax.bar(names, values, color=colors, width=0.6,
                      edgecolor='white', linewidth=1.5, zorder=3)
        
        # 在柱子上方显示数值
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                        f'{val}', ha='center', va='bottom',
                        fontsize=10, fontweight='bold', color=TEXT_COLOR)
        
        # 样式设置
        ax.set_title(title, fontsize=14, fontweight='bold',
                     color=TEXT_COLOR, pad=15)
        ax.set_ylabel('数量', fontsize=11, color=SECONDARY_TEXT_COLOR)
        ax.tick_params(axis='x', rotation=0, labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1)
        ax.grid(axis='y', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=BACKGROUND_COLOR)
        
        return fig

    # ==================== 十神雷达图 ====================

    def create_shishen_radar_chart(self, shishen_result, title='十神能量分布',
                                    figsize=(6, 6), save_path=None):
        """
        生成十神分布雷达图
        
        Args:
            shishen_result: 十神分析结果字典
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径（可选）
            
        Returns:
            matplotlib figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        ax.set_facecolor(CARD_COLOR)
        
        summary = shishen_result.get('summary', {})
        shishen_order = ['比肩', '劫财', '食神', '伤官', '正财',
                         '偏财', '正官', '七杀', '正印', '偏印']
        
        names = []
        values = []
        colors = []
        
        for name in shishen_order:
            count = summary.get(name, 0)
            names.append(name)
            values.append(count)
            colors.append(SHISHEN_COLORS.get(name, '#999999'))
        
        if not any(values):
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                    fontsize=14, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return fig
        
        # 角度计算
        angles = np.linspace(0, 2 * np.pi, len(names), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        
        # 绘制雷达图
        ax.fill(angles, values, color=WUXING_COLORS.get('土', '#DAA520'), 
                alpha=0.25, zorder=2)
        ax.plot(angles, values, color=WUXING_COLORS.get('土', '#DAA520'), 
                linewidth=2, zorder=3)
        
        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(names, fontsize=10, color=TEXT_COLOR)
        
        # 设置网格
        ax.set_yticklabels([])
        ax.grid(color='#E0E0E0', linestyle='--', alpha=0.7)
        ax.spines['polar'].set_color('#E0E0E0')
        
        # 标题
        ax.set_title(title, fontsize=14, fontweight='bold',
                     color=TEXT_COLOR, pad=20)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=BACKGROUND_COLOR)
        
        return fig

    # ==================== 大运走势图 ====================

    def create_dayun_line_chart(self, major_fortune, title='大运走势',
                                 figsize=(10, 5), save_path=None):
        """
        生成大运走势折线图
        
        Args:
            major_fortune: 大运数据字典
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径（可选）
            
        Returns:
            matplotlib figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        ax.set_facecolor(CARD_COLOR)
        
        periods = major_fortune.get('periods', [])
        
        if not periods:
            ax.text(0.5, 0.5, '暂无大运数据', ha='center', va='center',
                    fontsize=14, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return fig
        
        ages = []
        ganzhi_list = []
        scores = []
        
        for period in periods:
            start_age = period.get('start_age', 0)
            end_age = period.get('end_age', 0)
            mid_age = (start_age + end_age) // 2
            ages.append(mid_age)
            ganzhi_list.append(period.get('ganzhi', ''))
            
            # 简单评分（根据描述关键词）
            desc = (period.get('description', '') + 
                   period.get('analysis', '')).lower()
            score = 5
            good_keywords = ['吉', '好', '顺', '发', '旺', '喜', '利', '成', '得']
            bad_keywords = ['凶', '差', '逆', '破', '衰', '忌', '不利', '失']
            
            good_count = sum(1 for kw in good_keywords if kw in desc)
            bad_count = sum(1 for kw in bad_keywords if kw in desc)
            score += good_count * 0.8 - bad_count * 0.8
            score = max(1, min(10, score))
            scores.append(score)
        
        # 绘制折线图
        ax.plot(ages, scores, marker='o', linewidth=2.5, markersize=8,
                color=WUXING_COLORS.get('火', '#DC143C'),
                markerfacecolor='white', markeredgewidth=2,
                markeredgecolor=WUXING_COLORS.get('火', '#DC143C'),
                zorder=3)
        
        # 填充区域
        ax.fill_between(ages, scores, alpha=0.15,
                       color=WUXING_COLORS.get('火', '#DC143C'), zorder=2)
        
        # 在点上方标注干支
        for age, score, ganzhi in zip(ages, scores, ganzhi_list):
            ax.text(age, score + 0.3, ganzhi, ha='center', va='bottom',
                    fontsize=9, color=TEXT_COLOR, fontweight='bold')
        
        # 标注年龄段
        for i, period in enumerate(periods):
            start_age = period.get('start_age', 0)
            end_age = period.get('end_age', 0)
            mid_age = ages[i]
            ax.text(mid_age, 0.5, f'{start_age}-{end_age}岁', 
                    ha='center', va='top', fontsize=8, 
                    color=SECONDARY_TEXT_COLOR)
        
        # 样式设置
        ax.set_title(title, fontsize=14, fontweight='bold',
                     color=TEXT_COLOR, pad=15)
        ax.set_xlabel('年龄（岁）', fontsize=11, color=SECONDARY_TEXT_COLOR)
        ax.set_ylabel('运势指数', fontsize=11, color=SECONDARY_TEXT_COLOR)
        ax.set_ylim(0, 11)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['低迷', '偏弱', '平稳', '偏旺', '鼎盛'], fontsize=9)
        ax.grid(axis='y', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=BACKGROUND_COLOR)
        
        return fig

    # ==================== 十二长生分布柱状图 ====================

    def create_shier_changsheng_chart(self, shier_changsheng_data, title='十二长生分布',
                                        figsize=(8, 5), save_path=None):
        """
        生成十二长生分布柱状图
        
        Args:
            shier_changsheng_data: 十二长生数据字典 {柱位: {name, ...}}
            title: 图表标题
            figsize: 图表尺寸
            save_path: 保存路径（可选）
            
        Returns:
            matplotlib figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        ax.set_facecolor(CARD_COLOR)
        
        pillar_order = ['年柱', '月柱', '日柱', '时柱']
        changsheng_levels = {
            '长生': 9, '沐浴': 7, '冠带': 8, '临官': 10, '帝旺': 10,
            '衰': 6, '病': 4, '死': 2, '墓': 5, '绝': 1, '胎': 3, '养': 5
        }
        
        names = []
        values = []
        colors_list = []
        
        for pillar in pillar_order:
            info = shier_changsheng_data.get(pillar, {})
            name = info.get('name', '')
            level = changsheng_levels.get(name, 5)
            names.append(f'{pillar}\n{name}')
            values.append(level)
            
            if level >= 9:
                colors_list.append(WUXING_COLORS['火'])
            elif level >= 7:
                colors_list.append(WUXING_COLORS['土'])
            elif level >= 5:
                colors_list.append(WUXING_COLORS['金'])
            else:
                colors_list.append(WUXING_COLORS['水'])
        
        # 绘制柱状图
        bars = ax.bar(names, values, color=colors_list, width=0.5,
                      edgecolor='white', linewidth=1.5, zorder=3)
        
        # 在柱子上方显示长生名称
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    f'{val}', ha='center', va='bottom',
                    fontsize=11, fontweight='bold', color=TEXT_COLOR)
        
        # 样式设置
        ax.set_title(title, fontsize=14, fontweight='bold',
                     color=TEXT_COLOR, pad=15)
        ax.set_ylabel('旺衰指数', fontsize=11, color=SECONDARY_TEXT_COLOR)
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        ax.set_ylim(0, 12)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['绝', '病', '衰', '冠带', '旺'], fontsize=9)
        ax.grid(axis='y', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=BACKGROUND_COLOR)
        
        return fig

    # ==================== 综合仪表盘 ====================

    def create_dashboard(self, wuxing_result=None, shishen_result=None,
                         major_fortune=None, shier_changsheng=None,
                         save_path=None):
        """
        生成综合仪表盘
        
        Args:
            wuxing_result: 五行分析结果
            shishen_result: 十神分析结果
            major_fortune: 大运数据
            shier_changsheng: 十二长生数据
            save_path: 保存路径（可选）
            
        Returns:
            matplotlib figure 对象
        """
        fig = plt.figure(figsize=(14, 10))
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        fig.suptitle('命理综合分析仪表盘', fontsize=16, fontweight='bold',
                     color=TEXT_COLOR, y=0.98)
        
        # 子图布局: 2行3列
        gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)
        
        # 1. 五行分布饼图 (左上)
        if wuxing_result:
            ax1 = fig.add_subplot(gs[0, 0])
            self._plot_wuxing_pie_to_axes(ax1, wuxing_result, '五行分布')
        
        # 2. 十神柱状图 (上中)
        if shishen_result:
            ax2 = fig.add_subplot(gs[0, 1])
            self._plot_shishen_bar_to_axes(ax2, shishen_result, '十神分布')
        
        # 3. 十二长生 (右上)
        if shier_changsheng:
            ax3 = fig.add_subplot(gs[0, 2])
            self._plot_changsheng_to_axes(ax3, shier_changsheng, '十二长生')
        
        # 4. 大运走势 (下排跨两列)
        if major_fortune:
            ax4 = fig.add_subplot(gs[1, 0:2])
            self._plot_dayun_line_to_axes(ax4, major_fortune, '大运走势')
        
        # 5. 十神雷达图 (右下)
        if shishen_result:
            ax5 = fig.add_subplot(gs[1, 2], polar=True)
            self._plot_shishen_radar_to_axes(ax5, shishen_result, '十神能量')
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=BACKGROUND_COLOR)
        
        return fig

    # ==================== 子图绘制辅助方法 ====================

    def _plot_wuxing_pie_to_axes(self, ax, wuxing_result, title):
        """在指定axes上绘制五行饼图"""
        ax.set_facecolor(CARD_COLOR)
        
        wuxing_names = ['木', '火', '土', '金', '水']
        values = []
        colors = []
        labels = []
        
        for name in wuxing_names:
            wx_data = wuxing_result.get(name, {})
            count = wx_data.get('count', 0)
            percentage = wx_data.get('percentage', 0)
            if count > 0:
                values.append(count)
                colors.append(WUXING_COLORS.get(name, '#999999'))
                labels.append(f'{name} {percentage:.0f}%')
        
        if not values:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                    fontsize=12, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return
        
        wedges, texts = ax.pie(
            values, labels=labels, colors=colors, startangle=90,
            counterclock=False, labeldistance=1.1,
            wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2),
            textprops=dict(fontsize=9, color=TEXT_COLOR)
        )
        
        centre_circle = plt.Circle((0, 0), 0.4, fc=CARD_COLOR, ec='none')
        ax.add_artist(centre_circle)
        total = sum(values)
        ax.text(0, 0.05, f'{total:.1f}', ha='center', va='center',
                fontsize=14, fontweight='bold', color=TEXT_COLOR)
        ax.text(0, -0.15, '总量', ha='center', va='center',
                fontsize=8, color=SECONDARY_TEXT_COLOR)
        
        ax.set_title(title, fontsize=12, fontweight='bold',
                     color=TEXT_COLOR, pad=10)
        ax.axis('equal')

    def _plot_shishen_bar_to_axes(self, ax, shishen_result, title):
        """在指定axes上绘制十神柱状图"""
        ax.set_facecolor(CARD_COLOR)
        
        summary = shishen_result.get('summary', {})
        shishen_order = ['比肩', '劫财', '食神', '伤官', '正财',
                         '偏财', '正官', '七杀', '正印', '偏印']
        
        names = []
        values = []
        colors = []
        
        for name in shishen_order:
            count = summary.get(name, 0)
            names.append(name)
            values.append(count)
            colors.append(SHISHEN_COLORS.get(name, '#999999'))
        
        if not any(values):
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                    fontsize=12, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return
        
        bars = ax.bar(names, values, color=colors, width=0.6,
                      edgecolor='white', linewidth=1, zorder=3)
        
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                        f'{val}', ha='center', va='bottom',
                        fontsize=9, color=TEXT_COLOR)
        
        ax.set_title(title, fontsize=12, fontweight='bold',
                     color=TEXT_COLOR, pad=10)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.tick_params(axis='y', labelsize=9)
        ax.set_ylim(0, max(values) * 1.25 if max(values) > 0 else 1)
        ax.grid(axis='y', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    def _plot_changsheng_to_axes(self, ax, shier_changsheng_data, title):
        """在指定axes上绘制十二长生图"""
        ax.set_facecolor(CARD_COLOR)
        
        pillar_order = ['年柱', '月柱', '日柱', '时柱']
        changsheng_levels = {
            '长生': 9, '沐浴': 7, '冠带': 8, '临官': 10, '帝旺': 10,
            '衰': 6, '病': 4, '死': 2, '墓': 5, '绝': 1, '胎': 3, '养': 5
        }
        
        names = []
        values = []
        colors_list = []
        
        for pillar in pillar_order:
            info = shier_changsheng_data.get(pillar, {})
            name = info.get('name', '')
            level = changsheng_levels.get(name, 5)
            names.append(f'{pillar}\n{name}')
            values.append(level)
            
            if level >= 9:
                colors_list.append(WUXING_COLORS['火'])
            elif level >= 7:
                colors_list.append(WUXING_COLORS['土'])
            elif level >= 5:
                colors_list.append(WUXING_COLORS['金'])
            else:
                colors_list.append(WUXING_COLORS['水'])
        
        bars = ax.bar(names, values, color=colors_list, width=0.5,
                      edgecolor='white', linewidth=1, zorder=3)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    f'{val}', ha='center', va='bottom',
                    fontsize=9, color=TEXT_COLOR)
        
        ax.set_title(title, fontsize=12, fontweight='bold',
                     color=TEXT_COLOR, pad=10)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.set_ylim(0, 12)
        ax.set_yticks([2, 5, 8, 10])
        ax.grid(axis='y', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    def _plot_dayun_line_to_axes(self, ax, major_fortune, title):
        """在指定axes上绘制大运折线图"""
        ax.set_facecolor(CARD_COLOR)
        
        periods = major_fortune.get('periods', [])
        
        if not periods:
            ax.text(0.5, 0.5, '暂无大运数据', ha='center', va='center',
                    fontsize=12, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return
        
        ages = []
        ganzhi_list = []
        scores = []
        
        for period in periods:
            start_age = period.get('start_age', 0)
            end_age = period.get('end_age', 0)
            mid_age = (start_age + end_age) // 2
            ages.append(mid_age)
            ganzhi_list.append(period.get('ganzhi', ''))
            
            desc = (period.get('description', '') + 
                   period.get('analysis', ''))
            score = 5
            good_keywords = ['吉', '好', '顺', '发', '旺', '喜', '利', '成', '得']
            bad_keywords = ['凶', '差', '逆', '破', '衰', '忌', '不利', '失']
            
            good_count = sum(1 for kw in good_keywords if kw in desc)
            bad_count = sum(1 for kw in bad_keywords if kw in desc)
            score += good_count * 0.8 - bad_count * 0.8
            score = max(1, min(10, score))
            scores.append(score)
        
        ax.plot(ages, scores, marker='o', linewidth=2, markersize=6,
                color=WUXING_COLORS.get('火', '#DC143C'),
                markerfacecolor='white', markeredgewidth=1.5,
                markeredgecolor=WUXING_COLORS.get('火', '#DC143C'),
                zorder=3)
        ax.fill_between(ages, scores, alpha=0.15,
                       color=WUXING_COLORS.get('火', '#DC143C'), zorder=2)
        
        for age, score, ganzhi in zip(ages, scores, ganzhi_list):
            ax.text(age, score + 0.3, ganzhi, ha='center', va='bottom',
                    fontsize=8, color=TEXT_COLOR)
        
        ax.set_title(title, fontsize=12, fontweight='bold',
                     color=TEXT_COLOR, pad=10)
        ax.set_xlabel('年龄（岁）', fontsize=9, color=SECONDARY_TEXT_COLOR)
        ax.set_ylabel('运势指数', fontsize=9, color=SECONDARY_TEXT_COLOR)
        ax.set_ylim(0, 11)
        ax.set_yticks([2, 5, 8, 10])
        ax.set_yticklabels(['低', '中', '高', '旺'], fontsize=8)
        ax.grid(axis='y', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    def _plot_shishen_radar_to_axes(self, ax, shishen_result, title):
        """在指定axes上绘制十神雷达图"""
        ax.set_facecolor(CARD_COLOR)
        
        summary = shishen_result.get('summary', {})
        shishen_order = ['比肩', '劫财', '食神', '伤官', '正财',
                         '偏财', '正官', '七杀', '正印', '偏印']
        
        names = []
        values = []
        
        for name in shishen_order:
            count = summary.get(name, 0)
            names.append(name)
            values.append(count)
        
        if not any(values):
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                    fontsize=12, color=SECONDARY_TEXT_COLOR)
            ax.set_axis_off()
            return
        
        max_val = max(values) if max(values) > 0 else 1
        values_norm = [v / max_val * 10 for v in values]
        
        angles = np.linspace(0, 2 * np.pi, len(names), endpoint=False).tolist()
        values_norm += values_norm[:1]
        angles += angles[:1]
        
        ax.fill(angles, values_norm, color=WUXING_COLORS.get('土', '#DAA520'),
                alpha=0.25, zorder=2)
        ax.plot(angles, values_norm, color=WUXING_COLORS.get('土', '#DAA520'),
                linewidth=1.5, zorder=3)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(names, fontsize=8, color=TEXT_COLOR)
        ax.set_yticklabels([])
        ax.grid(color='#E0E0E0', linestyle='--', alpha=0.5)
        ax.spines['polar'].set_color('#E0E0E0')
        
        ax.set_title(title, fontsize=12, fontweight='bold',
                     color=TEXT_COLOR, pad=15)


def close_figure(fig):
    """关闭图表，释放资源"""
    plt.close(fig)