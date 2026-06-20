"""
梅花易数起卦模块 - 实现传统梅花易数的起卦和解卦功能
"""
import datetime
from core.baazi import TIAN_GAN, DI_ZHI, YEAR_GANZHI


YAO_NAMES = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']


class MeiHuaCalculator:
    """梅花易数计算器 - 实现多种起卦方式"""

    def __init__(self):
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

    def _get_yao_type(self, remainder):
        """获取爻的类型（阴爻或阳爻）"""
        if remainder == 0:
            return '老阴'
        elif remainder == 3:
            return '老阳'
        elif remainder == 1:
            return '少阴'
        elif remainder == 2:
            return '少阳'
        return '少阳'

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

    def _get_yangs_from_num(self, num):
        """从数字获取爻的详细信息"""
        yao_list = []
        for _ in range(3):
            remainder = num % 3
            yao_type = self._get_yao_type(remainder)
            yao_list.insert(0, {
                'type': yao_type,
                'is_changing': yao_type in ['老阴', '老阳'],
                'symbol': '---' if yao_type in ['老阳', '少阳'] else '-- --',
                'symbol_short': '阳' if yao_type in ['老阳', '少阳'] else '阴'
            })
            num = num // 3
        return yao_list

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
        """
        if not numbers or len(numbers) > 3:
            raise ValueError("数字起卦需要1-3个数字")

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

    def direction_divination(self, direction, question=''):
        """
        方位起卦 - 根据方位起卦
        方位对应数字：东方3、南方9、西方7、北方1、东南4、西南2、西北6、东北8
        上卦=方位数，下卦=时辰数，动爻=(方位数+时辰数)%6
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
        now = datetime.datetime.now()
        hour = now.hour
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
        文字起卦 - 根据文字笔画起卦
        上卦=文字笔画总数%8，下卦=(笔画总数+字数)%8，动爻=(笔画总数*字数)%6
        """
        total_strokes = sum(len(char) * 2 if '\u4e00' <= char <= '\u9fff' else len(char) 
                           for char in text)
        
        char_count = len(text)
        
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
            'total_strokes': total_strokes,
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
        """
        upper_num = divination_result['upper_num']
        lower_num = divination_result['lower_num']
        changing_yao = divination_result['changing_yao']

        base_upper_yangs = divination_result['base_upper_yangs'].copy()
        base_lower_yangs = divination_result['base_lower_yangs'].copy()

        all_yangs = base_lower_yangs + base_upper_yangs

        upper_middle = base_upper_yangs[0]
        upper_top = base_upper_yangs[1]
        lower_bottom = base_lower_yangs[2]
        lower_middle = base_lower_yangs[1]

        hu_upper_yangs = [upper_middle, upper_top, lower_bottom]
        hu_lower_yangs = [lower_bottom, lower_middle, upper_middle]

        bi_upper_yangs = []
        bi_lower_yangs = []
        for i, yao in enumerate(all_yangs):
            if i + 1 == changing_yao:
                new_type = '老阳' if yao['type'] in ['老阴', '少阴'] else '老阴'
                new_symbol = '---' if yao['type'] in ['老阴', '少阴'] else '-- --'
                new_symbol_short = '阳' if yao['type'] in ['老阴', '少阴'] else '阴'
                changed_yao = {
                    'type': new_type,
                    'is_changing': False,
                    'symbol': new_symbol,
                    'symbol_short': new_symbol_short
                }
                if i < 3:
                    bi_lower_yangs.append(changed_yao)
                else:
                    bi_upper_yangs.append(changed_yao)
            else:
                if i < 3:
                    bi_lower_yangs.append(yao)
                else:
                    bi_upper_yangs.append(yao)

        cuo_upper_yangs = []
        cuo_lower_yangs = []
        for yao in base_upper_yangs:
            new_type = '老阳' if yao['type'] in ['老阴', '少阴'] else '老阴'
            new_symbol = '---' if yao['type'] in ['老阴', '少阴'] else '-- --'
            new_symbol_short = '阳' if yao['type'] in ['老阴', '少阴'] else '阴'
            cuo_upper_yangs.append({
                'type': new_type,
                'is_changing': False,
                'symbol': new_symbol,
                'symbol_short': new_symbol_short
            })
        for yao in base_lower_yangs:
            new_type = '老阳' if yao['type'] in ['老阴', '少阴'] else '老阴'
            new_symbol = '---' if yao['type'] in ['老阴', '少阴'] else '-- --'
            new_symbol_short = '阳' if yao['type'] in ['老阴', '少阴'] else '阴'
            cuo_lower_yangs.append({
                'type': new_type,
                'is_changing': False,
                'symbol': new_symbol,
                'symbol_short': new_symbol_short
            })

        zong_upper_yangs = base_lower_yangs[::-1]
        zong_lower_yangs = base_upper_yangs[::-1]

        return {
            'base': {
                'upper_num': upper_num,
                'lower_num': lower_num,
                'upper_yangs': base_upper_yangs,
                'lower_yangs': base_lower_yangs,
                'all_yangs': all_yangs,
                'changing_yao': changing_yao,
                'changing_yao_name': YAO_NAMES[changing_yao - 1] if changing_yao <= 6 else ''
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
