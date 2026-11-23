"""
梅花易数起卦模块 - 实现传统梅花易数的起卦和解卦功能
"""

# 天干地支常量统一取自 core.ganzhi_constants（唯一权威源）；
# 保留本模块的同名再导出，兼容 `from core.divination.meihua import TIAN_GAN` 的旧写法。
from core.ganzhi_constants import TIAN_GAN, DI_ZHI

#: 六爻自下而上的名称，索引 0 为最下方的初爻
YAO_NAMES = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']

# =============================================================================
# 先天八卦数 → 三爻位图（通行《梅花易数》先天卦序）
#   乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
# 元组索引 0 = 初爻（最下），索引 2 = 上爻（最上），与 YAO_NAMES 的「初→上」一致。
# 先天卦数是固定的三爻位图，绝非按 num % 3 的进制拆分结果。
# =============================================================================
TRIGRAM_YAO = {
    1: ('阳', '阳', '阳'),  # 乾 ☰（三阳）
    2: ('阳', '阳', '阴'),  # 兑 ☱（下二阳，上阴）
    3: ('阳', '阴', '阳'),  # 离 ☲（上下阳，中阴）
    4: ('阳', '阴', '阴'),  # 震 ☳（下阳，上二阴）
    5: ('阴', '阳', '阳'),  # 巽 ☴（下阴，上二阳）
    6: ('阴', '阳', '阴'),  # 坎 ☵（上下阴，中阳）
    7: ('阴', '阴', '阳'),  # 艮 ☶（下二阴，上阳）
    8: ('阴', '阴', '阴'),  # 坤 ☷（三阴）
}

#: 三爻位图（初→上）→ 先天八卦数的反查表，用于「位图直查」而不是进制推导
TRIGRAM_NUM_FROM_YAO = {pattern: num for num, pattern in TRIGRAM_YAO.items()}


class MeiHuaCalculator:
    """梅花易数计算器 - 实现多种起卦方式"""

    def __init__(self):
        """初始化时构建天干支名→序号索引，供起卦后干支换算与取用。"""
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}

    def _convert_to_hexagram(self, num):
        """将数字转换为卦象"""
        if num == 0:
            num = 8
        elif num < 1 or num > 8:
            num = num % 8
            if num == 0:
                num = 8
        return num

    def _build_hexagram(self, upper_num, lower_num):
        """构建卦象"""
        upper_hex = self._convert_to_hexagram(upper_num)
        lower_hex = self._convert_to_hexagram(lower_num)
        return {
            'upper': upper_hex,
            'lower': lower_hex,
            'full': f'{upper_hex}-{lower_hex}'
        }

    def _get_changing_yao(self, upper_num, lower_num):
        """获取动爻"""
        total = upper_num + lower_num
        remainder = total % 6
        if remainder == 0:
            return 6
        return remainder

    @staticmethod
    def _get_stroke_counts(chars):
        """批量取汉字的康熙笔画数；任一汉字未收录即显式报错，绝不估算或按 ×2 假造。

        Args:
            chars: 汉字字符列表（可含重复）。

        Returns:
            list[int]: 与 chars 一一对应的笔画数。

        Raises:
            ValueError: 存在未收录笔画数据的汉字。
        """
        from core.database_manager import get_db_manager

        unique = list(dict.fromkeys(chars))
        batch = get_db_manager().get_stroke_count_batch(unique)
        missing = [char for char in unique if not batch.get(char)]
        if missing:
            raise ValueError(
                "以下汉字未收录笔画数据，无法按笔画起卦："
                + "、".join(missing)
                + "；请改用已收录的汉字，或手动指定笔画数"
            )
        return [batch[char] for char in chars]

    @staticmethod
    def _make_yao(yao_type):
        """由爻型构造统一的爻信息字典，保证 type/符号/阴阳/变爻标记四处一致。"""
        is_yang = yao_type in ('老阳', '少阳')
        return {
            'type': yao_type,
            'is_changing': yao_type in ('老阴', '老阳'),
            'symbol': '---' if is_yang else '-- --',
            'symbol_short': '阳' if is_yang else '阴',
        }

    @classmethod
    def _flip_yao(cls, yao):
        """返回阴阳相反的静爻（变卦/错卦使用，变后不再是老阴/老阳）。"""
        return cls._make_yao('少阴' if yao['symbol_short'] == '阳' else '少阳')

    def _get_yangs_from_num(self, num):
        """由先天卦数直取三爻位图（初→上），不再做 num % 3 的进制拆分。

        先天卦数对应固定的三爻位图（见 TRIGRAM_YAO），例如离3=阳阴阳、
        坤8=阴阴阴；用进制拆分会把位图算成完全不同的卦。
        """
        num = self._convert_to_hexagram(num)
        return [
            self._make_yao('少阳' if yao == '阳' else '少阴')
            for yao in TRIGRAM_YAO[num]
        ]

    def time_divination(self, year, month, day, hour, question=''):
        """
        时间起卦 - 根据年月日时起卦
        算法：年+月+日=上卦，年+月+日+时=下卦，总数取动爻
        先天八卦数：乾1兑2离3震4巽5坎6艮7坤8
        """
        year_num = (year - 4) % 60
        month_num = month
        day_num = day
        hour_num = hour

        upper_total = year_num + month_num + day_num
        lower_total = upper_total + hour_num

        upper_num = upper_total % 8
        if upper_num == 0:
            upper_num = 8
        lower_num = lower_total % 8
        if lower_num == 0:
            lower_num = 8

        changing_yao = lower_total % 6
        if changing_yao == 0:
            changing_yao = 6

        base_hex = self._build_hexagram(upper_num, lower_num)
        
        return {
            'method': '时间起卦',
            'question': question,
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'upper_total': upper_total,
            'lower_total': lower_total,
            'upper_num': upper_num,
            'lower_num': lower_num,
            'changing_yao': changing_yao,
            'base_hex': base_hex,
            'base_upper_yangs': self._get_yangs_from_num(upper_num),
            'base_lower_yangs': self._get_yangs_from_num(lower_num),
        }

    def number_divination(self, numbers, question=''):
        """
        数字起卦 - 根据用户输入的数字起卦
        支持1-3个数字：
        - 1个数字：上卦=数%8，下卦=(数//10)%8，动爻=数%6
        - 2个数字：上卦=第一个数%8，下卦=第二个数%8，动爻=(两数之和)%6
        - 3个数字：上卦=第一个数%8，下卦=第二个数%8，动爻=第三个数%6

        Args:
            numbers: 数字列表，1-3个正整数
            question: 占问问题

        Returns:
            卦象结果字典

        Raises:
            ValueError: 参数不符合要求
        """
        if not numbers or not isinstance(numbers, (list, tuple)):
            raise ValueError("数字起卦需要1-3个数字")
        
        numbers = [int(n) for n in numbers if isinstance(n, (int, float)) and n > 0]
        
        if len(numbers) == 0 or len(numbers) > 3:
            raise ValueError("数字起卦需要1-3个正整数")

        if len(numbers) == 1:
            num = numbers[0]
            upper_num = num % 8
            lower_num = (num // 10) % 8
            if lower_num == 0:
                lower_num = 8
            changing_yao = num % 6
            if changing_yao == 0:
                changing_yao = 6
        elif len(numbers) == 2:
            upper_num = numbers[0] % 8
            lower_num = numbers[1] % 8
            changing_yao = (numbers[0] + numbers[1]) % 6
            if changing_yao == 0:
                changing_yao = 6
        else:
            upper_num = numbers[0] % 8
            lower_num = numbers[1] % 8
            changing_yao = numbers[2] % 6
            if changing_yao == 0:
                changing_yao = 6

        if upper_num == 0:
            upper_num = 8
        if lower_num == 0:
            lower_num = 8

        base_hex = self._build_hexagram(upper_num, lower_num)

        return {
            'method': '数字起卦',
            'question': question,
            'numbers': numbers,
            'upper_num': upper_num,
            'lower_num': lower_num,
            'changing_yao': changing_yao,
            'base_hex': base_hex,
            'base_upper_yangs': self._get_yangs_from_num(upper_num),
            'base_lower_yangs': self._get_yangs_from_num(lower_num),
        }

    def direction_divination(self, direction, question='', hour=None):
        """
        方位起卦 - 根据方位起卦
        方位对应数字：东方3、南方9、西方7、北方1、东南4、西南2、西北6、东北8
        上卦=方位数，下卦=时辰数，动爻=(方位数+时辰数)%6
        
        Args:
            direction: 方位字符串（东/南/西/北/东南/西南/西北/东北）
            question: 占问问题
            hour: 可选，占问时刻小时数（0-23），默认当前系统时间
        """
        direction_map = {
            '东': 3, '东方': 3, '正东方': 3, 'east': 3,
            '南': 9, '南方': 9, '正南方': 9, 'south': 9,
            '西': 7, '西方': 7, '正西方': 7, 'west': 7,
            '北': 1, '北方': 1, '正北方': 1, 'north': 1,
            '东南': 4, '东南方': 4, 'southeast': 4,
            '西南': 2, '西南方': 2, 'southwest': 2,
            '西北': 6, '西北方': 6, 'northwest': 6,
            '东北': 8, '东北方': 8, 'northeast': 8
        }

        if direction not in direction_map:
            raise ValueError("无效的方位，请输入：东、南、西、北、东南、西南、西北、东北")

        direction_num = direction_map[direction]
        if hour is None:
            import datetime
            hour = datetime.datetime.now().hour
        hour_num = hour % 12 + 1

        upper_num = direction_num % 8
        lower_num = hour_num % 8

        if upper_num == 0:
            upper_num = 8
        if lower_num == 0:
            lower_num = 8

        total = direction_num + hour_num
        changing_yao = total % 6
        if changing_yao == 0:
            changing_yao = 6

        base_hex = self._build_hexagram(upper_num, lower_num)

        return {
            'method': '方位起卦',
            'question': question,
            'direction': direction,
            'direction_num': direction_num,
            'hour': hour,
            'hour_num': hour_num,
            'upper_num': upper_num,
            'lower_num': lower_num,
            'changing_yao': changing_yao,
            'base_hex': base_hex,
            'base_upper_yangs': self._get_yangs_from_num(upper_num),
            'base_lower_yangs': self._get_yangs_from_num(lower_num),
        }

    def text_divination(self, text, question=''):
        """
        文字起卦 - 按每个汉字真实笔画起卦
        上卦=总笔画%8，下卦=(总笔画+字数)%8，动爻=(总笔画*字数)%6

        笔画一律取数据库康熙笔画表（DatabaseManager.get_stroke_count）。
        未收录的汉字必须显式报错，严禁再用 len(char)*2 之类的假造值。
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("文字起卦需要非空文字")

        chars = [char for char in text if '\u4e00' <= char <= '\u9fff']
        if not chars:
            raise ValueError("文字起卦未检测到有效汉字，请输入中文内容")

        stroke_counts = self._get_stroke_counts(chars)
        total_strokes = sum(stroke_counts)
        char_count = len(chars)

        upper_num = total_strokes % 8
        lower_num = (total_strokes + char_count) % 8

        if upper_num == 0:
            upper_num = 8
        if lower_num == 0:
            lower_num = 8

        total = total_strokes * char_count
        changing_yao = total % 6
        if changing_yao == 0:
            changing_yao = 6

        base_hex = self._build_hexagram(upper_num, lower_num)

        return {
            'method': '文字起卦',
            'question': question,
            'text': text,
            'char_count': char_count,
            'char_strokes': dict(zip(chars, stroke_counts)),
            'total_strokes': total_strokes,
            'upper_num': upper_num,
            'lower_num': lower_num,
            'changing_yao': changing_yao,
            'base_hex': base_hex,
            'base_upper_yangs': self._get_yangs_from_num(upper_num),
            'base_lower_yangs': self._get_yangs_from_num(lower_num),
        }

    def copper_coin_divination(self, six_lines, question=''):
        """
        铜钱摇卦 - 模拟传统3枚铜钱摇6次（从初爻到上爻）
        
        传统铜钱定爻（每爻掷三枚）：
        - 三背 = 老阳（阳，变爻）
        - 二背 = 少阳（阳，静爻）
        - 一背 = 少阴（阴，静爻）
        - 零背（三字）= 老阴（阴，变爻）

        输入 six_lines 已是逐爻定出的爻型（初→上），直接透传构造爻位图：
        下卦取初二三爻、上卦取四五上爻，三爻位图直查先天卦数。
        绝不把 6 个爻的编码值「相加后 %8」当作整卦数——三元之和只对应单爻。

        Args:
            six_lines: 6 次摇卦结果列表（初→上），每项为 '老阳'/'少阴'/'少阳'/'老阴'
            question: 占问问题

        Returns:
            卦象结果字典
        """
        if len(six_lines) != 6:
            raise ValueError("铜钱摇卦需要提供6次摇卦结果")

        VALID_YAO_TYPES = {'老阳', '少阴', '少阳', '老阴'}
        for i, yao_type in enumerate(six_lines):
            if yao_type not in VALID_YAO_TYPES:
                raise ValueError(f"第{i+1}爻无效，应为 老阳/少阴/少阳/老阴，收到: {yao_type}")

        # 爻型由原始输入直接透传，不再二次推导（原 num % 3 会把老阳 3 % 3 == 0 判成老阴）
        lower_yangs = [self._make_yao(t) for t in six_lines[0:3]]   # 初、二、三爻
        upper_yangs = [self._make_yao(t) for t in six_lines[3:6]]   # 四、五、上爻

        lower_num = TRIGRAM_NUM_FROM_YAO[tuple(y['symbol_short'] for y in lower_yangs)]
        upper_num = TRIGRAM_NUM_FROM_YAO[tuple(y['symbol_short'] for y in upper_yangs)]

        # 检查哪些爻是老阴/老阳（变爻），记录所有变爻
        changing_positions = []
        for i, yao_type in enumerate(six_lines):
            if yao_type in ('老阴', '老阳'):
                changing_positions.append(i + 1)  # 1-indexed，与初→上顺序一致

        # 如果没有任何变爻，默认取第6爻为动爻（无变则静，以末爻为机）
        if not changing_positions:
            changing_positions = [6]

        changing_yao = changing_positions[0]

        base_hex = self._build_hexagram(upper_num, lower_num)

        return {
            'method': '铜钱摇卦',
            'question': question,
            'six_lines': six_lines,
            'upper_num': upper_num,
            'lower_num': lower_num,
            'changing_yao': changing_yao,
            'changing_positions': changing_positions,
            'base_hex': base_hex,
            'base_upper_yangs': upper_yangs,
            'base_lower_yangs': lower_yangs,
        }
    
    def stroke_divination(self, char_or_text, question='', stroke_count=None):
        """
        笔画起卦 - 单字笔画数起卦
        上卦=笔画数%8，下卦=笔画数//8 的余数%8，动爻=笔画数%6
        
        Args:
            char_or_text: 单个汉字
            question: 占问问题
            stroke_count: 可选，手动指定笔画数（若不指定则自动查康熙字典笔画库）
            
        Returns:
            卦象结果字典
        """
        if len(char_or_text) != 1:
            raise ValueError("笔画起卦需要一个汉字")
        
        if not '\u4e00' <= char_or_text <= '\u9fff':
            raise ValueError("笔画起卦需要输入一个汉字")
        
        # 获取笔画数：优先用手动指定，其次查数据库；查不到必须报错，不做任何估算
        if stroke_count is None:
            stroke_count = self._get_stroke_counts([char_or_text])[0]
        
        upper_num = stroke_count % 8
        if upper_num == 0:
            upper_num = 8
        lower_num = (stroke_count // 8) % 8
        if lower_num == 0:
            lower_num = 8
        
        changing_yao = stroke_count % 6
        if changing_yao == 0:
            changing_yao = 6
        
        base_hex = self._build_hexagram(upper_num, lower_num)

        return {
            'method': '笔画起卦',
            'question': question,
            'char': char_or_text,
            'stroke_count': stroke_count,
            'upper_num': upper_num,
            'lower_num': lower_num,
            'changing_yao': changing_yao,
            'base_hex': base_hex,
            'base_upper_yangs': self._get_yangs_from_num(upper_num),
            'base_lower_yangs': self._get_yangs_from_num(lower_num),
        }

    def generate_all_hexagrams(self, divination_result):
        """
        生成所有卦象（本卦、互卦、变卦、错卦、综卦）
        支持铜钱摇卦的多变爻场景。

        统一约定：所有爻列表均为「初→上」顺序（索引 0 = 初爻/最下）。
        因此 all_yangs 亦为初→上，动爻位置 i+1 可直接对应「第 i+1 爻」。
        """
        upper_num = divination_result['upper_num']
        lower_num = divination_result['lower_num']
        changing_yao = divination_result['changing_yao']
        changing_positions = divination_result.get('changing_positions', [changing_yao])

        base_upper_yangs = list(divination_result['base_upper_yangs'])
        base_lower_yangs = list(divination_result['base_lower_yangs'])

        # 六爻按初→上排列：初、二、三（下卦）+ 四、五、上（上卦）
        all_yangs = base_lower_yangs + base_upper_yangs

        # 互卦：下互取二三四爻，上互取三四五爻（古法；切片天然保持初→上）
        hu_lower_yangs = all_yangs[1:4]   # 二、三、四爻 → 互卦下卦
        hu_upper_yangs = all_yangs[2:5]   # 三、四、五爻 → 互卦上卦

        # 变卦：按变爻位置翻转阴阳，其余保持；仍按初→上切分上下卦
        bi_all = [
            self._flip_yao(yao) if (i + 1) in changing_positions else yao
            for i, yao in enumerate(all_yangs)
        ]
        bi_lower_yangs = bi_all[:3]
        bi_upper_yangs = bi_all[3:]

        # 错卦：六爻全反（上下卦各自取反，爻位顺序不变）
        cuo_lower_yangs = [self._flip_yao(yao) for yao in base_lower_yangs]
        cuo_upper_yangs = [self._flip_yao(yao) for yao in base_upper_yangs]

        # 综卦：整卦颠倒（六爻反向）。新下卦 = 原上卦反向，新上卦 = 原下卦反向
        zong_lower_yangs = base_upper_yangs[::-1]
        zong_upper_yangs = base_lower_yangs[::-1]

        return {
            'base': {
                'upper_num': upper_num,
                'lower_num': lower_num,
                'upper_yangs': base_upper_yangs,
                'lower_yangs': base_lower_yangs,
                'all_yangs': all_yangs,
                'changing_yao': changing_yao,
                'changing_positions': changing_positions,
                'changing_yao_name': YAO_NAMES[changing_yao - 1] if changing_yao <= 6 else '',
            },
            'hu': {
                'upper_yangs': hu_upper_yangs,
                'lower_yangs': hu_lower_yangs
            },
            'bian': {
                'upper_yangs': bi_upper_yangs,
                'lower_yangs': bi_lower_yangs
            },
            'cuo': {
                'upper_yangs': cuo_upper_yangs,
                'lower_yangs': cuo_lower_yangs
            },
            'zong': {
                'upper_yangs': zong_upper_yangs,
                'lower_yangs': zong_lower_yangs
            }
        }
