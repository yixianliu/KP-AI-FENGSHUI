from core.calendar_utils import TIAN_GAN, DI_ZHI
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING, DI_ZHI_HIDDEN_GAN
from core.database_manager import DatabaseManager


def _get_db():
    return DatabaseManager()


# ---- 懒加载变量（从数据库加载） ----
_NAYIN_MAP = None
_SHEN_SHA = None
_MAIN_STARS = None
_TIAN_GAN_RELATION = None
_RELATION_DETAIL = None
_DI_ZHI_RELATION = None
_KONG_WANG_TABLE = None


def _lazy_init():
    """懒加载初始化，从数据库加载所有数据"""
    global _NAYIN_MAP, _SHEN_SHA, _MAIN_STARS, _TIAN_GAN_RELATION
    global _RELATION_DETAIL, _DI_ZHI_RELATION, _KONG_WANG_TABLE
    if _NAYIN_MAP is not None:
        return
    db = _get_db()
    _NAYIN_MAP = db.get_nayin_wuxing()
    _SHEN_SHA = db.get_shensha_for_calculation()
    _MAIN_STARS = _get_default_main_stars()
    _TIAN_GAN_RELATION = _compute_tian_gan_relation(db)
    _RELATION_DETAIL = _get_default_relation_detail()
    _DI_ZHI_RELATION = _compute_di_zhi_relation(db)
    _KONG_WANG_TABLE = _compute_kong_wang_table(db)


def _get_default_main_stars() -> dict:
    """返回主星默认数据（14主星的信息，也可后续存入数据库）"""
    return {
        '紫微': {'characteristics': '紫微为帝星，主尊贵、权威、领导力', 'influence': '具有领导才能，容易成为领袖人物，一生运势较强', 'element': '土'},
        '天府': {'characteristics': '天府为财库，主财富、稳重、保守', 'influence': '财运较好，善于理财，但有时过于保守', 'element': '土'},
        '太阳': {'characteristics': '太阳主光明、热情、正直', 'influence': '性格开朗，乐于助人，事业上容易得到他人帮助', 'element': '火'},
        '太阴': {'characteristics': '太阴主温柔、细腻、智慧', 'influence': '心思细腻，富有艺术才华，适合从事文艺工作', 'element': '水'},
        '贪狼': {'characteristics': '贪狼主欲望、才华、交际', 'influence': '多才多艺，社交能力强，但需注意节制欲望', 'element': '木'},
        '巨门': {'characteristics': '巨门主口才、是非、谋略', 'influence': '善于言辞，适合从事律师、教师等职业', 'element': '水'},
        '天相': {'characteristics': '天相主相貌、辅佐、正直', 'influence': '相貌端正，善于辅佐他人，适合做幕僚', 'element': '水'},
        '天梁': {'characteristics': '天梁主荫庇、延寿、清高', 'influence': '一生多福气，容易得到长辈相助', 'element': '土'},
        '七杀': {'characteristics': '七杀主刚强、果断、权威', 'influence': '性格刚强，做事果断，但需注意脾气', 'element': '金'},
        '破军': {'characteristics': '破军主变革、开创、破坏', 'influence': '具有开创精神，但有时过于冲动', 'element': '水'},
        '廉贞': {'characteristics': '廉贞主清廉、固执、桃花', 'influence': '为人正直，但有时过于固执', 'element': '火'},
        '武曲': {'characteristics': '武曲主财富、武勇、果断', 'influence': '财运旺盛，适合经商或从军', 'element': '金'}
    }


def _get_default_relation_detail() -> dict:
    """返回干支关系详细说明"""
    return {
        '生': {'description': '相生关系，主帮助、支持、生扶', 'influence': '相生为吉，主得到他人帮助，事情顺利发展'},
        '克': {'description': '相克关系，主制约、管制、压制', 'influence': '相克为凶，主压力、阻碍、冲突'},
        '被生': {'description': '被生关系，主受生扶、得滋养', 'influence': '被生为吉，主得到贵人相助，受益于他人'},
        '被克': {'description': '被克关系，主受制约、受压制', 'influence': '被克为凶，主遭遇压制，诸事不顺'},
        '冲': {'description': '相冲关系，主对立、冲突、变动', 'influence': '相冲为凶，主变动大、冲突多、人际关系紧张'},
        '合': {'description': '相合关系，主和谐、合作、吸引', 'influence': '相合为吉，主人际关系好、合作顺利、感情融洽'},
        '害': {'description': '相害关系，主伤害、陷害、暗中破坏', 'influence': '相害为凶，主小人陷害、暗中伤害、是非纠纷'},
        '刑': {'description': '相刑关系，主刑罚、伤害、疾病', 'influence': '相刑为凶，主官司诉讼、疾病缠身、意外伤害'}
    }


def _compute_tian_gan_relation(db) -> dict:
    """根据天干五行计算天干之间的生克被生被克关系"""
    wuxing_sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    wuxing_ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    # 反向：谁生我、谁克我
    wuxing_bei_sheng = {v: k for k, v in wuxing_sheng.items()}
    wuxing_bei_ke = {v: k for k, v in wuxing_ke.items()}

    gan_wuxing = db.get_tian_gan_wuxing()
    tian_gan = db.get_tian_gan_list()

    result = {}
    for gan1 in tian_gan:
        wx1 = gan_wuxing.get(gan1, '')
        if not wx1:
            continue
        result[gan1] = {}
        # 我生：五行相生链中我的下一个
        target_wx = wuxing_sheng.get(wx1)
        for gan2 in tian_gan:
            if gan_wuxing.get(gan2) == target_wx:
                result[gan1]['生'] = gan2
                break
        # 我克：五行相克链中我克的那个
        target_wx = wuxing_ke.get(wx1)
        for gan2 in tian_gan:
            if gan_wuxing.get(gan2) == target_wx:
                result[gan1]['克'] = gan2
                break
        # 被生：谁生我
        target_wx = wuxing_bei_sheng.get(wx1)
        for gan2 in tian_gan:
            if gan_wuxing.get(gan2) == target_wx:
                result[gan1]['被生'] = gan2
                break
        # 被克：谁克我
        target_wx = wuxing_bei_ke.get(wx1)
        for gan2 in tian_gan:
            if gan_wuxing.get(gan2) == target_wx:
                result[gan1]['被克'] = gan2
                break
    return result


def _compute_di_zhi_relation(db) -> dict:
    """从数据库的地支合冲害刑表计算地支关系映射 {zhi: {冲: zhi, 合: zhi, 害: zhi, 刑: zhi}}"""
    di_zhi = db.get_di_zhi_list()
    result = {z: {} for z in di_zhi}

    # 六冲
    chong_rows = db._query_all("SELECT zhi_pair FROM di_zhi_chong")
    for r in chong_rows:
        pair = r['zhi_pair']
        if len(pair) == 2:
            result[pair[0]]['冲'] = pair[1]
            result[pair[1]]['冲'] = pair[0]

    # 六合
    he_rows = db._query_all("SELECT zhi_pair FROM di_zhi_he")
    for r in he_rows:
        pair = r['zhi_pair']
        if len(pair) == 2:
            result[pair[0]]['合'] = pair[1]
            result[pair[1]]['合'] = pair[0]

    # 六害
    hai_rows = db._query_all("SELECT zhi_pair FROM di_zhi_hai")
    for r in hai_rows:
        pair = r['zhi_pair']
        if len(pair) == 2:
            result[pair[0]]['害'] = pair[1]
            result[pair[1]]['害'] = pair[0]

    # 相刑（取第一个相刑的地支）
    xing_rows = db._query_all("SELECT zhi_group FROM di_zhi_xing")
    for r in xing_rows:
        group = r['zhi_group']
        if len(group) >= 2:
            for i, zhi in enumerate(group):
                if '刑' not in result[zhi]:
                    # 取下一个地支作为刑的对象
                    next_zhi = group[(i + 1) % len(group)]
                    result[zhi]['刑'] = next_zhi

    return result


def _compute_kong_wang_table(db) -> dict:
    """计算六十甲子的空亡表 {ganzhi: [kongwang_zhi1, kongwang_zhi2]}"""
    # 空亡规则：每旬（10组甲子）空亡该旬中缺失的两个地支
    jiazi = db.get_sixty_jiazi()
    di_zhi = db.get_di_zhi_list()

    result = {}
    for xun_start in range(0, 60, 10):
        xun_jiazi = jiazi[xun_start:xun_start + 10]
        # 找到该旬中已有的地支
        used_zhi = set()
        for gz in xun_jiazi:
            used_zhi.add(gz[1])
        # 找出缺失的两个地支
        kongwang = [z for z in di_zhi if z not in used_zhi]
        for gz in xun_jiazi:
            result[gz] = kongwang[:2]
    return result

class MingLiAnalyzer:
    def __init__(self):
        _lazy_init()
        tg = TIAN_GAN
        dz = DI_ZHI
        self.tian_gan_map = {t: i for i, t in enumerate(tg)}
        self.di_zhi_map = {d: i for i, d in enumerate(dz)}

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
            nayin_info = _NAYIN_MAP.get(ganzhi, ('', ''))
            
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
        neutral = []
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        for sha_name, sha_info in _SHEN_SHA.items():
            conditions = sha_info['conditions']
            sha_type = sha_info.get('type', 'neutral')
            
            for i, ganzhi in enumerate(ganzhi_list):
                gan = ganzhi[0]
                zhi = ganzhi[1]

                matched = False
                # 检查天干条件（如天德、文昌等按天干查找）
                if gan in conditions:
                    if zhi in conditions[gan]:
                        matched = True
                # 检查地支条件（如桃花、驿马等按地支查找）
                if not matched and zhi in conditions:
                    if gan in conditions[zhi] or zhi in conditions[zhi]:
                        matched = True

                if matched:
                    entry = {
                        'name': sha_name,
                        'type': sha_type,
                        'location': pillars[i],
                        'ganzhi': ganzhi,
                        'description': sha_info['description'],
                        'detailed': sha_info.get('detailed', '')
                    }
                    if sha_type == 'positive':
                        positive.append(entry)
                    elif sha_type == 'negative':
                        negative.append(entry)
                    else:
                        neutral.append(entry)
        
        return {'positive': positive, 'negative': negative, 'neutral': neutral}

    def analyze_main_stars(self, bazhi):
        rizhu = bazhi['rizhu']
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        stars = []
        for star_name, star_info in _MAIN_STARS.items():
            if star_info['element'] == rizhu_wx:
                stars.append({
                    'name': star_name,
                    'element': star_info['element'],
                    'characteristics': star_info['characteristics'],
                    'influence': star_info['influence']
                })
        
        if not stars:
            star_list = list(_MAIN_STARS.keys())[:3]
            for star_name in star_list:
                stars.append({
                    'name': star_name,
                    'element': _MAIN_STARS[star_name]['element'],
                    'characteristics': _MAIN_STARS[star_name]['characteristics'],
                    'influence': _MAIN_STARS[star_name]['influence']
                })
        
        return {'stars': stars}

    def analyze_ganzhi_relations(self, bazhi):
        gan_relations = []
        zhi_relations = []
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        for i, ganzhi1 in enumerate(ganzhi_list):
            for j, ganzhi2 in enumerate(ganzhi_list):
                if i >= j:
                    continue
                
                gan1, zhi1 = ganzhi1[0], ganzhi1[1]
                gan2, zhi2 = ganzhi2[0], ganzhi2[1]
                
                if gan1 in _TIAN_GAN_RELATION:
                    rel = _TIAN_GAN_RELATION[gan1]
                    if gan2 == rel['生']:
                        detail = _RELATION_DETAIL.get('生', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '生',
                            'description': f'{gan1}生{gan2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif gan2 == rel['克']:
                        detail = _RELATION_DETAIL.get('克', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '克',
                            'description': f'{gan1}克{gan2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif gan2 == rel['被生']:
                        detail = _RELATION_DETAIL.get('被生', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '被生',
                            'description': f'{gan1}被{gan2}生',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif gan2 == rel['被克']:
                        detail = _RELATION_DETAIL.get('被克', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '被克',
                            'description': f'{gan1}被{gan2}克',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                
                if zhi1 in _DI_ZHI_RELATION:
                    rel = _DI_ZHI_RELATION[zhi1]
                    if zhi2 == rel.get('冲'):
                        detail = _RELATION_DETAIL.get('冲', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '冲',
                            'description': f'{zhi1}冲{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif zhi2 == rel.get('合'):
                        detail = _RELATION_DETAIL.get('合', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '合',
                            'description': f'{zhi1}合{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif zhi2 == rel.get('害'):
                        detail = _RELATION_DETAIL.get('害', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '害',
                            'description': f'{zhi1}害{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif zhi2 == rel.get('刑'):
                        detail = _RELATION_DETAIL.get('刑', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '刑',
                            'description': f'{zhi1}刑{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
        
        return {
            'gan_relations': gan_relations,
            'zhi_relations': zhi_relations
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
        
        year_kongwang = _KONG_WANG_TABLE.get(year_ganzhi, [])
        day_kongwang = _KONG_WANG_TABLE.get(day_ganzhi, [])
        
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
