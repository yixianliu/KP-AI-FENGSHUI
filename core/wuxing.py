"""
五行量化分析模块 - 完善五行能量计算体系

修复内容：
1. 细化藏干能量分值：本气0.6、中气0.3、余气0.1（原为统一0.5）
2. 增加月令扶抑权重：根据月令调整五行能量
3. 增加通根强弱判定规则
4. 完善五行均衡分析逻辑
"""

TIAN_GAN_WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
}

DI_ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

DI_ZHI_HIDDEN_GAN = {
    '子': ['癸'],
    '丑': ['己', '辛', '癸'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲']
}

DI_ZHI_HIDDEN_GAN_DETAIL = {
    '子': [('癸', '本气', 0.6)],
    '丑': [('己', '本气', 0.6), ('辛', '中气', 0.3), ('癸', '余气', 0.1)],
    '寅': [('甲', '本气', 0.6), ('丙', '中气', 0.3), ('戊', '余气', 0.1)],
    '卯': [('乙', '本气', 0.6)],
    '辰': [('戊', '本气', 0.6), ('乙', '中气', 0.3), ('癸', '余气', 0.1)],
    '巳': [('丙', '本气', 0.6), ('戊', '中气', 0.3), ('庚', '余气', 0.1)],
    '午': [('丁', '本气', 0.6), ('己', '中气', 0.3)],
    '未': [('己', '本气', 0.6), ('丁', '中气', 0.3), ('乙', '余气', 0.1)],
    '申': [('庚', '本气', 0.6), ('壬', '中气', 0.3), ('戊', '余气', 0.1)],
    '酉': [('辛', '本气', 0.6)],
    '戌': [('戊', '本气', 0.6), ('辛', '中气', 0.3), ('丁', '余气', 0.1)],
    '亥': [('壬', '本气', 0.6), ('甲', '中气', 0.3)]
}

YUE_LING_WEIGHT = {
    '寅': {'木': 1.5, '火': 0.5, '土': 0.3, '金': 0.2, '水': 0.3},
    '卯': {'木': 1.5, '火': 0.6, '土': 0.2, '金': 0.1, '水': 0.3},
    '辰': {'土': 1.0, '木': 0.4, '水': 0.3, '火': 0.2, '金': 0.3},
    '巳': {'火': 1.5, '土': 0.4, '金': 0.2, '木': 0.3, '水': 0.2},
    '午': {'火': 1.5, '土': 0.5, '金': 0.1, '木': 0.2, '水': 0.2},
    '未': {'土': 1.0, '火': 0.4, '木': 0.3, '水': 0.2, '金': 0.3},
    '申': {'金': 1.5, '水': 0.5, '土': 0.3, '木': 0.2, '火': 0.2},
    '酉': {'金': 1.5, '土': 0.4, '水': 0.3, '木': 0.1, '火': 0.2},
    '戌': {'土': 1.0, '金': 0.4, '火': 0.3, '木': 0.2, '水': 0.2},
    '亥': {'水': 1.5, '木': 0.5, '火': 0.2, '土': 0.3, '金': 0.3},
    '子': {'水': 1.5, '金': 0.4, '火': 0.1, '木': 0.3, '土': 0.3},
    '丑': {'土': 1.0, '水': 0.4, '金': 0.3, '火': 0.2, '木': 0.2}
}


class WuXingAnalyzer:
    """五行分析器
    
    修复内容：
    1. 藏干能量细化：本气0.6、中气0.3、余气0.1
    2. 增加月令扶抑权重
    3. 增加通根强弱判定
    4. 完善五行均衡分析
    """
    
    def __init__(self):
        self.wuxing = ['木', '火', '土', '金', '水']
    
    def analyze(self, bazhi, month_zhi=None):
        """分析五行能量（含月令权重、藏干细化）
        
        修正：原算法藏干统一0.5分值，现在区分本气/中气/余气
        修正：原算法无月令权重，现在根据月令调整能量
        """
        ganzhi_list = bazhi['四柱']
        
        result = {wx: {'count': 0.0, 'score': 0.0, 'elements': [], 'sources': []} 
                 for wx in self.wuxing}
        
        lunar_month_zhi = month_zhi if month_zhi else bazhi.get('month_zhi', '')
        yue_ling_weight = YUE_LING_WEIGHT.get(lunar_month_zhi, {})
        
        for pillar_name, ganzhi in zip(['年柱', '月柱', '日柱', '时柱'], ganzhi_list):
            if not ganzhi:
                continue
                
            gan = ganzhi[0]
            zhi = ganzhi[1]
            
            wx_gan = TIAN_GAN_WUXING[gan]
            base_score = 1.0
            if lunar_month_zhi and wx_gan in yue_ling_weight:
                base_score *= yue_ling_weight[wx_gan]
            
            result[wx_gan]['count'] += 1
            result[wx_gan]['score'] += base_score
            result[wx_gan]['elements'].append(gan)
            result[wx_gan]['sources'].append(f'{pillar_name}天干{gan}')
            
            wx_zhi = DI_ZHI_WUXING[zhi]
            base_score = 1.0
            if lunar_month_zhi and wx_zhi in yue_ling_weight:
                base_score *= yue_ling_weight[wx_zhi]
            
            result[wx_zhi]['count'] += 1
            result[wx_zhi]['score'] += base_score
            result[wx_zhi]['elements'].append(zhi)
            result[wx_zhi]['sources'].append(f'{pillar_name}地支{zhi}')
            
            hidden_gans = DI_ZHI_HIDDEN_GAN_DETAIL.get(zhi, [])
            for hidden_gan, qi_type, qi_score in hidden_gans:
                wx_hidden = TIAN_GAN_WUXING[hidden_gan]
                base_score = qi_score
                if lunar_month_zhi and wx_hidden in yue_ling_weight:
                    base_score *= yue_ling_weight[wx_hidden]
                
                result[wx_hidden]['count'] += qi_score
                result[wx_hidden]['score'] += base_score
                result[wx_hidden]['elements'].append(f'{zhi}藏{hidden_gan}')
                result[wx_hidden]['sources'].append(f'{pillar_name}{zhi}藏{hidden_gan}({qi_type})')
        
        total_score = sum(result[wx]['score'] for wx in self.wuxing)
        total_count = sum(result[wx]['count'] for wx in self.wuxing)
        
        rizhu = bazhi.get('rizhu', '')
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        tonggen_info = self._analyze_tonggen(bazhi, rizhu)
        
        for wx in self.wuxing:
            result[wx]['percentage'] = round(
                result[wx]['score'] / total_score * 100 if total_score > 0 else 0, 1
            )
            result[wx]['count_percentage'] = round(
                result[wx]['count'] / total_count * 100 if total_count > 0 else 0, 1
            )
            result[wx]['is_rizhu'] = wx == rizhu_wx
        
        result['summary'] = self.get_summary(result, rizhu_wx)
        result['tonggen'] = tonggen_info
        result['yue_ling'] = lunar_month_zhi
        result['total_score'] = round(total_score, 2)
        result['total_count'] = round(total_count, 2)
        result['rizhu_wx'] = rizhu_wx
        
        return result
    
    def _analyze_tonggen(self, bazhi, rizhu):
        """分析日主通根情况（新增）"""
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        tonggen_list = []
        strong_count = 0
        weak_count = 0
        
        for pillar_name, ganzhi in zip(['年柱', '月柱', '日柱', '时柱'], bazhi['四柱']):
            if not ganzhi:
                continue
                
            zhi = ganzhi[1]
            zhi_wx = DI_ZHI_WUXING.get(zhi)
            
            if zhi_wx == rizhu_wx:
                hidden_gans = DI_ZHI_HIDDEN_GAN_DETAIL.get(zhi, [])
                has_rizhu_in_hidden = any(hg[0] == rizhu for hg in hidden_gans)
                
                if has_rizhu_in_hidden:
                    tonggen_list.append({
                        'pillar': pillar_name,
                        'zhi': zhi,
                        'strength': '强根',
                        'reason': f'{zhi}中藏{rizhu}为本气'
                    })
                    strong_count += 1
                else:
                    tonggen_list.append({
                        'pillar': pillar_name,
                        'zhi': zhi,
                        'strength': '中气',
                        'reason': f'{zhi}五行与日主相同'
                    })
                    weak_count += 1
        
        total_tonggen = len(tonggen_list)
        
        return {
            'rizhu': rizhu,
            'rizhu_wx': rizhu_wx,
            'total': total_tonggen,
            'strong': strong_count,
            'weak': weak_count,
            'details': tonggen_list,
            'description': self._get_tonggen_description(total_tonggen, strong_count)
        }
    
    def _get_tonggen_description(self, total, strong):
        """生成通根描述"""
        if total == 0:
            return '日主无通根，身弱之象'
        elif total >= 3:
            return f'日主通根{total}处，{strong}处强根，身强无疑'
        elif total == 2:
            if strong >= 1:
                return f'日主通根{total}处，{strong}处强根，身较强'
            else:
                return f'日主通根{total}处，无强根，身偏弱'
        else:
            if strong >= 1:
                return f'日主通根{total}处强根，身偏强'
            else:
                return f'日主通根{total}处，根气不足，身偏弱'
    
    def get_summary(self, data, rizhu_wx):
        """生成五行分析摘要（完善版）"""
        sorted_wx = sorted(self.wuxing, key=lambda x: data[x]['score'], reverse=True)
        
        max_wx = sorted_wx[0]
        min_wx = sorted_wx[-1]
        
        max_score = data[max_wx]['score']
        min_score = data[min_wx]['score']
        total_score = data.get('total_score', 0)
        
        summary = []
        
        if total_score > 0:
            max_ratio = max_score / total_score
            min_ratio = min_score / total_score
            
            if max_ratio >= 0.4:
                summary.append(f"{max_wx}旺极")
            elif max_ratio >= 0.3:
                summary.append(f"{max_wx}偏旺")
            
            if min_ratio <= 0.08:
                summary.append(f"{min_wx}极弱")
            elif min_ratio <= 0.15:
                summary.append(f"{min_wx}偏弱")
            
            if rizhu_wx and data[rizhu_wx]['score'] >= total_score * 0.25:
                summary.append("日主偏强")
            elif rizhu_wx and data[rizhu_wx]['score'] <= total_score * 0.12:
                summary.append("日主偏弱")
        
        if not summary:
            summary.append("五行均衡")
        
        return '，'.join(summary)
    
    def analyze_wangshuai(self, bazhi, month_zhi=None):
        """判断日主旺衰（新增完整方法）"""
        wuxing_result = self.analyze(bazi, month_zhi)
        
        rizhu_wx = wuxing_result.get('rizhu_wx', '')
        rizhu_score = wuxing_result.get(rizhu_wx, {}).get('score', 0)
        total_score = wuxing_result.get('total_score', 0)
        
        tonggen = wuxing_result.get('tonggen', {})
        tonggen_total = tonggen.get('total', 0)
        tonggen_strong = tonggen.get('strong', 0)
        
        rizhu_ratio = rizhu_score / total_score if total_score > 0 else 0
        
        wangshuai_level = ''
        description = ''
        
        if rizhu_ratio >= 0.3 or (tonggen_total >= 2 and tonggen_strong >= 1):
            wangshuai_level = '身强'
            description = f'日主{rizhu_wx}得令或得地，五行分值占比{rizhu_ratio:.1%}，通根{tonggen_total}处'
        elif rizhu_ratio <= 0.12 or tonggen_total == 0:
            wangshuai_level = '身弱'
            description = f'日主{rizhu_wx}不得令不得地，五行分值占比{rizhu_ratio:.1%}，通根{tonggen_total}处'
        else:
            wangshuai_level = '中和'
            description = f'日主{rizhu_wx}五行中和，分值占比{rizhu_ratio:.1%}'
        
        return {
            'level': wangshuai_level,
            'description': description,
            'rizhu_score': round(rizhu_score, 2),
            'total_score': total_score,
            'rizhu_ratio': round(rizhu_ratio, 3),
            'tonggen': tonggen
        }