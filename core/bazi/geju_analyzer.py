"""
格局判定模块 - 补齐格局分支
包含身强身弱、从格、专旺、合化、冲克制衡全部判定逻辑

修复内容：
1. 身强/身弱判定：基于五行能量、月令、通根综合判断
2. 从格判定：从财、从官杀、从儿、从势
3. 专旺格判定：曲直、炎上、稼穑、从革、润下
4. 合化格判定：天干五合、地支六合三合
5. 特殊格局：伤官见官、官杀混杂、财官双美等
"""
from core.calendar_utils import WuxingQuantifier
from core.database_manager import DatabaseManager


def _get_db():
    """返回 DatabaseManager 实例，供本模块惰性加载合化/冲刑/五行生克等参考数据。"""
    return DatabaseManager()


# 模块级变量，首次使用时加载
_TIAN_GAN_WUXING = None
_TIAN_GAN_HE = None
_DI_ZHI_HE = None
_DI_ZHI_SAN_HE = None
_DI_ZHI_CHONG = None
_DI_ZHI_XING = None
_TIAN_GAN_MAP = None


def _lazy_init():
    """首次调用时从数据库加载天干五行、五合、地支六合/三合/冲/刑/天干序号等基础表；之后幂等。"""
    global _TIAN_GAN_WUXING, _TIAN_GAN_HE, _DI_ZHI_HE
    global _DI_ZHI_SAN_HE, _DI_ZHI_CHONG, _DI_ZHI_XING, _TIAN_GAN_MAP
    if _TIAN_GAN_WUXING is None:
        db = _get_db()
        _TIAN_GAN_WUXING = db.get_tian_gan_wuxing()
        _TIAN_GAN_HE = db.get_tian_gan_he()
        _DI_ZHI_HE = db.get_di_zhi_he()
        _DI_ZHI_SAN_HE = db.get_di_zhi_san_he()
        _DI_ZHI_CHONG = db.get_di_zhi_chong_map()
        _DI_ZHI_XING = db.get_di_zhi_xing_map()
        _TIAN_GAN_MAP = db.get_tian_gan_map()


# 保留旧模块级变量名称兼容性（内容已清空，实际通过 _lazy_init() 加载）
TIAN_GAN_WUXING = None
TIAN_GAN_HE = None
DI_ZHI_HE = None
DI_ZHI_SAN_HE = None
DI_ZHI_CHONG = None
DI_ZHI_XING = None


class GeJuAnalyzer:
    """格局判定分析器"""

    def __init__(self):
        """初始化时加载基础命理表，并持有五行量化器用于旺衰/能量计算。"""
        _lazy_init()
        self.wuxing_quantifier = WuxingQuantifier()

    def analyze(self, bazi, wuxing_result=None, month_zhi=None):
        """综合判定八字格局"""
        if wuxing_result is None:
            wuxing_result = self.wuxing_quantifier.analyze(bazi, month_zhi)
        
        wangshuai = self.wuxing_quantifier.analyze_wangshuai(bazi, month_zhi)
        
        geju_result = {
            'wangshuai': wangshuai,
            'main_geju': '',
            'geju_type': '',
            'description': '',
            'sub_geju': [],
            'hehua': [],
            'chongxing': [],
            'special_patterns': [],
            'analysis': ''
        }
        
        geju_result['main_geju'], geju_result['geju_type'], geju_result['description'] = self._judge_main_geju(bazi, wuxing_result, wangshuai)
        
        geju_result['hehua'] = self._analyze_hehua(bazi)
        geju_result['chongxing'] = self._analyze_chongxing(bazi)
        geju_result['special_patterns'] = self._analyze_special_patterns(bazi, wuxing_result, wangshuai)
        
        geju_result['analysis'] = self._generate_comprehensive_analysis(geju_result)
        
        return geju_result

    def _judge_main_geju(self, bazi, wuxing_result, wangshuai):
        """判定主格局"""
        sorted_wx = sorted(['木', '火', '土', '金', '水'],
                          key=lambda x: wuxing_result[x]['score'], reverse=True)
        max_wx = sorted_wx[0]

        if self._is_zhuanwang(bazi, wuxing_result):
            return self._get_zhuanwang_name(max_wx), '专旺格', self._get_zhuanwang_desc(max_wx)
        
        if self._is_congge(bazi, wuxing_result, wangshuai):
            return self._get_congge_name(bazi, wuxing_result), '从格', '日主极弱，顺从强势五行'
        
        if wangshuai['level'] == '身强':
            if self._is_sha_gong(bazi, wuxing_result):
                return '杀印相生格', '扶抑格', '身强用杀，印化杀生身'
            elif self._is_cai_gong(bazi, wuxing_result):
                return '身强用财格', '扶抑格', '身强用财，财来耗身'
            elif self._is_shi_sang(bazi, wuxing_result):
                return '食神吐秀格', '扶抑格', '身强用食伤泄秀'
            else:
                return '身强格', '扶抑格', '日主偏强，需克泄耗'
        
        elif wangshuai['level'] == '身弱':
            if self._is_yin_gong(bazi, wuxing_result):
                return '身弱用印格', '扶抑格', '身弱用印，印来生身'
            elif self._is_bi_jie(bazi, wuxing_result):
                return '身弱用比劫格', '扶抑格', '身弱用比劫帮身'
            else:
                return '身弱格', '扶抑格', '日主偏弱，需生扶'
        
        else:
            if self._is_cai_guan_shuang_mei(bazi, wuxing_result):
                return '财官双美格', '中和格', '财官得位，富贵双全'
            elif self._is_yin_shang_sheng_gui(bazi, wuxing_result):
                return '印绶生贵格', '中和格', '印星有力，官贵相生'
            else:
                return '中和格', '中和格', '五行均衡，不偏不倚'

    def _is_zhuanwang(self, bazi, wuxing_result):
        """判定专旺格"""
        total_score = wuxing_result.get('total_score', 0)
        if total_score == 0:
            return False
        
        sorted_wx = sorted(['木', '火', '土', '金', '水'],
                          key=lambda x: wuxing_result[x]['score'], reverse=True)
        
        max_wx = sorted_wx[0]
        max_score = wuxing_result[max_wx]['score']
        max_ratio = max_score / total_score
        
        if max_ratio >= 0.5:
            return True
        return False

    def _get_zhuanwang_name(self, wx):
        """获取专旺格名称"""
        names = {
            '木': '曲直格',
            '火': '炎上格',
            '土': '稼穑格',
            '金': '从革格',
            '水': '润下格'
        }
        return names.get(wx, '专旺格')

    def _get_zhuanwang_desc(self, wx):
        """获取专旺格描述"""
        descs = {
            '木': '木气专旺，曲直仁寿，主仁慈福寿',
            '火': '火气专旺，炎上光明，主文明热情',
            '土': '土气专旺，稼穑厚重，主诚信稳重',
            '金': '金气专旺，从革肃杀，主果断刚毅',
            '水': '水气专旺，润下流动，主智慧灵活'
        }
        return descs.get(wx, '五行专旺，气势磅礴')

    def _is_congge(self, bazi, wuxing_result, wangshuai):
        """判定从格"""
        if wangshuai['level'] != '身弱':
            return False
        
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        total_score = wuxing_result.get('total_score', 0)
        rizhu_score = wuxing_result.get(rizhu_wx, {}).get('score', 0)
        rizhu_ratio = rizhu_score / total_score if total_score > 0 else 0
        
        tonggen = wuxing_result.get('tonggen', {})
        tonggen_total = tonggen.get('total', 0)
        
        if rizhu_ratio <= 0.1 and tonggen_total == 0:
            return True
        return False

    def _get_congge_name(self, bazi, wuxing_result):
        """获取从格名称

        修复：旧逻辑用 if/elif 枚举五行，导致『从财格』仅当最强五行为『土』时才能命中，
        金/火日主永无机会判定为从财格。现改为依据『日主五行 ↔ 最强五行』的十神关系判定，
        使从财格（最强五行为日主之『我克』）可被任意日主正确触发。
        """
        sorted_wx = sorted(['木', '火', '土', '金', '水'],
                          key=lambda x: wuxing_result[x]['score'], reverse=True)

        max_wx = sorted_wx[0]

        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')

        rel = self._wuxing_relation(rizhu_wx, max_wx)
        mapping = {
            '我生': '从儿格',
            '克我': '从官杀格',
            '我克': '从财格',
            '生我': '从印格',
            '同我': '从旺格',
        }
        return mapping.get(rel, '从势格')

    @staticmethod
    def _wuxing_relation(day_wx, other_wx):
        """返回 day_wx 与 other_wx 的五行生克关系（十神大类）"""
        order = ['木', '火', '土', '金', '水']
        if day_wx not in order or other_wx not in order:
            return '同我'
        a = order.index(day_wx)
        b = order.index(other_wx)
        if a == b:
            return '同我'
        if (a + 1) % 5 == b:
            return '我生'
        if (a + 4) % 5 == b:
            return '生我'
        if (a + 2) % 5 == b:
            return '我克'
        if (a + 3) % 5 == b:
            return '克我'
        return '同我'

    def _is_sha_gong(self, bazi, wuxing_result):
        """判定杀印相生格"""
        rizhu = bazi.get('rizhu', '')

        gan_list = [ganzhi[0] for ganzhi in bazi['四柱']]

        has_sha = False
        has_yin = False
        
        for gan in gan_list:
            if self._is_killing(rizhu, gan):
                has_sha = True
            if self._is_seal(rizhu, gan):
                has_yin = True
        
        return has_sha and has_yin

    def _is_cai_gong(self, bazi, wuxing_result):
        """判定身强用财格"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        total_score = wuxing_result.get('total_score', 0)
        cai_wx = self._get_cai_wx(rizhu_wx)
        
        if cai_wx and wuxing_result.get(cai_wx, {}).get('score', 0) / total_score >= 0.2:
            return True
        return False

    def _is_shi_sang(self, bazi, wuxing_result):
        """判定食神吐秀格"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        total_score = wuxing_result.get('total_score', 0)
        shi_wx = self._get_shi_wx(rizhu_wx)
        
        if shi_wx and wuxing_result.get(shi_wx, {}).get('score', 0) / total_score >= 0.25:
            return True
        return False

    def _is_yin_gong(self, bazi, wuxing_result):
        """判定身弱用印格"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        total_score = wuxing_result.get('total_score', 0)
        yin_wx = self._get_yin_wx(rizhu_wx)
        
        if yin_wx and wuxing_result.get(yin_wx, {}).get('score', 0) / total_score >= 0.2:
            return True
        return False

    def _is_bi_jie(self, bazi, wuxing_result):
        """判定身弱用比劫格"""
        tonggen = wuxing_result.get('tonggen', {})
        tonggen_total = tonggen.get('total', 0)
        
        if tonggen_total >= 1:
            return True
        return False

    def _is_cai_guan_shuang_mei(self, bazi, wuxing_result):
        """判定财官双美格"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        cai_wx = self._get_cai_wx(rizhu_wx)
        guan_wx = self._get_guan_wx(rizhu_wx)
        
        if cai_wx and guan_wx:
            total_score = wuxing_result.get('total_score', 0)
            cai_score = wuxing_result.get(cai_wx, {}).get('score', 0)
            guan_score = wuxing_result.get(guan_wx, {}).get('score', 0)
            
            if cai_score / total_score >= 0.15 and guan_score / total_score >= 0.15:
                return True
        return False

    def _is_yin_shang_sheng_gui(self, bazi, wuxing_result):
        """判定印绶生贵格"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        yin_wx = self._get_yin_wx(rizhu_wx)
        guan_wx = self._get_guan_wx(rizhu_wx)
        
        if yin_wx and guan_wx:
            total_score = wuxing_result.get('total_score', 0)
            yin_score = wuxing_result.get(yin_wx, {}).get('score', 0)
            guan_score = wuxing_result.get(guan_wx, {}).get('score', 0)
            
            if yin_score / total_score >= 0.2 and guan_score / total_score >= 0.15:
                return True
        return False

    def _analyze_hehua(self, bazi):
        """分析合化"""
        result = []
        
        gan_list = [ganzhi[0] for ganzhi in bazi['四柱']]
        zhi_list = [ganzhi[1] for ganzhi in bazi['四柱']]
        
        for i, gan1 in enumerate(gan_list):
            for j, gan2 in enumerate(gan_list):
                if i >= j:
                    continue
                he_key = ''.join(sorted([gan1, gan2]))
                he_row = _TIAN_GAN_HE.get(he_key)
                if he_row:
                    result.append({
                        'type': '天干五合',
                        'elements': f'{gan1}合{gan2}',
                        'hehua': he_row.get('hua_wuxing', ''),
                        'pillar1': ['年柱', '月柱', '日柱', '时柱'][i],
                        'pillar2': ['年柱', '月柱', '日柱', '时柱'][j]
                    })
        
        for i, zhi1 in enumerate(zhi_list):
            for j, zhi2 in enumerate(zhi_list):
                if i >= j:
                    continue
                he_key = ''.join(sorted([zhi1, zhi2]))
                he_row = _DI_ZHI_HE.get(he_key)
                if he_row:
                    result.append({
                        'type': '地支六合',
                        'elements': f'{zhi1}合{zhi2}',
                        'hehua': he_row.get('hua_wuxing', ''),
                        'pillar1': ['年柱', '月柱', '日柱', '时柱'][i],
                        'pillar2': ['年柱', '月柱', '日柱', '时柱'][j]
                    })
        
        for sanhe_key, sanhe_row in _DI_ZHI_SAN_HE.items():
            if all(zhi in zhi_list for zhi in sanhe_key):
                result.append({
                    'type': '地支三合',
                    'elements': sanhe_key,
                    'hehua': sanhe_row.get('hua_wuxing', '')
                })
        
        return result

    def _analyze_chongxing(self, bazi):
        """分析冲刑"""
        result = []
        
        zhi_list = [ganzhi[1] for ganzhi in bazi['四柱']]
        
        for i, zhi1 in enumerate(zhi_list):
            for j, zhi2 in enumerate(zhi_list):
                if i >= j:
                    continue
                
                if _DI_ZHI_CHONG.get(zhi1) == zhi2:
                    result.append({
                        'type': '相冲',
                        'elements': f'{zhi1}冲{zhi2}',
                        'pillar1': ['年柱', '月柱', '日柱', '时柱'][i],
                        'pillar2': ['年柱', '月柱', '日柱', '时柱'][j]
                    })
                
                if zhi2 in _DI_ZHI_XING.get(zhi1, []):
                    result.append({
                        'type': '相刑',
                        'elements': f'{zhi1}刑{zhi2}',
                        'pillar1': ['年柱', '月柱', '日柱', '时柱'][i],
                        'pillar2': ['年柱', '月柱', '日柱', '时柱'][j]
                    })
        
        return result

    def _analyze_special_patterns(self, bazi, wuxing_result, wangshuai):
        """分析特殊格局"""
        patterns = []
        
        if self._is_shang_guan_jian_guan(bazi):
            patterns.append({
                'name': '伤官见官',
                'type': '凶',
                'description': '伤官与正官同时出现，主是非口舌，官非诉讼'
            })
        
        if self._is_guan_sha_hun_za(bazi):
            patterns.append({
                'name': '官杀混杂',
                'type': '凶',
                'description': '正官与七杀同时出现，主仕途多阻，感情不顺'
            })
        
        if self._is_yin_sheng_ri_zhu(bazi, wuxing_result):
            patterns.append({
                'name': '印星生身',
                'type': '吉',
                'description': '印星有力生助日主，主学业有成，贵人相助'
            })
        
        if self._is_cai_sheng_sha(bazi, wuxing_result):
            patterns.append({
                'name': '财生杀',
                'type': '凶',
                'description': '财星生助官杀，主压力增大，小人作祟'
            })
        
        if self._is_sha_sheng_yin(bazi, wuxing_result):
            patterns.append({
                'name': '杀生印',
                'type': '吉',
                'description': '官杀生助印星，主化险为夷，贵人提携'
            })
        
        return patterns

    def _is_shang_guan_jian_guan(self, bazi):
        """判定伤官见官"""
        gan_list = [ganzhi[0] for ganzhi in bazi['四柱']]
        
        rizhu = bazi.get('rizhu', '')
        rizhu_idx = _TIAN_GAN_MAP.get(rizhu)
        
        has_shang_guan = False
        has_guan = False
        
        for gan in gan_list:
            gan_idx = _TIAN_GAN_MAP.get(gan)
            if gan_idx is None or rizhu_idx is None:
                continue
            
            diff = (gan_idx - rizhu_idx) % 10
            if diff in (1, 9):
                has_shang_guan = True
            elif diff in (2, 8):
                has_guan = True
        
        return has_shang_guan and has_guan

    def _is_guan_sha_hun_za(self, bazi):
        """判定官杀混杂"""
        gan_list = [ganzhi[0] for ganzhi in bazi['四柱']]
        
        rizhu = bazi.get('rizhu', '')
        rizhu_idx = _TIAN_GAN_MAP.get(rizhu)
        
        has_zheng_guan = False
        has_sha = False
        
        for gan in gan_list:
            gan_idx = _TIAN_GAN_MAP.get(gan)
            if gan_idx is None or rizhu_idx is None:
                continue
            
            diff = (gan_idx - rizhu_idx) % 10
            rizhu_yang = rizhu_idx % 2 == 0
            gan_yang = gan_idx % 2 == 0
            
            if diff in (2, 8):
                if (diff == 2 and not rizhu_yang and gan_yang) or (diff == 8 and rizhu_yang and not gan_yang):
                    has_zheng_guan = True
                else:
                    has_sha = True
        
        return has_zheng_guan and has_sha

    def _is_yin_sheng_ri_zhu(self, bazi, wuxing_result):
        """判定印星生身"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        yin_wx = self._get_yin_wx(rizhu_wx)
        
        if yin_wx:
            total_score = wuxing_result.get('total_score', 0)
            yin_score = wuxing_result.get(yin_wx, {}).get('score', 0)
            
            if yin_score / total_score >= 0.2:
                return True
        return False

    def _is_cai_sheng_sha(self, bazi, wuxing_result):
        """判定财生杀"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        cai_wx = self._get_cai_wx(rizhu_wx)
        sha_wx = self._get_guan_wx(rizhu_wx)
        
        if cai_wx and sha_wx:
            total_score = wuxing_result.get('total_score', 0)
            cai_score = wuxing_result.get(cai_wx, {}).get('score', 0)
            sha_score = wuxing_result.get(sha_wx, {}).get('score', 0)
            
            if cai_score / total_score >= 0.15 and sha_score / total_score >= 0.15:
                return True
        return False

    def _is_sha_sheng_yin(self, bazi, wuxing_result):
        """判定杀生印"""
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        sha_wx = self._get_guan_wx(rizhu_wx)
        yin_wx = self._get_yin_wx(rizhu_wx)
        
        if sha_wx and yin_wx:
            total_score = wuxing_result.get('total_score', 0)
            sha_score = wuxing_result.get(sha_wx, {}).get('score', 0)
            yin_score = wuxing_result.get(yin_wx, {}).get('score', 0)
            
            if sha_score / total_score >= 0.15 and yin_score / total_score >= 0.2:
                return True
        return False

    def _is_killing(self, rizhu, other):
        """判断是否为官杀"""
        rizhu_idx = _TIAN_GAN_MAP.get(rizhu)
        other_idx = _TIAN_GAN_MAP.get(other)
        
        if rizhu_idx is None or other_idx is None:
            return False
        
        diff = (other_idx - rizhu_idx) % 10
        return diff in (2, 8)

    def _is_seal(self, rizhu, other):
        """判断是否为印星"""
        rizhu_idx = _TIAN_GAN_MAP.get(rizhu)
        other_idx = _TIAN_GAN_MAP.get(other)
        
        if rizhu_idx is None or other_idx is None:
            return False
        
        diff = (other_idx - rizhu_idx) % 10
        return diff in (4, 6)

    def _get_cai_wx(self, rizhu_wx):
        """获取财星五行"""
        cai_map = {
            '木': '土', '火': '金', '土': '水', '金': '木', '水': '火'
        }
        return cai_map.get(rizhu_wx)

    def _get_shi_wx(self, rizhu_wx):
        """获取食伤五行"""
        shi_map = {
            '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
        }
        return shi_map.get(rizhu_wx)

    def _get_yin_wx(self, rizhu_wx):
        """获取印星五行"""
        yin_map = {
            '木': '水', '火': '木', '土': '火', '金': '土', '水': '金'
        }
        return yin_map.get(rizhu_wx)

    def _get_guan_wx(self, rizhu_wx):
        """获取官杀五行"""
        guan_map = {
            '木': '金', '火': '水', '土': '木', '金': '火', '水': '土'
        }
        return guan_map.get(rizhu_wx)

    def _generate_comprehensive_analysis(self, geju_result):
        """生成综合分析"""
        parts = []
        
        parts.append(f"日主旺衰：{geju_result['wangshuai']['level']}")
        parts.append(f"主格局：{geju_result['main_geju']}")
        parts.append(f"格局类型：{geju_result['geju_type']}")
        parts.append(f"格局描述：{geju_result['description']}")
        
        if geju_result['hehua']:
            hehua_str = '；'.join([f"{h['type']}{h['elements']}合化为{h['hehua']}" for h in geju_result['hehua']])
            parts.append(f"合化情况：{hehua_str}")
        
        if geju_result['chongxing']:
            chongxing_str = '；'.join([f"{c['type']}{c['elements']}" for c in geju_result['chongxing']])
            parts.append(f"冲刑情况：{chongxing_str}")
        
        if geju_result['special_patterns']:
            pattern_str = '；'.join([f"{p['name']}({p['type']})：{p['description']}" for p in geju_result['special_patterns']])
            parts.append(f"特殊格局：{pattern_str}")
        
        return '。'.join(parts)
