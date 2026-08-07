"""命理分析模块 - 八字四柱的传统命理要素解读。

在四柱（年/月/日/时，各为一组干支）已排定之后，本模块负责把干支
翻译成命理师看得懂的结论，覆盖七大要素：

- 藏干：每个地支内部暗藏一到三个天干（本气/中气/余气），是判断
  日主强弱与十神的隐性力量来源；
- 纳音：六十甲子每两柱一组，配一个"纳音五行"（如"海中金"），
  是有别于干支本身五行的另一套象征体系；
- 神煞：桃花、驿马、天德等吉凶星曜，按天干或地支的固定口诀查表命中；
- 主星：借用紫微斗数十四主星的性格描述，按日主五行匹配；
- 干支关系：四柱两两之间的生、克、被生、被克（天干）与冲、合、害、
  刑（地支），是断吉凶与人际的主要依据；
- 自坐：日干（日主，即命主本人）与其所坐日支的关系，看命主根基；
- 空亡：六十甲子每一旬（10 组）必缺两个地支，缺的即"空亡"，
  落空亡的柱位主该方面事体虚耗、不实。

数据来源：MySQL 数据库（经 DatabaseManager 访问），模块级采用懒加载，
首次调用 _lazy_init() 时才建立连接并把查表结果缓存到全局变量，
避免导入本模块就触发数据库 IO。
"""

from core.calendar_utils import TIAN_GAN, DI_ZHI
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING, DI_ZHI_HIDDEN_GAN
from core.database_manager import DatabaseManager


def _get_db():
    """获取数据库管理器实例，供本模块内部懒加载取数使用。

    Returns:
        DatabaseManager: 数据库访问对象。DatabaseManager 自身通常已做
            连接复用，这里每次新建仅为取一次数，不持有长连接。
    """
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
    """命理分析器：对已排好的八字四柱做藏干、纳音、神煞等七项解读。

    典型用法是构造一次实例后调用 analyze_all(bazhi) 拿到全部结论；
    也可按需单独调用某一项 analyze_xxx 方法。

    入参 bazhi 是排盘层产出的字典，本类会用到其中这几个键：
        '四柱':  ['年柱干支', '月柱干支', '日柱干支', '时柱干支']，各为两字字符串
        'year'/'month'/'day'/'hour': 同上四柱的英文键写法
        'rizhu': 日干（单个天干字），即"日主"，代表命主本人
    不同方法用到的键不同（历史遗留的两套命名并存），使用时需保证对应键存在。
    """

    def __init__(self):
        """初始化分析器：触发数据库懒加载并建立干支到序号的索引表。"""
        # 先把纳音、神煞、干支关系、空亡等查表数据一次性载入模块级缓存，
        # 后续各 analyze_* 方法可直接读全局变量，无需再碰数据库
        _lazy_init()
        tg = TIAN_GAN
        dz = DI_ZHI
        # 天干/地支 -> 序号，供需要按位置做模运算的场景快速查找
        self.tian_gan_map = {t: i for i, t in enumerate(tg)}
        self.di_zhi_map = {d: i for i, d in enumerate(dz)}

    def analyze_hidden_stems(self, bazhi):
        """分析四柱地支藏干。

        地支并非单一五行，其内部"藏"着一到三个天干（本气/中气/余气），
        例如寅藏甲丙戊。藏干是判断日主旺衰、十神组合的隐性力量来源，
        排盘时必须显式列出。

        Args:
            bazhi: 排盘结果字典，需含 '四柱' 键（长度 4 的干支字符串列表，
                顺序为年、月、日、时）。

        Returns:
            dict: {'hidden_stems': [...]}，列表每项为
                {'pillar': 柱名, 'ganzhi': 该柱干支, 'hidden_stems': 藏干列表,
                 'description': '年柱地支寅藏干：甲(木)、丙(火)、戊(土)'}。
                无藏干记录的地支（理论上不存在）会被跳过，故列表长度可能小于 4。
        """
        result = []
        pillars = ['年柱', '月柱', '日柱', '时柱']
        
        for i, pillar in enumerate(pillars):
            ganzhi = bazhi['四柱'][i]
            # 干支为两字字符串，[0] 是天干、[1] 是地支；藏干只看地支
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
        """分析四柱纳音五行。

        纳音是六十甲子各自配定的一个五行别名（如甲子乙丑"海中金"），
        与干支本身的五行是两套并行体系：干支五行论旺衰生克，纳音多用于
        论命主气质、合婚与流年吉凶。

        Args:
            bazhi: 排盘结果字典，需含 'year'/'month'/'day'/'hour' 四个键，
                值为该柱的两字干支字符串。

        Returns:
            dict: 以 'year'/'month'/'day'/'hour' 为键，每项为
                {'pillar': 中文柱名, 'ganzhi': 干支, 'nayin': 纳音名,
                 'element': 纳音五行, 'description': 成句描述}。
                查不到纳音的干支降级为空字符串，不抛异常。
        """
        result = {}
        pillars = ['year', 'month', 'day', 'hour']
        pillar_names = ['年柱', '月柱', '日柱', '时柱']
        
        for i, pillar in enumerate(pillars):
            ganzhi = bazhi[pillar]
            # 纳音表以完整干支（如'甲子'）为键，取不到时降级为空，避免中断整盘
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
        """查找四柱命中的神煞，并按吉/凶/中性分类。

        神煞是附加在干支上的星曜标记（桃花、驿马、天德、劫煞等），
        每个神煞都有一句口诀式的查法，本质是"某天干（或某地支）见某地支
        即为命中"的查表规则，数据库中以 conditions 映射表存储。

        Args:
            bazhi: 排盘结果字典，需含 '四柱' 键（四组干支字符串）。

        Returns:
            dict: {'positive': [...], 'negative': [...], 'neutral': [...]}，
                三类分别是吉神、凶煞、中性神煞。每项含
                {'name','type','location'(命中的柱位),'ganzhi','description','detailed'}。
                同一神煞可能在多柱命中，会重复出现多条。
        """
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
        """按日主五行匹配紫微斗数主星，给出性格与运势倾向描述。

        这里不做真正的紫微排盘（不涉及命宫十二宫），只是借主星的性格
        断语做通俗化解读：取与日主（日干）五行相同的主星作为命主的
        代表星曜。

        Args:
            bazhi: 排盘结果字典，需含 'rizhu' 键（日干单字）。

        Returns:
            dict: {'stars': [{'name','element','characteristics','influence'}, ...]}。
        """
        rizhu = bazhi['rizhu']
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        stars = []
        for star_name, star_info in _MAIN_STARS.items():
            # 主星与日主同五行者，视为与命主气质相应
            if star_info['element'] == rizhu_wx:
                stars.append({
                    'name': star_name,
                    'element': star_info['element'],
                    'characteristics': star_info['characteristics'],
                    'influence': star_info['influence']
                })
        
        if not stars:
            # 日主五行缺失或无同五行主星时兜底取前三颗，保证 UI 不出现空白
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
        """分析四柱之间的天干关系与地支关系。

        天干之间论生、克、被生、被克（本质是五行相生相克链）；
        地支之间论冲、合、害、刑四种特殊关系：
        冲主变动对立，合主和谐结盟，害主暗中损伤，刑主刑伤官非。
        这些关系是断六亲、人际与吉凶应期的主要抓手。

        Args:
            bazhi: 排盘结果字典，需含 '四柱' 键（四组干支字符串）。

        Returns:
            dict: {'gan_relations': [...], 'zhi_relations': [...]}。
                每项含参与的两个柱名、两个干（或支）、关系名，以及取自
                _RELATION_DETAIL 的释义 detail_description 与吉凶断语 influence。
        """
        gan_relations = []
        zhi_relations = []
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        # 两两组合遍历四柱；i >= j 跳过是为了只取上三角，
        # 避免同一对柱位被正反各判一次而产生重复条目
        for i, ganzhi1 in enumerate(ganzhi_list):
            for j, ganzhi2 in enumerate(ganzhi_list):
                if i >= j:
                    continue
                
                gan1, zhi1 = ganzhi1[0], ganzhi1[1]
                gan2, zhi2 = ganzhi2[0], ganzhi2[1]
                
                # 天干关系：生/克/被生/被克 四者互斥（五行链上一个干只可能
                # 与另一个干构成其中一种关系），故用 elif 串联，命中即止
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
                
                # 地支关系：冲 > 合 > 害 > 刑 依次判定，同一对地支只记一种，
                # 优先级即此处 elif 的书写顺序（冲的力量最显著故排首位）
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
        """分析日主"自坐"，即日干与其所坐日支的关系。

        日柱天干为"日主"（命主本人），其下所坐的地支称"自坐"，
        二者五行关系直接反映命主的根基与自我处境：
            比和 - 干支同五行，根基稳固；
            生日 - 日主生日支，主付出耗泄；
            日生 - 日支生日主，主自身得养（坐印，最为有力）；
            日克 - 日主克日支，主掌控（坐财）；
            克日 - 日支克日主，主受制（坐煞）。

        Args:
            bazhi: 排盘结果字典，需含 'day' 键（日柱两字干支字符串）。

        Returns:
            dict: {'day_gan','day_zhi','relationship'(上述五种之一，
                均不匹配时为空串), 'hidden_stems'(日支藏干列表),
                'description'(以分号连接的成句描述)}。
        """
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
        """判断两个五行之间是否成立指定的生或克关系（单向）。

        供 analyze_self_seat 判定日主与自坐的关系时调用，是本类内部的
        五行运算基础工具。实现依赖"木火土金水"这个固定排列的性质：
        按此序相邻者为相生（木生火），相隔一位者为相克（木克土）。

        Args:
            wx1: 主动方五行，取 '木'/'火'/'土'/'金'/'水' 之一。
            wx2: 受动方五行，取值同上。
            rel_type: '生' 判断 wx1 是否生 wx2；'克' 判断 wx1 是否克 wx2。

        Returns:
            bool: 关系成立返回 True。任一五行非法或 rel_type 不识别时返回 False。
        """
        wuxing_order = ['木', '火', '土', '金', '水']
        if wx1 not in wuxing_order or wx2 not in wuxing_order:
            return False
        
        idx1 = wuxing_order.index(wx1)
        idx2 = wuxing_order.index(wx2)
        
        if rel_type == '生':
            # 相生链：序列上的下一位即我所生（木->火->土->金->水->木）
            return (idx1 + 1) % 5 == idx2
        elif rel_type == '克':
            # 相克链：隔一位即我所克（木->土->水->火->金->木）
            return (idx1 + 2) % 5 == idx2
        return False

    def analyze_kongwang(self, bazhi):
        """分析空亡（旬空）：哪些柱位落入年柱、日柱所在旬的空亡地支。

        天干十个、地支十二个，两两相配成一旬（10 组干支）时必然多出两个
        地支配不上天干，这两个"落单"的地支就是该旬的空亡。四柱中若有
        地支正好落在空亡上，主该柱所代表的人事（年柱祖上、月柱父母兄弟、
        日柱配偶、时柱子女）虚而不实、易成空。

        习惯上以年柱和日柱两个旬分别取空亡，故有"年空"与"日空"之别。

        Args:
            bazhi: 排盘结果字典，需含 'year'、'day' 两键（干支字符串）
                以及 '四柱' 键（四组干支，用于逐柱比对）。

        Returns:
            dict: {'year_kongwang': 年空二支, 'day_kongwang': 日空二支,
                'affected_pillars': [{'pillar','ganzhi','kongwang_type'}, ...],
                'description': 概要文案}。
        """
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
                    # 同时落年空与日空时标为"年空"，即年柱旬的判定优先
                    'kongwang_type': '年空' if zhi in year_kongwang else '日空'
                })
        
        return {
            'year_kongwang': year_kongwang,
            'day_kongwang': day_kongwang,
            'affected_pillars': affected_pillars,
            'description': f'年空：{year_kongwang}；日空：{day_kongwang}'
        }

    def analyze_all(self, bazhi):
        """一次性执行全部七项命理分析，返回汇总结果。

        这是本类对外的主入口，UI 层与 AI 解读层通常只调用此方法。

        Args:
            bazhi: 排盘结果字典。因为要跑齐所有子分析，需同时具备
                '四柱'、'year'/'month'/'day'/'hour'、'rizhu' 这几个键。

        Returns:
            dict: 七个子分析的结果，键为
                'hidden_stems'(藏干)、'nayin'(纳音)、'shensha'(神煞)、
                'main_stars'(主星)、'ganzhi_relations'(干支关系)、
                'self_seat'(自坐)、'kongwang'(空亡)，
                各值的结构见对应 analyze_* 方法的说明。
        """
        return {
            'hidden_stems': self.analyze_hidden_stems(bazhi),
            'nayin': self.analyze_nayin(bazhi),
            'shensha': self.analyze_shensha(bazhi),
            'main_stars': self.analyze_main_stars(bazhi),
            'ganzhi_relations': self.analyze_ganzhi_relations(bazhi),
            'self_seat': self.analyze_self_seat(bazhi),
            'kongwang': self.analyze_kongwang(bazhi)
        }
