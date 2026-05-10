from core.baazi import TIAN_GAN, DI_ZHI
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING, DI_ZHI_HIDDEN_GAN

NAYIN_MAP = {
    '甲子': ('海中金', '金'), '乙丑': ('海中金', '金'),
    '丙寅': ('炉中火', '火'), '丁卯': ('炉中火', '火'),
    '戊辰': ('大林木', '木'), '己巳': ('大林木', '木'),
    '庚午': ('路旁土', '土'), '辛未': ('路旁土', '土'),
    '壬申': ('剑锋金', '金'), '癸酉': ('剑锋金', '金'),
    '甲戌': ('山头火', '火'), '乙亥': ('山头火', '火'),
    '丙子': ('涧下水', '水'), '丁丑': ('涧下水', '水'),
    '戊寅': ('城头土', '土'), '己卯': ('城头土', '土'),
    '庚辰': ('白蜡金', '金'), '辛巳': ('白蜡金', '金'),
    '壬午': ('杨柳木', '木'), '癸未': ('杨柳木', '木'),
    '甲申': ('泉中水', '水'), '乙酉': ('泉中水', '水'),
    '丙戌': ('屋上土', '土'), '丁亥': ('屋上土', '土'),
    '戊子': ('霹雳火', '火'), '己丑': ('霹雳火', '火'),
    '庚寅': ('松柏木', '木'), '辛卯': ('松柏木', '木'),
    '壬辰': ('长流水', '水'), '癸巳': ('长流水', '水'),
    '甲午': ('沙中金', '金'), '乙未': ('沙中金', '金'),
    '丙申': ('山下火', '火'), '丁酉': ('山下火', '火'),
    '戊戌': ('平地木', '木'), '己亥': ('平地木', '木'),
    '庚子': ('壁上土', '土'), '辛丑': ('壁上土', '土'),
    '壬寅': ('金箔金', '金'), '癸卯': ('金箔金', '金'),
    '甲辰': ('覆灯火', '火'), '乙巳': ('覆灯火', '火'),
    '丙午': ('天河水', '水'), '丁未': ('天河水', '水'),
    '戊申': ('大驿土', '土'), '己酉': ('大驿土', '土'),
    '庚戌': ('钗钏金', '金'), '辛亥': ('钗钏金', '金'),
    '壬子': ('桑柘木', '木'), '癸丑': ('桑柘木', '木'),
    '甲寅': ('大溪水', '水'), '乙卯': ('大溪水', '水'),
    '丙辰': ('沙中土', '土'), '丁巳': ('沙中土', '土'),
    '戊午': ('天上火', '火'), '己未': ('天上火', '火'),
    '庚申': ('石榴木', '木'), '辛酉': ('石榴木', '木'),
    '壬戌': ('大海水', '水'), '癸亥': ('大海水', '水')
}

SHEN_SHA = {
    '天德': {
        'description': '天德贵人，主吉祥、逢凶化吉，一生少病灾',
        'locations': ['月柱'],
        'conditions': {'丙': ['寅'], '丁': ['亥'], '戊': ['寅'], '己': ['申'], '庚': ['亥'], '辛': ['巳'], '壬': ['寅'], '癸': ['申']}
    },
    '月德': {
        'description': '月德贵人，主仁慈、聪明、福寿，一生平安',
        'locations': ['月柱'],
        'conditions': {'丙': ['甲'], '丁': ['壬'], '戊': ['丙'], '己': ['甲'], '庚': ['戊'], '辛': ['丙'], '壬': ['庚'], '癸': ['戊']}
    },
    '文昌': {
        'description': '文昌星，主学业、才华、聪明过人',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['巳'], '乙': ['午'], '丙': ['申'], '丁': ['酉'], '戊': ['申'], '己': ['酉'], '庚': ['亥'], '辛': ['子'], '壬': ['寅'], '癸': ['卯']}
    },
    '桃花': {
        'description': '桃花星，主人缘、异性缘、社交能力强',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'子': ['卯'], '午': ['酉'], '卯': ['子'], '酉': ['午']}
    },
    '驿马': {
        'description': '驿马星，主变动、旅行、迁移',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'申': ['寅'], '寅': ['申'], '巳': ['亥'], '亥': ['巳']}
    },
    '华盖': {
        'description': '华盖星，主艺术、才华、孤独',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'寅': ['戌'], '戌': ['寅'], '辰': ['丑'], '丑': ['辰']}
    },
    '将星': {
        'description': '将星，主权威、领导力、事业有成',
        'locations': ['月柱', '时柱'],
        'conditions': {'子': ['午'], '午': ['子'], '卯': ['酉'], '酉': ['卯']}
    },
    '天乙': {
        'description': '天乙贵人，主贵人相助、逢凶化吉',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'], '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'], '庚': ['寅', '午'], '辛': ['寅', '午'], '壬': ['巳', '卯'], '癸': ['巳', '卯']}
    },
    '劫煞': {
        'description': '劫煞，主是非、争斗、意外之灾',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'申': ['巳'], '巳': ['申'], '寅': ['亥'], '亥': ['寅']}
    },
    '亡神': {
        'description': '亡神，主官非、病灾、精神困扰',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'寅': ['巳'], '巳': ['申'], '申': ['亥'], '亥': ['寅']}
    },
    '孤辰': {
        'description': '孤辰，主孤独、寡合、婚姻不顺',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'寅': ['巳'], '巳': ['申'], '申': ['亥'], '亥': ['寅']}
    },
    '寡宿': {
        'description': '寡宿，主孤独、守寡、人际关系淡薄',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'辰': ['丑'], '丑': ['辰'], '戌': ['未'], '未': ['戌']}
    }
}

MAIN_STARS = {
    '紫微': {
        'characteristics': '紫微为帝星，主尊贵、权威、领导力',
        'influence': '具有领导才能，容易成为领袖人物，一生运势较强',
        'element': '土'
    },
    '天府': {
        'characteristics': '天府为财库，主财富、稳重、保守',
        'influence': '财运较好，善于理财，但有时过于保守',
        'element': '土'
    },
    '太阳': {
        'characteristics': '太阳主光明、热情、正直',
        'influence': '性格开朗，乐于助人，事业上容易得到他人帮助',
        'element': '火'
    },
    '太阴': {
        'characteristics': '太阴主温柔、细腻、智慧',
        'influence': '心思细腻，富有艺术才华，适合从事文艺工作',
        'element': '水'
    },
    '贪狼': {
        'characteristics': '贪狼主欲望、才华、交际',
        'influence': '多才多艺，社交能力强，但需注意节制欲望',
        'element': '木'
    },
    '巨门': {
        'characteristics': '巨门主口才、是非、谋略',
        'influence': '善于言辞，适合从事律师、教师等职业',
        'element': '水'
    },
    '天相': {
        'characteristics': '天相主相貌、辅佐、正直',
        'influence': '相貌端正，善于辅佐他人，适合做幕僚',
        'element': '水'
    },
    '天梁': {
        'characteristics': '天梁主荫庇、延寿、清高',
        'influence': '一生多福气，容易得到长辈相助',
        'element': '土'
    },
    '七杀': {
        'characteristics': '七杀主刚强、果断、权威',
        'influence': '性格刚强，做事果断，但需注意脾气',
        'element': '金'
    },
    '破军': {
        'characteristics': '破军主变革、开创、破坏',
        'influence': '具有开创精神，但有时过于冲动',
        'element': '水'
    },
    '廉贞': {
        'characteristics': '廉贞主清廉、固执、桃花',
        'influence': '为人正直，但有时过于固执',
        'element': '火'
    },
    '武曲': {
        'characteristics': '武曲主财富、武勇、果断',
        'influence': '财运旺盛，适合经商或从军',
        'element': '金'
    }
}

TIAN_GAN_RELATION = {
    '甲': {'生': '丙', '克': '戊', '被生': '壬', '被克': '庚'},
    '乙': {'生': '丁', '克': '己', '被生': '癸', '被克': '辛'},
    '丙': {'生': '戊', '克': '庚', '被生': '甲', '被克': '壬'},
    '丁': {'生': '己', '克': '辛', '被生': '乙', '被克': '癸'},
    '戊': {'生': '庚', '克': '壬', '被生': '丙', '被克': '甲'},
    '己': {'生': '辛', '克': '癸', '被生': '丁', '被克': '乙'},
    '庚': {'生': '壬', '克': '甲', '被生': '戊', '被克': '丙'},
    '辛': {'生': '癸', '克': '乙', '被生': '己', '被克': '丁'},
    '壬': {'生': '甲', '克': '丙', '被生': '庚', '被克': '戊'},
    '癸': {'生': '乙', '克': '丁', '被生': '辛', '被克': '己'}
}

DI_ZHI_RELATION = {
    '子': {'冲': '午', '合': '丑', '害': '未', '刑': '卯'},
    '丑': {'冲': '未', '合': '子', '害': '午', '刑': '戌'},
    '寅': {'冲': '申', '合': '亥', '害': '巳', '刑': '巳'},
    '卯': {'冲': '酉', '合': '戌', '害': '辰', '刑': '子'},
    '辰': {'冲': '戌', '合': '酉', '害': '卯', '刑': '辰'},
    '巳': {'冲': '亥', '合': '申', '害': '寅', '刑': '寅'},
    '午': {'冲': '子', '合': '未', '害': '丑', '刑': '午'},
    '未': {'冲': '丑', '合': '午', '害': '子', '刑': '丑'},
    '申': {'冲': '寅', '合': '巳', '害': '亥', '刑': '申'},
    '酉': {'冲': '卯', '合': '辰', '害': '戌', '刑': '酉'},
    '戌': {'冲': '辰', '合': '卯', '害': '酉', '刑': '未'},
    '亥': {'冲': '巳', '合': '寅', '害': '申', '刑': '亥'}
}

KONG_WANG_TABLE = {
    '甲子': ['戌', '亥'], '乙丑': ['戌', '亥'], '丙寅': ['申', '酉'], '丁卯': ['申', '酉'],
    '戊辰': ['午', '未'], '己巳': ['午', '未'], '庚午': ['辰', '巳'], '辛未': ['辰', '巳'],
    '壬申': ['寅', '卯'], '癸酉': ['寅', '卯'], '甲戌': ['子', '丑'], '乙亥': ['子', '丑'],
    '丙子': ['戌', '亥'], '丁丑': ['戌', '亥'], '戊寅': ['申', '酉'], '己卯': ['申', '酉'],
    '庚辰': ['午', '未'], '辛巳': ['午', '未'], '壬午': ['辰', '巳'], '癸未': ['辰', '巳'],
    '甲申': ['寅', '卯'], '乙酉': ['寅', '卯'], '丙戌': ['子', '丑'], '丁亥': ['子', '丑'],
    '戊子': ['戌', '亥'], '己丑': ['戌', '亥'], '庚寅': ['申', '酉'], '辛卯': ['申', '酉'],
    '壬辰': ['午', '未'], '癸巳': ['午', '未'], '甲午': ['辰', '巳'], '乙未': ['辰', '巳'],
    '丙申': ['寅', '卯'], '丁酉': ['寅', '卯'], '戊戌': ['子', '丑'], '己亥': ['子', '丑'],
    '庚子': ['戌', '亥'], '辛丑': ['戌', '亥'], '壬寅': ['申', '酉'], '癸卯': ['申', '酉'],
    '甲辰': ['午', '未'], '乙巳': ['午', '未'], '丙午': ['辰', '巳'], '丁未': ['辰', '巳'],
    '戊申': ['寅', '卯'], '己酉': ['寅', '卯'], '庚戌': ['子', '丑'], '辛亥': ['子', '丑'],
    '壬子': ['戌', '亥'], '癸丑': ['戌', '亥'], '甲寅': ['申', '酉'], '乙卯': ['申', '酉'],
    '丙辰': ['午', '未'], '丁巳': ['午', '未'], '戊午': ['辰', '巳'], '己未': ['辰', '巳'],
    '庚申': ['寅', '卯'], '辛酉': ['寅', '卯'], '壬戌': ['子', '丑'], '癸亥': ['子', '丑']
}

class MingLiAnalyzer:
    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}

    def analyze_hidden_stems(self, bazhi):
        result = []
        pillars = ['年柱', '月柱', '日柱', '时柱']
        
        for i, pillar in enumerate(pillars):
            ganzhi = bazhi['四柱'][i]
            zhi = ganzhi[1]
            hidden_gans = DI_ZHI_HIDDEN_GAN.get(zhi, [])
            
            if hidden_gans:
                hidden_info = []
                for hg in hidden_gans:
                    wx = TIAN_GAN_WUXING.get(hg, '')
                    hidden_info.append(f"{hg}({wx})")
                
                result.append({
                    'pillar': pillar,
                    'ganzhi': ganzhi,
                    'hidden_stems': hidden_gans,
                    'description': f'{pillar}地支{zhi}藏干：{"、".join(hidden_info)}'
                })
        
        return {'hidden_stems': result}

    def analyze_nayin(self, bazhi):
        result = {}
        pillars = ['year', 'month', 'day', 'hour']
        pillar_names = ['年柱', '月柱', '日柱', '时柱']
        
        for i, pillar in enumerate(pillars):
            ganzhi = bazhi[pillar]
            nayin_info = NAYIN_MAP.get(ganzhi, ('', ''))
            
            result[pillar] = {
                'pillar': pillar_names[i],
                'ganzhi': ganzhi,
                'nayin': nayin_info[0],
                'element': nayin_info[1],
                'description': f'{pillar_names[i]}{ganzhi}，纳音{nayin_info[0]}，五行属{nayin_info[1]}'
            }
        
        return result

    def analyze_shensha(self, bazhi):
        positive = []
        negative = []
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        for sha_name, sha_info in SHEN_SHA.items():
            conditions = sha_info['conditions']
            
            for i, ganzhi in enumerate(ganzhi_list):
                gan = ganzhi[0]
                zhi = ganzhi[1]
                
                if gan in conditions:
                    if zhi in conditions[gan]:
                        entry = {
                            'name': sha_name,
                            'location': pillars[i],
                            'ganzhi': ganzhi,
                            'description': sha_info['description']
                        }
                        
                        if sha_name in ['天德', '月德', '文昌', '桃花', '驿马', '华盖', '将星', '天乙']:
                            positive.append(entry)
                        else:
                            negative.append(entry)
        
        return {'positive': positive, 'negative': negative}

    def analyze_main_stars(self, bazhi):
        rizhu = bazhi['rizhu']
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        stars = []
        for star_name, star_info in MAIN_STARS.items():
            if star_info['element'] == rizhu_wx:
                stars.append({
                    'name': star_name,
                    'element': star_info['element'],
                    'characteristics': star_info['characteristics'],
                    'influence': star_info['influence']
                })
        
        if not stars:
            star_list = list(MAIN_STARS.keys())[:3]
            for star_name in star_list:
                stars.append({
                    'name': star_name,
                    'element': MAIN_STARS[star_name]['element'],
                    'characteristics': MAIN_STARS[star_name]['characteristics'],
                    'influence': MAIN_STARS[star_name]['influence']
                })
        
        return {'stars': stars}

    def analyze_ganzhi_relations(self, bazhi):
        gan_relations = []
        zhi_relations = []
        
        pillars = bazhi['四柱']
        
        for i, ganzhi1 in enumerate(pillars):
            for j, ganzhi2 in enumerate(pillars):
                if i >= j:
                    continue
                
                gan1, zhi1 = ganzhi1[0], ganzhi1[1]
                gan2, zhi2 = ganzhi2[0], ganzhi2[1]
                
                if gan1 in TIAN_GAN_RELATION:
                    rel = TIAN_GAN_RELATION[gan1]
                    if gan2 == rel['生']:
                        gan_relations.append(f'{gan1}生{gan2}')
                    elif gan2 == rel['克']:
                        gan_relations.append(f'{gan1}克{gan2}')
                    elif gan2 == rel['被生']:
                        gan_relations.append(f'{gan1}被{gan2}生')
                    elif gan2 == rel['被克']:
                        gan_relations.append(f'{gan1}被{gan2}克')
                
                if zhi1 in DI_ZHI_RELATION:
                    rel = DI_ZHI_RELATION[zhi1]
                    if zhi2 == rel['冲']:
                        zhi_relations.append(f'{zhi1}冲{zhi2}')
                    elif zhi2 == rel['合']:
                        zhi_relations.append(f'{zhi1}合{zhi2}')
                    elif zhi2 == rel['害']:
                        zhi_relations.append(f'{zhi1}害{zhi2}')
                    elif zhi2 == rel['刑']:
                        zhi_relations.append(f'{zhi1}刑{zhi2}')
        
        return {
            'gan_relations': list(set(gan_relations)),
            'zhi_relations': list(set(zhi_relations))
        }

    def analyze_self_seat(self, bazhi):
        day_ganzhi = bazhi['day']
        day_gan = day_ganzhi[0]
        day_zhi = day_ganzhi[1]
        
        day_gan_wx = TIAN_GAN_WUXING.get(day_gan, '')
        day_zhi_wx = DI_ZHI_WUXING.get(day_zhi, '')
        
        relationship = ''
        if day_gan_wx == day_zhi_wx:
            relationship = '比和'
        elif self._is_wuxing_relationship(day_gan_wx, day_zhi_wx, '生'):
            relationship = '生日'
        elif self._is_wuxing_relationship(day_zhi_wx, day_gan_wx, '生'):
            relationship = '日生'
        elif self._is_wuxing_relationship(day_gan_wx, day_zhi_wx, '克'):
            relationship = '日克'
        elif self._is_wuxing_relationship(day_zhi_wx, day_gan_wx, '克'):
            relationship = '克日'
        
        hidden_gans = DI_ZHI_HIDDEN_GAN.get(day_zhi, [])
        
        descriptions = []
        descriptions.append(f'日主{day_gan}({day_gan_wx})，自坐{day_zhi}({day_zhi_wx})')
        descriptions.append(f'日支与日主关系：{relationship}')
        
        if hidden_gans:
            hidden_desc = []
            for hg in hidden_gans:
                hg_wx = TIAN_GAN_WUXING.get(hg, '')
                hidden_desc.append(f'{hg}({hg_wx})')
            descriptions.append(f'日支藏干：{"、".join(hidden_desc)}')
        
        return {
            'day_gan': day_gan,
            'day_zhi': day_zhi,
            'relationship': relationship,
            'hidden_stems': hidden_gans,
            'description': '；'.join(descriptions)
        }

    def _is_wuxing_relationship(self, wx1, wx2, rel_type):
        wuxing_order = ['木', '火', '土', '金', '水']
        if wx1 not in wuxing_order or wx2 not in wuxing_order:
            return False
        
        idx1 = wuxing_order.index(wx1)
        idx2 = wuxing_order.index(wx2)
        
        if rel_type == '生':
            return (idx1 + 1) % 5 == idx2
        elif rel_type == '克':
            return (idx1 + 2) % 5 == idx2
        return False

    def analyze_kongwang(self, bazhi):
        year_ganzhi = bazhi['year']
        day_ganzhi = bazhi['day']
        
        year_kongwang = KONG_WANG_TABLE.get(year_ganzhi, [])
        day_kongwang = KONG_WANG_TABLE.get(day_ganzhi, [])
        
        affected_pillars = []
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        for i, ganzhi in enumerate(ganzhi_list):
            zhi = ganzhi[1]
            if zhi in year_kongwang or zhi in day_kongwang:
                affected_pillars.append({
                    'pillar': pillars[i],
                    'ganzhi': ganzhi,
                    'kongwang_type': '年空' if zhi in year_kongwang else '日空'
                })
        
        return {
            'year_kongwang': year_kongwang,
            'day_kongwang': day_kongwang,
            'affected_pillars': affected_pillars,
            'description': f'年空：{year_kongwang}；日空：{day_kongwang}'
        }

    def analyze_all(self, bazhi):
        return {
            'hidden_stems': self.analyze_hidden_stems(bazhi),
            'nayin': self.analyze_nayin(bazhi),
            'shensha': self.analyze_shensha(bazhi),
            'main_stars': self.analyze_main_stars(bazhi),
            'ganzhi_relations': self.analyze_ganzhi_relations(bazhi),
            'self_seat': self.analyze_self_seat(bazhi),
            'kongwang': self.analyze_kongwang(bazhi)
        }