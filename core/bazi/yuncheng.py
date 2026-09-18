"""
运程总结模块 - 根据八字排盘结果自动生成综合运程分析

覆盖维度：事业 / 财运 / 健康 / 感情
规则引擎：从已算出的结构化信号（十神权重、五行旺衰、用神喜忌、格局）
推导；可选经 智能 润色为流畅文案（analyze_with_ai）。

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
        """从十神权重表中安全取出某一项的数值。

        位于本类最底层：_lvl 及各维度文案方法都经由它读取权重，
        因此这里把所有脏数据（键缺失、值为 None、值为字符串）统一
        兜成 0.0，上层无需再做判空。

        Args:
            weights: 十神权重字典，形如 {'官杀': 2.4, '财星': 1.1, 'total': 8.0}；
                允许为 None。
            key: 要取的十神类别名，或汇总键 'total'。

        Returns:
            float: 对应权重值；缺失或无法转 float 时返回 0.0。
        """
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
        # 用占全局权重的比例而非绝对值，才能跨不同八字横向比较；
        # 五类十神均分约为 0.2，故 0.3 以上论旺、0.1 以下论弱
        r = YunChengAnalyzer._w(weights, key) / total
        if r >= 0.3:
            return '旺'
        if r <= 0.1:
            return '弱'
        return '平'

    @staticmethod
    def _yong(yong):
        """从用神结论中提取用神、喜神、忌神三组名称。

        用神是全局最需要的那个五行/十神，喜神为辅助用神者，忌神为
        损伤用神者——这三者是各维度文案给出"宜/忌"建议的共同依据，
        故各 _career/_wealth/_love 等方法开头都会先调用本方法取值。

        Args:
            yong: 用神分析结果字典。兼容两套键名：优先取带 _name 后缀的
                中文名（yongshen_name / xishen_names / jishen_names），
                取不到则回退到 yongshen / xishen / jishen。

        Returns:
            tuple[str, str, str]: (用神名, 喜神名串, 忌神名串)。
                喜神与忌神可能有多个，已用顿号连接成单个字符串；
                任一项缺失时返回空字符串，调用方直接以真值判断即可。
        """
        ys = yong.get('yongshen_name') or yong.get('yongshen') or ''
        xs = '、'.join(yong.get('xishen_names') or []) or '、'.join(yong.get('xishen') or [])
        js = '、'.join(yong.get('jishen_names') or []) or '、'.join(yong.get('jishen') or [])
        return ys, xs, js

    @staticmethod
    def _strength_desc(strength):
        """把日主旺衰结论翻译成一句可读的中文断语。

        供各维度文案作为开场白复用，统一口径避免各处措辞不一。

        Args:
            strength: 旺衰等级，'身强' / '身弱' / '中和' 之一。

        Returns:
            str: 对应断语；传入未知值（含空串）时返回 '日主强弱待定'。
        """
        return {
            '身强': '日主五行能量充沛，可任财官',
            '身弱': '日主五行偏弱，宜生扶帮身',
            '中和': '日主五行中和，不偏不倚',
        }.get(strength, '日主强弱待定')

    # ----------------------------------------------------------------
    # 各维度文案（均由真实信号驱动）
    # ----------------------------------------------------------------
    def _career(self, rizhu, wx, weights, yong, strength, geju_name):
        """生成「事业」维度文案。

        analyze() 调度的第一个维度方法。事业主要看官杀（职权与约束）、
        印星（贵人学业）、食伤（才华表达）、比劫（合作竞争）四类十神的
        强弱组合，再叠加用神与格局做收尾建议。

        Args:
            rizhu: 日干（命主本人）。
            wx: 日主五行。
            weights: 十神权重字典。
            yong: 用神分析结果字典。
            strength: 日主旺衰等级（'身强'/'身弱'/'中和'）。
            geju_name: 格局名称；扶抑格/身强格/身弱格属通用格局，不额外成句。

        Returns:
            str: 拼接好的事业分析段落。
        """
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

        # 扶抑格/身强格/身弱格是最普遍的默认归类，说了等于没说，
        # 只有特殊格局（如从格、专旺格）才值得单独成句
        if geju_name and geju_name not in ('', '扶抑格', '身强格', '身弱格'):
            parts.append(f'命入{geju_name}，格局自有气象，事业宜顺势扬长。')

        return ''.join(parts)

    def _wealth(self, rizhu, wx, weights, yong, strength):
        """生成「财运」维度文案。

        analyze() 调度的第二个维度方法。财运以财星为主体，食伤为财之
        原神（才华变现即"食伤生财"），比劫则为夺财之星（合伙分利）。
        另需结合身强弱：身弱而财旺者担不起财，反主为财所累。

        Args:
            rizhu: 日干。
            wx: 日主五行。
            weights: 十神权重字典。
            yong: 用神分析结果字典。
            strength: 日主旺衰等级。

        Returns:
            str: 拼接好的财运分析段落。
        """
        ys, xs, js = self._yong(yong)
        c智能 = self._lvl(weights, '财星')    # 财运
        bi = self._lvl(weights, '比劫')     # 合作 / 分财 / 竞争
        shi = self._lvl(weights, '食伤')   # 生财之源（财之原神）
        parts = [f'日主{rizhu}（五行属{wx or "？"}），{self._strength_desc(strength)}。']

        if c智能 == '旺':
            parts.append('财星透力，财源广进、善抓机会，然亦易财来财去，宜理财有度、忌投机冒进。')
        elif c智能 == '弱':
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
        """生成「健康」维度文案。

        analyze() 调度的第三个维度方法。中医与命理共用五行配脏腑的体系
        （见模块级 _WX_BODY），故健康推断的路径是：先由日主五行定先天
        体质倾向，再从五行旺衰摘要中挑出过旺/过弱的五行，对应到脏腑给出
        "偏弱宜补、偏旺宜泄"的调养方向。

        注意：结论仅为五行生克之推演，末尾会附加免责声明，不作医学诊断。

        Args:
            rizhu: 日干。
            wx: 日主五行，用于查 _WX_BODY 定位相关脏腑。
            weights: 十神权重字典（此处主要看印星，印主生身、类比免疫力）。
            yong: 用神分析结果字典。
            wx_summary: 五行旺衰摘要串，形如 '木旺极，水极弱'，本方法从中
                解析出偏颇的五行。
            strength: 日主旺衰等级。

        Returns:
            str: 拼接好的健康分析段落。
        """
        ys, xs, js = self._yong(yong)
        yin = self._lvl(weights, '印星')    # 生身 / 免疫力靠山
        body = _WX_BODY.get(wx, '相应脏腑')
        parts = [f'日主{rizhu}（五行属{wx or "？"}），先天体质与「{body}」最为相关。']

        # 五行旺衰 -> 偏颇脏腑
        # wx_summary 是 WuXingAnalyzer 拼出的短句（如 '木旺极，水极弱'），
        # 五行字总是紧挨在类别词之前，故下面靠"截取类别词前两个字符再筛
        # 五行字"的方式反解，属对既有文案格式的轻量解析而非严格分词
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
            # 上面的嵌套扫描会让同一个五行重复入列，此处按五行去重，
            # 保证每个偏颇五行只出一句调养建议
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
        """生成「感情」维度文案。

        analyze() 调度的第四个维度方法。命理以十神代指配偶：男命看财星
        （妻星），女命看官杀（夫星）；女命另需看食伤（食伤克官，主感情
        中的锋芒与波折）。比劫过旺则主缘分被分（争夫夺妻、第三者）。

        Args:
            rizhu: 日干。本方法据其阴阳粗判男女命取向（甲丙戊庚壬为阳干），
                因为界面未必传入性别，此为退而求其次的参考口径。
            wx: 日主五行。
            weights: 十神权重字典。
            yong: 用神分析结果字典。
            strength: 日主旺衰等级。

        Returns:
            str: 拼接好的感情分析段落；rizhu 为空时仅输出通用部分。
        """
        ys, xs, js = self._yong(yong)
        c智能 = self._lvl(weights, '财星')    # 男命妻星
        guan = self._lvl(weights, '官杀')  # 女命夫星
        shi = self._lvl(weights, '食伤')   # 女命克官（情关）/ 子女
        bi = self._lvl(weights, '比劫')     # 争夫 / 分缘
        parts = [f'日主{rizhu}（五行属{wx or "？"}）。']

        if rizhu:
            # 以日主阴阳粗判男女命取向（与界面 gender 互补参考）
            yang = (('甲', '丙', '戊', '庚', '壬').count(rizhu) > 0)
            if yang:
                if c智能 == '旺':
                    parts.append('财星得力，异性缘佳、易得伴侣扶持；身强财旺更利婚稳。')
                elif c智能 == '弱':
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
        """生成「综合」概述文案。

        analyze() 调度的收尾方法，把日主、格局、五行、用神喜忌四条主线
        压缩成一小段总述，末句给出贯穿全局的调运原则：顺用神而行——
        身弱则生扶补益，身强则克泄耗其有余，中和则随大运流年而转。

        Args:
            rizhu: 日干。
            wx: 日主五行。
            strength: 日主旺衰等级。
            geju_name: 格局名称，为空则跳过格局句。
            geju_type: 格局类别（如正格/变格），缺失时占位显示破折号。
            wx_summary: 五行旺衰摘要串，为空则跳过五行句。
            yong: 用神分析结果字典。

        Returns:
            str: 拼接好的综合概述段落。
        """
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
        """把长段文案压缩成一组短标签，供 UI 以徽章形式速览。

        analyze() 最后调用，输出与前述各维度同源（同样基于十神强弱与
        用神），只是换成极简表达。

        Args:
            weights: 十神权重字典。
            yong: 用神分析结果字典。
            strength: 日主旺衰等级，非空时作为首个标签。
            wx_summary: 五行旺衰摘要串（当前保留待用，不参与标签生成）。

        Returns:
            List[str]: 标签列表，如 ['身强', '事业偏强', '财运偏弱', '用神水']。
        """
        tags = []
        if strength:
            tags.append(strength)
        lv_map = {'旺': '偏强', '弱': '偏弱', '平': '均衡'}
        # 把十神术语映射为大众能懂的生活维度词，再缀上强弱后缀
        for cat, key in (('官杀', '事业'), ('财星', '财运'), ('印星', '贵人'),
                         ('食伤', '才华'), ('比劫', '人缘')):
            lv = self._lvl(weights, cat)
            # 只保留有辨识度的偏强/偏弱项，'平' 属常态不出标签以免刷屏
            if lv != '平':
                tags.append(f'{key}{lv_map[lv]}')
        ys, xs, js = self._yong(yong)
        if ys:
            tags.append(f'用神{ys}')
        return tags

    # ----------------------------------------------------------------
    # 可选：智能 润色（离线不调用；调用方自行决定是否启用）
    # ----------------------------------------------------------------
    def build_ai_prompt(self, result: Dict[str, Any]) -> str:
        """将结构化信号整理为给 智能 的提示词，便于生成流畅运程散文。"""
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
            print(f'运程 智能 润色失败（回落规则文案）：{e}')
            return None
