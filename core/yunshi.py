from core.baazi import TIAN_GAN, DI_ZHI, YEAR_GANZHI, MONTH_GAN

YUNSHI_ANALYSIS = {
    '甲': {
        'positive': '甲木参天，蓬勃向上，主创新、开拓、积极进取',
        'negative': '过旺则固执、冲动，需注意人际关系'
    },
    '乙': {
        'positive': '乙木柔韧，善于变通，主智慧、文雅、富有艺术气质',
        'negative': '过弱则意志不坚，容易随波逐流'
    },
    '丙': {
        'positive': '丙火炎炎，热情洋溢，主光明、才华、社交能力强',
        'negative': '过旺则急躁、冲动，需控制情绪'
    },
    '丁': {
        'positive': '丁火柔和，温文尔雅，主细腻、体贴、富有同情心',
        'negative': '过弱则缺乏主见，容易犹豫不决'
    },
    '戊': {
        'positive': '戊土厚重，稳重可靠，主踏实、守信、有责任感',
        'negative': '过旺则固执、保守，需灵活变通'
    },
    '己': {
        'positive': '己土温润，包容万物，主善良、谦和、善于协调',
        'negative': '过弱则缺乏自信，容易依赖他人'
    },
    '庚': {
        'positive': '庚金锐利，果断刚毅，主决断、勇敢、事业心强',
        'negative': '过旺则刻薄、刚愎自用，需注意人际关系'
    },
    '辛': {
        'positive': '辛金清秀，才华出众，主聪慧、优雅、追求完美',
        'negative': '过弱则缺乏魄力，容易优柔寡断'
    },
    '壬': {
        'positive': '壬水奔腾，活力充沛，主智慧、灵活、适应能力强',
        'negative': '过旺则散漫、缺乏定力，需专注目标'
    },
    '癸': {
        'positive': '癸水柔顺，聪明伶俐，主敏感、细腻、富有想象力',
        'negative': '过弱则胆小、缺乏自信，需增强勇气'
    }
}

ZHI_ANALYSIS = {
    '子': '子水智慧，主思维敏捷，但需防桃花困扰',
    '丑': '丑土厚重，主稳重踏实，但需防固执保守',
    '寅': '寅木生发，主积极进取，但需防冲动鲁莽',
    '卯': '卯木柔顺，主文雅艺术，但需防犹豫不决',
    '辰': '辰土藏龙，主潜力无限，但需防优柔寡断',
    '巳': '巳火热情，主活力四射，但需防急躁冲动',
    '午': '午火旺盛，主光明正大，但需防骄傲自满',
    '未': '未土温和，主善良包容，但需防依赖他人',
    '申': '申金锐利，主果断刚毅，但需防刻薄寡恩',
    '酉': '酉金清秀，主才华出众，但需防孤芳自赏',
    '戌': '戌土厚重，主稳重可靠，但需防固执己见',
    '亥': '亥水智慧，主聪明灵活，但需防散漫无章'
}

class YunShiCalculator:
    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}
        self.ganzhi_map = {gz: i for i, gz in enumerate(YEAR_GANZHI)}

    def get_year_ganzhi(self, year):
        idx = (year - 4) % 60
        return YEAR_GANZHI[idx]

    def get_month_ganzhi(self, year_gan, month):
        month_idx = month - 1
        for key, gan_list in MONTH_GAN:
            if year_gan in key:
                month_gan = gan_list[month_idx]
                month_zhi = DI_ZHI[month_idx]
                return month_gan + month_zhi
        return ''

    def calculate_major_fortune(self, bazhi, gender, birth_year):
        rizhu = bazhi['rizhu']
        day_gan_idx = self.tian_gan_map[rizhu]
        
        is_male = gender == '男'
        is_yang = day_gan_idx % 2 == 0
        
        if (is_male and is_yang) or (not is_male and not is_yang):
            direction = '顺行'
        else:
            direction = '逆行'

        month_ganzhi = bazhi['month']
        start_idx = self.ganzhi_map[month_ganzhi]
        
        periods = []
        for i in range(9):
            if direction == '顺行':
                ganzhi_idx = (start_idx + i) % 60
            else:
                ganzhi_idx = (start_idx - i + 60) % 60
            
            ganzhi = YEAR_GANZHI[ganzhi_idx]
            
            start_age = 10 + i * 10
            if i == 0:
                start_age = 0
            
            start_year = birth_year + start_age
            end_year = start_year + 10
            
            analysis = self._analyze_fortune_period(ganzhi)
            
            periods.append({
                'period': i + 1,
                'ganzhi': ganzhi,
                'start_age': start_age,
                'end_age': start_age + 9,
                'start_year': start_year,
                'end_year': end_year - 1,
                'direction': direction,
                'analysis': analysis
            })
        
        return {'periods': periods, 'direction': direction}

    def calculate_annual_fortune(self, bazhi, start_year=2024, years_count=10):
        years = []
        
        for i in range(years_count):
            year = start_year + i
            year_ganzhi = self.get_year_ganzhi(year)
            
            minor_fortune = self._calculate_minor_fortune(bazhi, year)
            analysis = self._analyze_annual_fortune(bazhi, year_ganzhi)
            
            years.append({
                'year': year,
                'ganzhi': year_ganzhi,
                'minor_fortune': minor_fortune,
                'analysis': analysis
            })
        
        return {'years': years}

    def _calculate_minor_fortune(self, bazhi, year):
        rizhu = bazhi['rizhu']
        rizhu_idx = self.tian_gan_map[rizhu]
        
        year_idx = (year - 4) % 60
        minor_idx = (rizhu_idx * 2 + year_idx) % 60
        
        return YEAR_GANZHI[minor_idx]

    def calculate_monthly_fortune(self, bazhi, target_year=None):
        if target_year is None:
            target_year = 2024
        
        months = []
        year_gan = self.get_year_ganzhi(target_year)[0]
        
        for month in range(1, 13):
            month_ganzhi = self.get_month_ganzhi(year_gan, month)
            analysis = self._analyze_monthly_fortune(bazhi, month_ganzhi)
            
            months.append({
                'year': target_year,
                'month': month,
                'ganzhi': month_ganzhi,
                'month_name': DI_ZHI[month - 1] + '月',
                'analysis': analysis
            })
        
        return {'months': months}

    def _analyze_fortune_period(self, ganzhi):
        gan = ganzhi[0]
        zhi = ganzhi[1]
        
        gan_info = YUNSHI_ANALYSIS.get(gan, {})
        zhi_info = ZHI_ANALYSIS.get(zhi, '')
        
        parts = []
        if 'positive' in gan_info:
            parts.append(gan_info['positive'])
        if zhi_info:
            parts.append(zhi_info)
        
        return '；'.join(parts)

    def _analyze_annual_fortune(self, bazhi, year_ganzhi):
        rizhu = bazhi['rizhu']
        year_gan = year_ganzhi[0]
        year_zhi = year_ganzhi[1]
        
        gan_info = YUNSHI_ANALYSIS.get(year_gan, {})
        zhi_info = ZHI_ANALYSIS.get(year_zhi, '')
        
        parts = []
        
        rizhu_idx = self.tian_gan_map[rizhu]
        year_gan_idx = self.tian_gan_map[year_gan]
        diff = (year_gan_idx - rizhu_idx) % 10
        
        relationship = ''
        if diff == 0:
            relationship = '本年与日主相同，主得朋友相助'
        elif diff in (1, 9):
            relationship = '本年生助日主，主得贵人扶持'
        elif diff in (2, 8):
            relationship = '本年克制日主，主压力较大'
        elif diff in (3, 7):
            relationship = '本年被日主克制，主财运不错'
        elif diff in (4, 6):
            relationship = '本年生助日主，主学业或事业进步'
        
        if relationship:
            parts.append(relationship)
        
        if 'positive' in gan_info:
            parts.append(f'天干{year_gan}：{gan_info["positive"]}')
        
        if zhi_info:
            parts.append(f'地支{year_zhi}：{zhi_info}')
        
        return '；'.join(parts)

    def _analyze_monthly_fortune(self, bazhi, month_ganzhi):
        month_gan = month_ganzhi[0]
        month_zhi = month_ganzhi[1]
        
        gan_info = YUNSHI_ANALYSIS.get(month_gan, {})
        zhi_info = ZHI_ANALYSIS.get(month_zhi, '')
        
        parts = []
        
        if 'positive' in gan_info:
            parts.append(f'{month_gan}月：{gan_info["positive"]}')
        
        if zhi_info:
            parts.append(zhi_info)
        
        return '；'.join(parts)