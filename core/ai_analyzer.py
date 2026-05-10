from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING

PERSONALITY_TRAITS = {
    '木': {
        'positive': ['积极向上', '富有创造力', '善于创新', '有进取心', '正直善良'],
        'negative': ['固执己见', '过于冲动', '缺乏耐心', '容易情绪化']
    },
    '火': {
        'positive': ['热情洋溢', '乐观开朗', '富有感染力', '社交能力强', '充满活力'],
        'negative': ['急躁冲动', '缺乏冷静', '过于张扬', '容易骄傲']
    },
    '土': {
        'positive': ['稳重可靠', '诚实守信', '有责任感', '踏实肯干', '包容大度'],
        'negative': ['过于保守', '缺乏变通', '固执僵化', '反应迟钝']
    },
    '金': {
        'positive': ['果断刚毅', '追求完美', '有决断力', '精明干练', '公正无私'],
        'negative': ['刻薄寡恩', '刚愎自用', '过于挑剔', '缺乏变通']
    },
    '水': {
        'positive': ['聪明灵活', '思维敏捷', '适应力强', '富有智慧', '善于变通'],
        'negative': ['散漫无章', '缺乏定力', '优柔寡断', '过于敏感']
    }
}

ELEMENT_RECOMMENDATIONS = {
    '木': {
        'career': '适合从事创意、艺术、教育、农林等行业',
        'color': '绿色、青色系',
        'direction': '东方',
        'advice': '保持创新精神，注意人际关系'
    },
    '火': {
        'career': '适合从事销售、演艺、公关、能源等行业',
        'color': '红色、紫色系',
        'direction': '南方',
        'advice': '发挥热情优势，保持冷静思考'
    },
    '土': {
        'career': '适合从事金融、房地产、建筑、管理等行业',
        'color': '黄色、棕色系',
        'direction': '中央',
        'advice': '发挥稳重优势，学会灵活变通'
    },
    '金': {
        'career': '适合从事法律、金融、金属、机械等行业',
        'color': '白色、金色系',
        'direction': '西方',
        'advice': '发挥果断优势，注意人际关系'
    },
    '水': {
        'career': '适合从事商贸、物流、旅游、科技等行业',
        'color': '蓝色、黑色系',
        'direction': '北方',
        'advice': '发挥智慧优势，保持专注定力'
    }
}

class AIAnalyzer:
    def __init__(self):
        pass

    def analyze(self, bazhi, wuxing_result, shishen_result, mingli_result):
        rizhu = bazhi['rizhu']
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        analysis = {
            'overview': self._generate_overview(bazhi, wuxing_result, shishen_result),
            'personality': self._generate_personality(rizhu_wx, wuxing_result),
            'life_trends': self._generate_life_trends(wuxing_result, shishen_result),
            'opportunities': self._generate_opportunities(wuxing_result, shishen_result),
            'challenges': self._generate_challenges(wuxing_result, shishen_result),
            'compatibility': self._generate_compatibility(wuxing_result),
            'recommendations': self._generate_recommendations(rizhu_wx, wuxing_result)
        }
        
        return analysis

    def _generate_overview(self, bazhi, wuxing_result, shishen_result):
        rizhu = bazhi['rizhu']
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        parts = []
        parts.append(f"您的日主为{rizhu}，五行属{rizhu_wx}")
        
        if wuxing_result['summary']:
            parts.append(f"五行分析显示：{wuxing_result['summary']}")
        
        shishen_summary = shishen_result['summary']
        if shishen_summary:
            shishen_list = []
            for shishen, count in shishen_summary.items():
                shishen_list.append(f"{shishen}{count}个")
            parts.append(f"十神分布：{'、'.join(shishen_list)}")
        
        return '；'.join(parts)

    def _generate_personality(self, rizhu_wx, wuxing_result):
        traits = PERSONALITY_TRAITS.get(rizhu_wx, {'positive': [], 'negative': []})
        
        positive_traits = traits['positive'][:3]
        negative_traits = traits['negative'][:2]
        
        dominant_elements = []
        for wx in ['木', '火', '土', '金', '水']:
            if wuxing_result[wx]['count'] >= 6:
                dominant_elements.append(wx)
            elif wuxing_result[wx]['count'] >= 4:
                dominant_elements.append(wx)
        
        for wx in dominant_elements:
            if wx != rizhu_wx:
                wx_traits = PERSONALITY_TRAITS.get(wx, {'positive': [], 'negative': []})
                positive_traits.extend(wx_traits['positive'][:2])
        
        return list(set(positive_traits))[:5]

    def _generate_life_trends(self, wuxing_result, shishen_result):
        trends = []
        
        wuxing_summary = wuxing_result['summary']
        if '旺极' in wuxing_summary:
            trends.append('整体运势较强，但需注意物极必反')
        elif '偏旺' in wuxing_summary:
            trends.append('运势较旺，适合积极进取')
        elif '偏弱' in wuxing_summary:
            trends.append('运势偏弱，需要积累和等待时机')
        elif '五行均衡' in wuxing_summary:
            trends.append('五行均衡，运势平稳发展')
        
        shishen_summary = shishen_result['summary']
        if '正官' in shishen_summary or '七杀' in shishen_summary:
            trends.append('事业上有一定的压力和挑战')
        if '正印' in shishen_summary or '偏印' in shishen_summary:
            trends.append('学业和智慧方面有优势')
        if '正财' in shishen_summary or '偏财' in shishen_summary:
            trends.append('财运方面有机会')
        
        return '；'.join(trends)

    def _generate_opportunities(self, wuxing_result, shishen_result):
        opportunities = []
        
        max_wx = max(['木', '火', '土', '金', '水'], key=lambda x: wuxing_result[x]['count'])
        opportunities.append(f'{max_wx}元素旺盛，在相关领域会有机会')
        
        shishen_summary = shishen_result['summary']
        if '正印' in shishen_summary:
            opportunities.append('学业、知识学习方面有良机')
        if '偏财' in shishen_summary:
            opportunities.append('投资、副业等方面有机会')
        if '食神' in shishen_summary:
            opportunities.append('创意、艺术方面有发挥空间')
        if '正官' in shishen_summary:
            opportunities.append('事业晋升、职位提升有机会')
        
        return opportunities

    def _generate_challenges(self, wuxing_result, shishen_result):
        challenges = []
        
        min_wx = min(['木', '火', '土', '金', '水'], key=lambda x: wuxing_result[x]['count'])
        if wuxing_result[min_wx]['count'] <= 2:
            challenges.append(f'{min_wx}元素较弱，需要注意相关方面的不足')
        
        shishen_summary = shishen_result['summary']
        if '七杀' in shishen_summary:
            challenges.append('可能面临竞争压力和挑战')
        if '劫财' in shishen_summary:
            challenges.append('需要注意财务方面的损耗')
        if '伤官' in shishen_summary and '正官' in shishen_summary:
            challenges.append('需要注意人际关系的协调')
        
        return challenges

    def _generate_compatibility(self, wuxing_result):
        elements = ['木', '火', '土', '金', '水']
        counts = [(wx, wuxing_result[wx]['count']) for wx in elements]
        counts.sort(key=lambda x: x[1], reverse=True)
        
        dominant = counts[0][0]
        secondary = counts[1][0]
        
        compatibility = []
        
        element_pairs = {
            '木': ['水', '火'],
            '火': ['木', '土'],
            '土': ['火', '金'],
            '金': ['土', '水'],
            '水': ['金', '木']
        }
        
        compatible = element_pairs.get(dominant, [])
        if secondary in compatible:
            compatibility.append(f'{dominant}与{secondary}相生，整体格局协调')
        else:
            compatibility.append(f'{dominant}为主导，{secondary}为辅助')
        
        for wx, count in counts[-2:]:
            if count <= 2:
                compatibility.append(f'{wx}元素较弱，建议适当补充')
        
        return '；'.join(compatibility)

    def _generate_recommendations(self, rizhu_wx, wuxing_result):
        recommendations = []
        
        rec = ELEMENT_RECOMMENDATIONS.get(rizhu_wx, {})
        if 'career' in rec:
            recommendations.append(f"职业选择：{rec['career']}")
        if 'color' in rec:
            recommendations.append(f"幸运颜色：{rec['color']}")
        if 'advice' in rec:
            recommendations.append(f"生活建议：{rec['advice']}")
        
        min_wx = min(['木', '火', '土', '金', '水'], key=lambda x: wuxing_result[x]['count'])
        if wuxing_result[min_wx]['count'] <= 2:
            wx_rec = ELEMENT_RECOMMENDATIONS.get(min_wx, {})
            if 'advice' in wx_rec:
                recommendations.append(f"注意补充{min_wx}元素：{wx_rec['advice']}")
        
        return recommendations