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
    # 与 core.analysis_storage._JSON_SCHEMAS 对齐（三种类型的并集，仅保留列表型字段；
    # final_verdict / disclaimer 为段落型，由各自面板/导出分支单独处理）。
    ('personality', '性格特质'),
    ('career', '事业财运'),
    ('relationships', '婚姻感情'),
    ('health', '健康注意'),
    ('four_pillars_detail', '四柱详细解读'),
    ('analysis', '卦象/课体分析'),
    ('hexagram_interpretations', '卦爻解释'),
    ('timing', '应期时机'),
    ('scenario_advice', '场景化建议'),
    ('advice', '行动建议'),
    ('historical_cases', '历史案例'),
    ('probability_stats', '概率统计'),
]


def _to_str(v: Any) -> str:
    """把任意排盘字段值统一转换为可写入 CSV 单元格的字符串。

    排盘结果中同一字段可能是 None（未计算）、列表（如喜神/忌神多个值）
    或标量，直接交给 csv.writer 会写出 "None" 或 "['甲', '乙']" 这类
    脏数据，因此在写入前统一归一化。

    Args:
        v: 任意排盘字段值，可为 None、list/tuple 或标量

    Returns:
        str，None 归一为空字符串；list/tuple 用顿号连接（并过滤空元素）；
        其余类型直接 str() 转换
    """
    if v is None:
        # CSV 中空值留白，避免出现字面量 "None"
        return ''
    if isinstance(v, (list, tuple)):
        # 过滤掉 None / 空串等假值，防止出现 "甲、、乙" 这种连续分隔符
        return '、'.join(str(x) for x in v if x)
    return str(v)


class CsvExporter(BaseExporter):
    """CSV 导出器"""

    def export(self, data: Dict[str, Any], file_path: str) -> bool:
        """把排盘结果按章节顺序逐行写入 CSV 文件。

        实现 BaseExporter.export 契约。整份 CSV 采用「章节标题行 + 键值行 +
        空行分隔」的扁平结构（而非固定表头的二维表），因为各章节字段数量
        和含义完全不同，无法共用同一套列定义。
        调用方通常已用 filter_export_data 过滤过 data，这里再用 has_chapter
        做一次存在性判断，保证缺数据的章节不会输出空标题。

        Args:
            data: 排盘结果字典，可能包含 basic_info / bazi_types / bazi /
                wuxing / shishen / dayun / liunian / yuncheng / mingli /
                analysis / ai_analysis / meihua_data / meihua_ai /
                liuren_data / liuren_ai / zonghe 等键
            file_path: 目标 CSV 文件路径

        Returns:
            bool，写入成功返回 True；任何异常（路径不可写、编码失败等）
            被捕获后打印错误并返回 False，不向上抛出
        """
        try:
            # newline='' 由 csv 模块自行控制换行符，否则 Windows 上每行会多出空行；
            # utf-8-sig 写入 BOM，使 Excel 直接双击打开时不会把中文识别成乱码
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
                    # 大运/流年是同一虚拟章节的两个数据键；上游偶尔会传入
                    # 列表或字符串形式的旧结构，故先做 isinstance 兜底再取子键
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
                # 神煞属于 filter_export_data 中始终保留的旧字段，不在 CHAPTERS
                # 章节清单里，因此这里不走 has_chapter 而是直接判断列表是否为空
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
                    writer.writerow(['龙虎山大师兄分析预测'])
                    for key, title in _AI_SECTIONS:
                        items = ai.get(key, []) or []
                        if isinstance(items, str):
                            items = [items] if items.strip() else []
                        for it in items:
                            writer.writerow([title, _to_str(it)])
                    writer.writerow([])

                # 梅花易数卦象
                if has_chapter(data, 'meihua'):
                    mh = data.get('meihua_data', {}) or {}
                    writer.writerow(['梅花易数'])
                    for key, label in (
                        ('method', '起卦方法'),
                        ('base_hex', '本卦'),
                        ('changed_hex', '变卦'),
                        ('hu_hex', '互卦'),
                        ('ti_gong', '体卦'),
                        ('yong_gong', '用卦'),
                        ('ti_zhi', '体卦五行'),
                        ('yong_zhi', '用卦五行'),
                        ('hu_gong', '互卦五行'),
                        ('bian_gong', '变卦五行'),
                        ('hex_relation', '体用关系'),
                    ):
                        val = mh.get(key)
                        if val:
                            writer.writerow([label, _to_str(val)])
                    # 嵌入式 AI 解读（独立键）
                    mh_ai = data.get('meihua_ai') or {}
                    if mh_ai:
                        writer.writerow([])
                        writer.writerow(['— 龙虎山大师兄梅花解读 —'])
                        for key, title in _AI_SECTIONS:
                            items = mh_ai.get(key, []) or []
                            if isinstance(items, str):
                                items = [items] if items.strip() else []
                            for it in items:
                                writer.writerow([title, _to_str(it)])
                        if mh_ai.get('final_verdict'):
                            writer.writerow(['结论', _to_str(mh_ai.get('final_verdict'))])
                    writer.writerow([])

                # 大六壬起课
                if has_chapter(data, 'liuren'):
                    lr = data.get('liuren_data', {}) or {}
                    writer.writerow(['大六壬起课'])
                    for key, label in (
                        ('pan_date', '公历日期'),
                        ('si_ke', '四课'),
                        ('san_chuan', '三传'),
                        ('gate', '三传门法'),
                        ('yue_jiang', '月将'),
                        ('tian_jiang', '天将'),
                        ('shen_sha', '神煞'),
                    ):
                        val = lr.get(key)
                        if val:
                            writer.writerow([label, _to_str(val)])
                    # 嵌入式 AI 解读
                    lr_ai = data.get('liuren_ai') or {}
                    if lr_ai:
                        writer.writerow([])
                        writer.writerow(['— 龙虎山大师兄六壬解读 —'])
                        for key, title in _AI_SECTIONS:
                            items = lr_ai.get(key, []) or []
                            if isinstance(items, str):
                                items = [items] if items.strip() else []
                            for it in items:
                                writer.writerow([title, _to_str(it)])
                        if lr_ai.get('final_verdict'):
                            writer.writerow(['结论', _to_str(lr_ai.get('final_verdict'))])
                    writer.writerow([])

                # 综合建议（融合三方结论）
                if has_chapter(data, 'zonghe'):
                    z = data.get('zonghe', {}) or {}
                    writer.writerow(['综合建议（大师兄融合）'])
                    _ZONGHE_SECTIONS = [
                        ('tri_method_overview', '三方概览'),
                        ('consistency_check', '矛盾与印证'),
                        ('synthesis', '综合定论'),
                        ('unified_plan', '统一趋吉避凶方案'),
                        ('key_timing', '关键时机与禁忌'),
                    ]
                    for key, title in _ZONGHE_SECTIONS:
                        for it in (z.get(key) or []):
                            writer.writerow([title, _to_str(it)])
                    if z.get('disclaimer'):
                        writer.writerow(['免责说明', _to_str(z.get('disclaimer'))])
                    writer.writerow([])

            return True
        except Exception as e:
            # 导出属于用户主动触发的非关键路径，失败时不应让界面崩溃，
            # 统一吞掉异常并以返回值告知调用方
            print(f"CSV 导出失败: {e}")
            return False

    def get_file_extension(self) -> str:
        """返回本导出器对应的文件扩展名。

        实现 BaseExporter.get_file_extension 契约，供上层拼接默认文件名
        和文件对话框过滤器使用。

        Returns:
            str，固定为 '.csv'
        """
        return '.csv'
