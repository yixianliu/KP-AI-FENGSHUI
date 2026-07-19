"""
CSV 导出器
支持按"可选章节"导出：基本信息 / 命局类型 / 四柱八字 / 五行分析 /
十神分析 / 大运流年（含起运）/ 运程总结（事业/财运/健康/感情）/
吉凶批注 / AI 智能分析。调用方已用 filter_export_data
过滤 data，本导出器再按数据键是否存在逐项渲染。
"""
from typing import Dict, Any
from .base_exporter import BaseExporter, has_chapter
import csv

# AI 字段 -> 中文标题（与 PDF/Excel 导出保持一致）
_AI_SECTIONS = [
    ('personality', '性格特质'),
    ('career', '事业财运'),
    ('marriage', '婚姻感情'),
    ('health', '健康注意'),
    ('pattern_analysis', '格局分析'),
    ('wuxing_balance', '五行平衡分析'),
    ('shishen_analysis', '十神分析'),
    ('improvement_plan', '改善方案'),
    ('suggestions', '综合建议'),
]


def _to_str(v: Any) -> str:
    if v is None:
        return ''
    if isinstance(v, (list, tuple)):
        return '、'.join(str(x) for x in v if x)
    return str(v)


class CsvExporter(BaseExporter):
    """CSV 导出器"""

    def export(self, data: Dict[str, Any], file_path: str) -> bool:
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # 基本信息
                if has_chapter(data, 'basic_info'):
                    bi = data.get('basic_info', {})
                    writer.writerow(['基本信息'])
                    writer.writerow(['排盘类型', _to_str(bi.get('pan_type'))])
                    writer.writerow(['公历日期', _to_str(bi.get('solar_date'))])
                    writer.writerow(['农历日期', _to_str(bi.get('lunar_date'))])
                    writer.writerow(['出生时辰', _to_str(bi.get('hour'))])
                    writer.writerow(['出生地点', _to_str(bi.get('location'))])
                    writer.writerow(['性别', _to_str(bi.get('gender'))])
                    writer.writerow([])

                # 命局类型
                if has_chapter(data, 'bazi_types'):
                    bt = data.get('bazi_types', {})
                    writer.writerow(['命局类型'])
                    if bt.get('strength'):
                        writer.writerow(['日主强弱', _to_str(bt.get('strength'))])
                    if bt.get('geju_type'):
                        name = bt.get('geju_name', '')
                        val = bt.get('geju_type') + (f"（{name}）" if name else '')
                        writer.writerow(['格局类型', val])
                        if bt.get('geju_desc'):
                            writer.writerow(['格局说明', _to_str(bt.get('geju_desc'))])
                    if bt.get('wuxing_summary'):
                        writer.writerow(['五行旺衰', _to_str(bt.get('wuxing_summary'))])
                    ys = bt.get('yongshen') or {}
                    if ys.get('yongshen'):
                        writer.writerow(['用神', f"{ys.get('yongshen')}（{ys.get('yongshen_name')}）"])
                        if ys.get('xishen_names'):
                            writer.writerow(['喜神', '、'.join(ys.get('xishen_names'))])
                        if ys.get('jishen_names'):
                            writer.writerow(['忌神', '、'.join(ys.get('jishen_names'))])
                    writer.writerow([])

                # 四柱八字
                if has_chapter(data, 'bazi'):
                    bz = data.get('bazi', {})
                    writer.writerow(['四柱八字'])
                    writer.writerow(['年柱', _to_str(bz.get('year_pillar'))])
                    writer.writerow(['月柱', _to_str(bz.get('month_pillar'))])
                    writer.writerow(['日柱', _to_str(bz.get('day_pillar'))])
                    writer.writerow(['时柱', _to_str(bz.get('hour_pillar'))])
                    writer.writerow([])

                # 五行分析
                if has_chapter(data, 'wuxing'):
                    wx = data.get('wuxing', {})
                    writer.writerow(['五行分析'])
                    for n in ['木', '火', '土', '金', '水']:
                        if n in wx:
                            writer.writerow([f'{n}五行', f'{wx.get(n)}分'])
                    writer.writerow([])

                # 十神分析
                if has_chapter(data, 'shishen'):
                    ss = data.get('shishen', {})
                    writer.writerow(['十神分析'])
                    for name in ['正官', '七杀', '正财', '偏财', '正印', '偏印', '食神', '伤官', '比肩', '劫财']:
                        val = ss.get(name)
                        if val:
                            writer.writerow([name, f'{val}分'])
                    writer.writerow([])

                # 大运流年
                if has_chapter(data, 'yunshi'):
                    dayun = data.get('dayun', {}) or {}
                    liunian = data.get('liunian', {}) or {}
                    periods = dayun.get('periods', []) if isinstance(dayun, dict) else []
                    years = liunian.get('years', []) if isinstance(liunian, dict) else []
                    writer.writerow(['大运流年'])
                    if periods:
                        writer.writerow(['大运方向', _to_str(dayun.get('direction'))])
                        qiyun = dayun.get('qiyun_text')
                        if qiyun:
                            writer.writerow(['起运', _to_str(qiyun)])
                        for p in periods:
                            label = (f"第{p.get('period')}运 {p.get('ganzhi')} "
                                     f"（{p.get('start_age')}-{p.get('end_age')}岁，"
                                     f"{p.get('start_year')}-{p.get('end_year')}年）")
                            writer.writerow([label, _to_str(p.get('analysis'))])
                    for y in years:
                        writer.writerow([f"{y.get('year')}年 {y.get('ganzhi')}", _to_str(y.get('analysis'))])
                    writer.writerow([])

                # 运程总结
                if has_chapter(data, 'yuncheng'):
                    yc = data.get('yuncheng', {}) or {}
                    writer.writerow(['运程总结'])
                    if yc.get('overview'):
                        writer.writerow(['综合', _to_str(yc.get('overview'))])
                    for key, label in (('career', '事业'), ('wealth', '财运'),
                                       ('health', '健康'), ('love', '感情')):
                        if yc.get(key):
                            writer.writerow([label, _to_str(yc.get(key))])
                    tags = yc.get('tags') or []
                    if tags:
                        writer.writerow(['标签', '、'.join(str(t) for t in tags)])
                    writer.writerow([])

                # 神煞
                mingli = data.get('mingli', {}) or {}
                shensha = mingli.get('shensha', [])
                if shensha:
                    writer.writerow(['神煞'])
                    for s in shensha:
                        writer.writerow([_to_str(s.get('name')), _to_str(s.get('description'))])
                    writer.writerow([])

                # 吉凶批注
                analysis = data.get('analysis', []) or []
                if analysis:
                    writer.writerow(['吉凶批注'])
                    for an in analysis:
                        writer.writerow([_to_str(an.get('type')), _to_str(an.get('text'))])
                    writer.writerow([])

                # AI 智能分析
                if has_chapter(data, 'ai_analysis'):
                    ai = data.get('ai_analysis', {}) or {}
                    writer.writerow(['AI 智能深度分析'])
                    for key, title in _AI_SECTIONS:
                        items = ai.get(key, []) or []
                        for it in items:
                            writer.writerow([title, _to_str(it)])
                    writer.writerow([])

            return True
        except Exception as e:
            print(f"CSV 导出失败: {e}")
            return False

    def get_file_extension(self) -> str:
        return '.csv'
