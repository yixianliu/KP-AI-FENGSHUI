"""
运程总结模块 - 根据八字排盘结果自动生成综合运程分析

覆盖维度：事业 / 财运 / 健康 / 感情
规则引擎：从已算出的结构化信号（十神权重、五行旺衰、用神喜忌、格局）
推导；可选经 AI 润色为流畅文案（analyze_with_ai）。

设计原则：
- 完全离线可跑（规则引擎），不依赖任何外部接口；
- 文案紧扣真实算出的信号（用神/十神/五行），而非泛泛套话；
- 与既有 bazi_types / shishen / wuxing 数据结构解耦，缺失字段自动降级。
"""
from typing import Dict, Any, List, Optional

# 五行 -> 身体脏腑（健康推断）
_WX_BODY = {
    '木': '肝胆、筋骨、神经系统',
    '火': '心脑、血脉、小肠',
    '土': '脾胃、肌肤、中焦',
    '金': '肺系、呼吸道、大肠',
    '水': '肾系、膀胱、泌尿生殖',
}


class YunChengAnalyzer:
    """运程总结分析器"""

    def analyze(self, bazi, wuxing, shishen, bazi_types, geju=None) -> Dict[str, Any]:
        """生成事业/财运/健康/感情综合运程分析（规则引擎，离线可跑）。

        Args:
            bazi:       排盘结果（含 四柱 / rizhu）
            wuxing:     WuXingAnalyzer.analyze 结果（含 rizhu_wx / summary）
            shishen:    ShiShenAnalyzer.analyze 结果（含 total_weights）
            bazi_types: _compute_bazi_types 产出的命局类型（含 rizhu_wx / yongshen / wuxing_summary）
            geju:       GeJuAnalyzer.analyze 结果（可选，用于补充格局信息）
        Returns:
            {
              'rizhu','rizhu_wx',
              'career','wealth','health','love','overview','tags'
            }
        """
        bz = bazi or {}
        bt = bazi_types or {}
        wx = wuxing or {}
        ss = shishen or {}

        rizhu = bz.get('rizhu', '')
        rizhu_wx = bt.get('rizhu_wx') or wx.get('rizhu_wx', '')
        yong = bt.get('yongshen') or {}
        weights = ss.get('total_weights') or {}
        wx_summary = bt.get('wuxing_summary') or wx.get('summary', '') or ''
        strength = bt.get('strength') or yong.get('strength', '')
        geju_name = bt.get('geju_name') or (geju or {}).get('main_geju', '')
        geju_type = bt.get('geju_type', '')

        career = self._career(rizhu, rizhu_wx, weights, yong, strength, geju_name)
        wealth = self._wealth(rizhu, rizhu_wx, weights, yong, strength)
        health = self._health(rizhu, rizhu_wx, weights, yong, wx_summary, strength)
        love = self._love(rizhu, rizhu_wx, weights, yong, strength)
        overview = self._overview(rizhu, rizhu_wx, strength, geju_name, geju_type, wx_summary, yong)
        tags = self._tags(weights, yong, strength, wx_summary)

        return {
            'rizhu': rizhu,
            'rizhu_wx': rizhu_wx,
            'career': career,
            'wealth': wealth,
            'health': health,
            'love': love,
            'overview': overview,
            'tags': tags,
        }

    # ----------------------------------------------------------------
    # 工具方法
    # ----------------------------------------------------------------
    @staticmethod
    def _w(weights, key):
        try:
            return float((weights or {}).get(key, 0) or 0)
        except Exception:
            return 0.0

    @staticmethod
    def _lvl(weights, key):
        """某十神类的强弱：旺 / 平 / 弱"""
        total = YunChengAnalyzer._w(weights, 'total')
        if total <= 0:
            return '平'
        r = YunChengAnalyzer._w(weights, key) / total
        if r >= 0.3:
            return '旺'
        if r <= 0.1:
            return '弱'
        return '平'

    @staticmethod
    def _yong(yong):
        ys = yong.get('yongshen_name') or yong.get('yongshen') or ''
        xs = '、'.join(yong.get('xishen_names') or []) or '、'.join(yong.get('xishen') or [])
        js = '、'.join(yong.get('jishen_names') or []) or '、'.join(yong.get('jishen') or [])
        return ys, xs, js

    @staticmethod
    def _strength_desc(strength):
        return {
            '身强': '日主五行能量充沛，可任财官',
            '身弱': '日主五行偏弱，宜生扶帮身',
            '中和': '日主五行中和，不偏不倚',
        }.get(strength, '日主强弱待定')

    # ----------------------------------------------------------------
    # 各维度文案（均由真实信号驱动）
    # ----------------------------------------------------------------
    def _career(self, rizhu, wx, weights, yong, strength, geju_name):
        ys, xs, js = self._yong(yong)
        guan = self._lvl(weights, '官杀')   # 事业 / 职权 / 名气约束
        yin = self._lvl(weights, '印星')    # 贵人 / 学业
        shi = self._lvl(weights, '食伤')   # 才华 / 表达
        bi = self._lvl(weights, '比劫')     # 合作 / 竞争
        parts = [f'日主{rizhu}（五行属{wx or "？"}），{self._strength_desc(strength)}。']

        if guan == '旺':
            parts.append('官杀得力，事业心强、易得职权与名气，但亦多约束压力，宜担得起责任、稳扎稳打。')
        elif guan == '弱':
            parts.append('官杀偏弱，不喜被管束，宜以专业技术、自由发挥立身，强求官阶反招是非。')
        else:
            parts.append('官杀中和，事业稳步推进、进退有度。')

        if yin == '旺':
            parts.append('印星护身，多得长辈、上司提携与学业之助，宜借平台与资质增值。')
        elif yin == '弱':
            parts.append('印星不足，少现成靠山，事业须自修内功、主动结善缘。')

        if shi == '旺':
            parts.append('食伤吐秀，才华与表达出众，利于创意、技艺、口才、营销类方向。')

        if bi == '旺':
            parts.append('比劫有力，善合作合伙，亦须防同辈分利、竞争夺财。')

        if ys:
            parts.append(f'用神取{ys}，行运遇{ys}旺地事业得助而上扬；忌{js or "无"}过旺反成牵制。')

        if geju_name and geju_name not in ('', '扶抑格', '身强格', '身弱格'):
            parts.append(f'命入{geju_name}，格局自有气象，事业宜顺势扬长。')

        return ''.join(parts)

    def _wealth(self, rizhu, wx, weights, yong, strength):
        ys, xs, js = self._yong(yong)
        cai = self._lvl(weights, '财星')    # 财运
        bi = self._lvl(weights, '比劫')     # 合作 / 分财 / 竞争
        shi = self._lvl(weights, '食伤')   # 生财之源（财之原神）
        parts = [f'日主{rizhu}（五行属{wx or "？"}），{self._strength_desc(strength)}。']

        if cai == '旺':
            parts.append('财星透力，财源广进、善抓机会，然亦易财来财去，宜理财有度、忌投机冒进。')
        elif cai == '弱':
            parts.append('财星偏弱，求财须务实耕耘、积小成大，不宜高风险搏杀；身弱财旺反为财累。')
        else:
            parts.append('财星中和，财运平稳，量入为出可渐丰。')

        if shi == '旺':
            parts.append('食伤生财，以才华、技艺、创意变现之象明显，宜凭专长出头。')

        if bi == '旺':
            parts.append('比劫有力，合伙求财可期，但须明算账、防朋友分利或争财。')

        if ys:
            parts.append(f'用神取{ys}，逢{ys}旺运财气得扶；忌{js or "无"}耗财之星过旺。')

        return ''.join(parts)

    def _health(self, rizhu, wx, weights, yong, wx_summary, strength):
        ys, xs, js = self._yong(yong)
        yin = self._lvl(weights, '印星')    # 生身 / 免疫力靠山
        body = _WX_BODY.get(wx, '相应脏腑')
        parts = [f'日主{rizhu}（五行属{wx or "？"}），先天体质与「{body}」最为相关。']

        # 五行旺衰 -> 偏颇脏腑
        if wx_summary:
            weak_els = []
            for cat, els in (('极弱', '偏弱'), ('旺极', '偏旺')):
                if cat in wx_summary:
                    for ch in wx_summary:
                        if ch in ('木', '火', '土', '金', '水') and ch not in weak_els:
                            # 粗略取该类别对应的五行
                            idx = wx_summary.find(cat)
                            seg = wx_summary[max(0, idx - 2):idx]
                            for c in seg:
                                if c in ('木', '火', '土', '金', '水'):
                                    weak_els.append((c, cat))
            seen = set()
            for el, cat in weak_els:
                if el in seen:
                    continue
                seen.add(el)
                if cat in ('极弱', '偏弱'):
                    parts.append(f'{el}行偏弱，{_WX_BODY.get(el, "")}易亏，宜温养调补。')
                else:
                    parts.append(f'{el}行偏旺，{_WX_BODY.get(el, "")}易壅滞生热，宜疏泄清润。')

        if yin == '旺':
            parts.append('印星护身，先天免疫与恢复力尚可，唯仍须起居有常。')
        elif yin == '弱':
            parts.append('印星不足，少现成底气，平日宜固本培元、少透支。')

        if strength == '身弱':
            parts.append('日主偏弱，整体耐受力一般，劳顿之后恢复偏慢，宜劳逸有节。')
        elif strength == '身强':
            parts.append('日主偏强，体魄耐劳、承压尚可，仍须防过用。')

        parts.append('以上为依五行生克之推演，具体健康请遵医嘱，命理不作医学诊断。')
        return ''.join(parts)

    def _love(self, rizhu, wx, weights, yong, strength):
        ys, xs, js = self._yong(yong)
        cai = self._lvl(weights, '财星')    # 男命妻星
        guan = self._lvl(weights, '官杀')  # 女命夫星
        shi = self._lvl(weights, '食伤')   # 女命克官（情关）/ 子女
        bi = self._lvl(weights, '比劫')     # 争夫 / 分缘
        parts = [f'日主{rizhu}（五行属{wx or "？"}）。']

        if rizhu:
            # 以日主阴阳粗判男女命取向（与界面 gender 互补参考）
            yang = (('甲', '丙', '戊', '庚', '壬').count(rizhu) > 0)
            if yang:
                if cai == '旺':
                    parts.append('财星得力，异性缘佳、易得伴侣扶持；身强财旺更利婚稳。')
                elif cai == '弱':
                    parts.append('财星偏弱，姻缘须主动经营、晚成更宜；忌因财失和。')
                else:
                    parts.append('财星中和，感情平稳，贵在用心经营。')
            else:
                if guan == '旺':
                    parts.append('官杀得力，易遇负责对象、感情有归宿；官清则夫贤。')
                elif guan == '弱':
                    parts.append('官杀偏弱，良缘偏迟，宜提升自我、待时而嫁；忌官杀混杂招烦。')
                else:
                    parts.append('官杀中和，感情渐进，宜稳不宜急。')
                if shi == '旺':
                    parts.append('食伤吐秀，个性鲜明、重情调，亦须防锋芒伤官、口舌误缘。')

        if bi == '旺':
            parts.append('比劫有力，朋辈情缘交织，须明分寸、防第三者介入或分缘。')

        if ys:
            parts.append(f'用神取{ys}，逢{ys}旺运感情得润；忌{js or "无"}扰缘之星过旺。')

        return ''.join(parts)

    def _overview(self, rizhu, wx, strength, geju_name, geju_type, wx_summary, yong):
        ys, xs, js = self._yong(yong)
        bits = [f'日主{rizhu}（{wx or "？"}），{self._strength_desc(strength)}。']
        if geju_name:
            bits.append(f'格局：{geju_name}（{geju_type or "—"}）。')
        if wx_summary:
            bits.append(f'五行：{wx_summary}。')
        if ys:
            bits.append(f'用神{ys}，喜{xs or "—"}，忌{js or "—"}。')
        bits.append('综合来看，运程宜顺用神、扬长避短：身弱补益生扶，身强用克泄耗，中和则随运而转。')
        return ''.join(bits)

    def _tags(self, weights, yong, strength, wx_summary) -> List[str]:
        tags = []
        if strength:
            tags.append(strength)
        lv_map = {'旺': '偏强', '弱': '偏弱', '平': '均衡'}
        for cat, key in (('官杀', '事业'), ('财星', '财运'), ('印星', '贵人'),
                         ('食伤', '才华'), ('比劫', '人缘')):
            lv = self._lvl(weights, cat)
            if lv != '平':
                tags.append(f'{key}{lv_map[lv]}')
        ys, xs, js = self._yong(yong)
        if ys:
            tags.append(f'用神{ys}')
        return tags

    # ----------------------------------------------------------------
    # 可选：AI 润色（离线不调用；调用方自行决定是否启用）
    # ----------------------------------------------------------------
    def build_ai_prompt(self, result: Dict[str, Any]) -> str:
        """将结构化信号整理为给 AI 的提示词，便于生成流畅运程散文。"""
        bazi = result.get('bazi', {})
        wuxing = result.get('wuxing_detail') or result.get('wuxing')
        shishen = result.get('shishen')
        bazi_types = result.get('bazi_types', {})
        yc = self.analyze(bazi, wuxing, shishen, bazi_types)
        lines = [
            '你是命理咨询师。请基于以下已算出的八字结构化结论，',
            '用自然、专业、温和的中文，撰写一段约 200 字的「综合运程」综述，',
            '涵盖事业、财运、健康、感情，不要编造干支，仅围绕所给信号发挥：',
            '',
            f"日主：{yc.get('rizhu')}（{yc.get('rizhu_wx')}）",
            f"事业：{yc.get('career')}",
            f"财运：{yc.get('wealth')}",
            f"健康：{yc.get('health')}",
            f"感情：{yc.get('love')}",
            f"综合：{yc.get('overview')}",
        ]
        return '\n'.join(lines)

    def analyze_with_ai(self, result: Dict[str, Any], ai_client, system_prompt: str = '') -> Optional[str]:
        """调用 AGNES 将规则结论润色为流畅文案；失败返回 None（调用方回落规则文案）。"""
        try:
            prompt = self.build_ai_prompt(result)
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            resp = ai_client.chat_completion(messages, temperature=0.6, max_tokens=1024)
            text = (resp or {}).get('content', '').strip()
            return text or None
        except Exception as e:
            print(f'运程 AI 润色失败（回落规则文案）：{e}')
            return None
