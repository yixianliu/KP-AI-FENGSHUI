"""
梅花易数卦象分析与爻辞解读系统
包含八卦基础数据、64卦卦辞爻辞、吉凶判断及解卦分析
先天八卦数：乾1、兑2、离3、震4、巽5、坎6、艮7、坤8
数据来源：本地 SQLite（data/fengshui.db）
"""
from core.database_manager import DatabaseManager
from core.hexagram_data import GAN_YAO_FULL


def _get_db():
    """获取数据库管理器实例，用于后续八卦/64卦数据查询。"""
    return DatabaseManager()


def _get_bagua():
    """从数据库读取八卦基础数据，返回以先天数（1-8）为键的字典。"""
    return _get_db().get_ba_gua()


# 兼容旧代码的惰性加载
class _LazyBagua:
    """八卦数据的惰性加载容器，首次访问时才从数据库读取并缓存，避免无谓查询。"""
    def __init__(self):
        """初始化空缓存，实际数据在首次访问时由 _load 加载。"""
        self._data = None

    def _load(self):
        """从数据库加载八卦（乾兑离震巽坎艮坤）数据并缓存，重复调用只加载一次。"""
        if self._data is None:
            db_data = _get_bagua()
            self._data = {}
            for num, info in db_data.items():
                self._data[num] = {
                    'name': info['name'],
                    'nature': info['nature'],
                    'symbol': info['symbol'],
                    'wuxing': info['wuxing'],
                    'description': info['description']
                }
        return self._data

    def __getitem__(self, key):
        """支持下标访问，触发懒加载后返回对应先天数的八卦信息。"""
        return self._load()[key]

    def get(self, key, default=None):
        """兼容 dict.get：缺失键时返回 default。"""
        return self._load().get(key, default)

    def items(self):
        """返回 (先天数, 八卦信息) 的视图，便于遍历。"""
        return self._load().items()

    def keys(self):
        """返回所有先天数键的视图。"""
        return self._load().keys()

    def values(self):
        """返回所有八卦信息值的视图。"""
        return self._load().values()

    def __iter__(self):
        """支持 for 循环按先天数遍历八卦。"""
        return iter(self._load())

    def __len__(self):
        """返回八卦总数（正常为 8）。"""
        return len(self._load())

    def __contains__(self, key):
        """支持 in 运算符，判断某先天数是否已有八卦数据。"""
        return key in self._load()


class _LazyHexagrams:
    """兼容旧代码的HEXAGRAMS字典 - 从数据库加载"""
    def __init__(self):
        """初始化空缓存，64卦数据在首次访问时懒加载。"""
        self._data = None

    def _load(self):
        """从数据库加载64卦完整数据（卦名/卦辞/爻辞等）并按 (上卦,下卦) 缓存。"""
        if self._data is None:
            self._data = {}
            # 旧版以 hexagram_id 为键的数据已废弃，此处仅为兼容占位，不再处理
            for key, info in GAN_YAO_FULL.items():
                # key 为 hexagram_id（整数），但本容器以 (上卦,下卦) 元组为键，故跳过
                pass
            # 以 (上卦先天数, 下卦先天数) 为键从数据库加载64卦
            db = _get_db()
            rows = db.get_hexagram_64()
            for (upper, lower), info in rows.items():
                hex_id = info['hexagram_id']
                yao_list = db.get_hexagram_yao_ci(hex_id)
                yao_ci = []
                # 逐爻提取爻名、爻辞原文与释义，组装该卦的爻辞列表
                for yao in yao_list:
                    yao_ci.append({
                        'yao': yao['yao_name'],
                        'text': yao['yao_text'],
                        'meaning': yao['meaning']
                    })
                self._data[(upper, lower)] = {
                    'name': info['name'],
                    'judgment': info['judgment'],
                    'gua_ci': info['gua_ci'],
                    'description': info['description'],
                    'yao_ci': yao_ci
                }
        return self._data

    def __getitem__(self, key):
        """按 (上卦,下卦) 先天数元组取下卦完整信息，触发懒加载。"""
        return self._load()[key]

    def get(self, key, default=None):
        """兼容 dict.get：缺失键时返回 default。"""
        return self._load().get(key, default)

    def items(self):
        """返回 ((上卦,下卦), 卦信息) 的视图。"""
        return self._load().items()

    def keys(self):
        """返回所有 (上卦,下卦) 键的视图。"""
        return self._load().keys()

    def values(self):
        """返回所有64卦信息值的视图。"""
        return self._load().values()

    def __iter__(self):
        """遍历所有 (上卦,下卦) 键。"""
        return iter(self._load())

    def __len__(self):
        """返回64卦总数（正常为 64）。"""
        return len(self._load())

    def __contains__(self, key):
        """判断某 (上卦,下卦) 组合是否存在。"""
        return key in self._load()


BAGUA = _LazyBagua()
HEXAGRAMS = _LazyHexagrams()


class HexagramAnalyzer:
    """卦象分析器 - 解读卦象、爻辞及吉凶判断"""

    def __init__(self):
        """初始化分析器，绑定八卦与64卦的惰性加载数据源。"""
        self.bagua = BAGUA
        self.hexagrams = HEXAGRAMS

    def get_bagua_info(self, num):
        """获取八卦单卦信息"""
        return self.bagua.get(num, {'name': '未知', 'nature': '', 'symbol': '', 'wuxing': '', 'description': ''})

    def get_hexagram_info(self, upper_num, lower_num):
        """获取64卦完整信息"""
        key = (upper_num, lower_num)
        return self.hexagrams.get(key, {
            'name': '未知卦',
            'judgment': '平',
            'gua_ci': '',
            'description': '',
            'yao_ci': []
        })

    def analyze_divination(self, divination_result, all_hexagrams):
        """
        分析完整的起卦结果
        返回本卦、互卦、变卦、错卦、综卦的详细分析及综合判断
        """
        base_upper = divination_result['upper_num']
        base_lower = divination_result['lower_num']
        changing_yao = divination_result['changing_yao']
        question = divination_result.get('question', '')

        base_info = self.get_hexagram_info(base_upper, base_lower)

        # 派生四卦：变卦(爻变后之卦)、互卦(二至四/三至五爻所成)、错卦(六爻全反)、综卦(整卦颠倒)
        bi_upper = self._extract_hex_num(all_hexagrams['bian']['upper_yangs'])
        bi_lower = self._extract_hex_num(all_hexagrams['bian']['lower_yangs'])
        bi_info = self.get_hexagram_info(bi_upper, bi_lower)

        hu_upper = self._extract_hex_num(all_hexagrams['hu']['upper_yangs'])
        hu_lower = self._extract_hex_num(all_hexagrams['hu']['lower_yangs'])
        hu_info = self.get_hexagram_info(hu_upper, hu_lower)

        cuo_upper = self._extract_hex_num(all_hexagrams['cuo']['upper_yangs'])
        cuo_lower = self._extract_hex_num(all_hexagrams['cuo']['lower_yangs'])
        cuo_info = self.get_hexagram_info(cuo_upper, cuo_lower)

        zong_upper = self._extract_hex_num(all_hexagrams['zong']['upper_yangs'])
        zong_lower = self._extract_hex_num(all_hexagrams['zong']['lower_yangs'])
        zong_info = self.get_hexagram_info(zong_upper, zong_lower)

        yao_text = ''
        yao_meaning = ''
        yao_name = ''
        yao_ci_list = base_info.get('yao_ci', [])
        if yao_ci_list and changing_yao <= len(yao_ci_list):
            yao_data = yao_ci_list[changing_yao - 1]
            yao_name = yao_data.get('yao', '')
            yao_text = yao_data.get('text', '')
            yao_meaning = yao_data.get('meaning', '')

        judgment = self._make_judgment(base_info, bi_info, changing_yao)
        suggestions = self._generate_suggestions(base_info, bi_info, judgment, question)

        return {
            'question': question,
            'base': {
                'name': base_info.get('name', ''),
                'upper_num': base_upper,
                'lower_num': base_lower,
                'upper_name': self.get_bagua_info(base_upper)['name'],
                'lower_name': self.get_bagua_info(base_lower)['name'],
                'upper_element': self.get_bagua_info(base_upper)['wuxing'],
                'lower_element': self.get_bagua_info(base_lower)['wuxing'],
                'upper_nature': self.get_bagua_info(base_upper)['nature'],
                'lower_nature': self.get_bagua_info(base_lower)['nature'],
                'upper_symbol': self.get_bagua_info(base_upper)['symbol'],
                'lower_symbol': self.get_bagua_info(base_lower)['symbol'],
                'description': base_info.get('description', ''),
                'judgment': base_info.get('judgment', ''),
                'gua_ci': base_info.get('gua_ci', ''),
                'yao_ci': yao_ci_list,
                'changing_yao': changing_yao,
                'changing_yao_name': yao_name,
                'changing_yao_text': yao_text,
                'changing_yao_meaning': yao_meaning
            },
            'hu': {
                'name': hu_info.get('name', ''),
                'upper_num': hu_upper,
                'lower_num': hu_lower,
                'description': hu_info.get('description', '')
            },
            'bian': {
                'name': bi_info.get('name', ''),
                'upper_num': bi_upper,
                'lower_num': bi_lower,
                'description': bi_info.get('description', ''),
                'judgment': bi_info.get('judgment', '')
            },
            'cuo': {
                'name': cuo_info.get('name', ''),
                'upper_num': cuo_upper,
                'lower_num': cuo_lower,
                'description': cuo_info.get('description', '')
            },
            'zong': {
                'name': zong_info.get('name', ''),
                'upper_num': zong_upper,
                'lower_num': zong_lower,
                'description': zong_info.get('description', '')
            },
            'overall_judgment': judgment,
            'suggestions': suggestions,
            'wuxing_analysis': self._analyze_wuxing(base_upper, base_lower, bi_upper, bi_lower)
        }

    def _extract_hex_num(self, yangs):
        """从爻信息提取卦的先天数（二进制转十进制+1）"""
        num = 0
        # 三爻由下而上构成三位二进制：阳爻记 1、阴爻记 0，再整体 +1
        # 得到 1-8，对应先天八卦数 乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
        for yao in yangs:
            num = num * 2 + (1 if yao['symbol_short'] == '阳' else 0)
        num = num + 1
        if num < 1:
            num = 1
        elif num > 8:
            num = num % 8
            if num == 0:
                num = 8
        return num

    def _make_judgment(self, base_info, bi_info, changing_yao):
        """综合判断吉凶"""
        base_judgment = base_info.get('judgment', '平')
        bi_judgment = bi_info.get('judgment', '平')

        judgments = {'吉': 2, '平': 1, '凶': 0}
        base_score = judgments.get(base_judgment, 1)
        bi_score = judgments.get(bi_judgment, 1)

        total_score = base_score + bi_score

        if total_score >= 3:
            return '吉'
        elif total_score >= 2:
            return '平'
        else:
            return '凶'

    def _generate_suggestions(self, base_info, bi_info, judgment, question=''):
        """生成趋吉避凶建议"""
        suggestions = []

        if judgment == '吉':
            suggestions.append('运势吉利，宜积极进取，把握良机。')
            suggestions.append('保持谦虚谨慎，善始善终，不可骄傲自满。')
        elif judgment == '平':
            suggestions.append('运势平稳，宜稳扎稳打，不宜冒进。')
            suggestions.append('耐心等待时机，做好准备工作，厚积薄发。')
        else:
            suggestions.append('运势不佳，宜守静不动，避免冒险。')
            suggestions.append('反思自身问题，寻求贵人相助，积德行善。')

        base_name = base_info.get('name', '')
        base_desc = base_info.get('description', '')

        if '乾' in base_name or '刚健' in base_desc:
            suggestions.append('宜发挥刚健进取精神，但需避免过刚易折。')
        if '坤' in base_name or '柔顺' in base_desc:
            suggestions.append('宜以柔克刚，厚德载物，包容忍让。')
        if '屯' in base_name or '艰难' in base_desc:
            suggestions.append('当前处于困难阶段，需坚定信念，逐步积累，厚积薄发。')
        if '蒙' in base_name or '启蒙' in base_desc:
            suggestions.append('宜虚心学习，请教明师，勿自以为是。')
        if '需' in base_name or '等待' in base_desc:
            suggestions.append('宜耐心等待时机，不可急于求成。')
        if '讼' in base_name or '争讼' in base_desc:
            suggestions.append('宜避免口舌争端，退一步海阔天空。')
        if '师' in base_name or '军队' in base_desc:
            suggestions.append('宜有组织有纪律，谋定而后动。')
        if '比' in base_name or '亲比' in base_desc:
            suggestions.append('宜广结善缘，与人为善，得道多助。')

        bi_desc = bi_info.get('description', '')
        bi_judgment_val = bi_info.get('judgment', '')

        if bi_judgment_val == '吉' or '吉' in bi_desc:
            suggestions.append('未来趋势向好，坚持努力终将成功。')
        elif bi_judgment_val == '凶':
            suggestions.append('未来需谨慎行事，提前做好防范措施。')

        if question:
            suggestions.append(f'针对所问「{question}」，需结合实际情况灵活应对。')

        return suggestions

    def _analyze_wuxing(self, base_upper, base_lower, bi_upper, bi_lower):
        """五行生克分析"""
        db = _get_db()
        wx_relations = db.get_wuxing_relations()
        
        # 从数据库构建生克映射
        wuxing_sheng = {}
        wuxing_ke = {}
        if 'sheng' in wx_relations:
            for rel in wx_relations['sheng']['relations']:
                wuxing_sheng[rel['from']] = rel['to']
        if 'ke' in wx_relations:
            for rel in wx_relations['ke']['relations']:
                wuxing_ke[rel['from']] = rel['to']

        base_upper_wx = self.get_bagua_info(base_upper)['wuxing']
        base_lower_wx = self.get_bagua_info(base_lower)['wuxing']
        bi_upper_wx = self.get_bagua_info(bi_upper)['wuxing']
        bi_lower_wx = self.get_bagua_info(bi_lower)['wuxing']

        def get_relation(a, b):
            """判断五行 a 对 b 的生克关系：比和/我生/生我/我克/克我/未知。"""
            if a == b:
                return '比和'
            elif wuxing_sheng.get(a) == b:
                return '我生'
            elif wuxing_sheng.get(b) == a:
                return '生我'
            elif wuxing_ke.get(a) == b:
                return '我克'
            elif wuxing_ke.get(b) == a:
                return '克我'
            return '未知'

        return {
            'base_upper_wuxing': base_upper_wx,
            'base_lower_wuxing': base_lower_wx,
            'base_relation': get_relation(base_upper_wx, base_lower_wx),
            'bian_upper_wuxing': bi_upper_wx,
            'bian_lower_wuxing': bi_lower_wx,
            'bian_relation': get_relation(bi_upper_wx, bi_lower_wx)
        }
