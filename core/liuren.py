"""
大六壬排盘核心引擎

实现六壬(六壬神课)完整起课体系：
- 天地盘：地盘 12 地支固定（罗盘位），天盘按「月将加占时」旋转生成
- 四课：干上 / 干阴 / 支上 / 支阴（含所乘天将）
- 三传：九宗门（贼克 / 比用 / 涉害 / 昴星 / 伏吟 / 返吟 / 别责 / 八专），主路径自动判定 + 标注兜底
- 十二天将：贵人起法（昼贵/夜贵、顺逆布天盘），螣蛇…天后顺逆排布
- 神煞：驿马、六合等基础神煞
- 日干支换算：公历日期 → 干支纪日（1900-01-01 为甲戌基准）

返回结构化 dict，供 UI 展示与 AI 解读直接消费。

约定：
- 地盘顺序（罗盘顺时针，自北子起）：子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥
- 五行：木(甲乙·寅卯) 火(丙丁·巳午) 土(戊己·辰戌丑未) 金(庚辛·申酉) 水(壬癸·亥子)
- 天干寄宫：甲寅 乙辰 丙戊巳 丁己未 庚申 辛戌 壬亥 癸子
"""

from core.ganzhi_constants import TIAN_GAN as GAN, DI_ZHI as ZHI

# ===== 基础序列表 =====
# GAN / ZHI 直接复用 core.ganzhi_constants 的权威定义（见上方 import），
# 本模块内沿用 GAN / ZHI 这两个短名，避免大面积改动既有算法代码。
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
           '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
ZHI_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火',
           '辰': '土', '戌': '土', '丑': '土', '未': '土', '申': '金', '酉': '金'}
WX_KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}  # 「我」克者
WX_KE_BY = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}  # 克「我」者
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}  # 我生者（相）
WX_SHENG_BY = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 生我者（休）

# 天干寄宫（六壬专用）
GAN_JIGONG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
               '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '子'}

# 十二天将（贵人起，顺布序）
TIAN_JIANG = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
              '天空', '白虎', '太常', '玄武', '太阴', '天后']
# 十二月将（登明…神后，按公历月份 1-12 对应）
YUE_JIANG = {1: '亥', 2: '戌', 3: '酉', 4: '申', 5: '未', 6: '午',
              7: '巳', 8: '辰', 9: '卯', 10: '寅', 11: '丑', 12: '子'}
YUE_JIANG_NAME = {'子': '神后', '丑': '大吉', '寅': '功曹', '卯': '太冲',
                  '辰': '天罡', '巳': '太乙', '午': '胜光', '未': '小吉',
                  '申': '传送', '酉': '从魁', '戌': '河魁', '亥': '登明'}

# 贵人（昼贵）：甲戊庚牛羊、乙己鼠猴乡、丙丁猪鸡位、壬癸兔蛇藏、六辛逢马虎
GUIREN_DAY = {'甲': '丑', '戊': '丑', '庚': '丑', '乙': '子', '己': '子',
              '丙': '亥', '丁': '亥', '壬': '卯', '癸': '卯', '辛': '寅'}
GUIREN_NIGHT = {'甲': '未', '戊': '未', '庚': '未', '乙': '申', '己': '申',
                '丙': '酉', '丁': '酉', '壬': '巳', '癸': '巳', '辛': '午'}

# 九宗门可选「取用」方式
GATE_METHODS = ['auto', 'zeike', 'biyong', 'shehai', 'maoxing',
                'fuyin', 'fanyin', 'bieze', 'bazhuan']
GATE_NAMES = {
    'auto': '九宗门(自动)',
    'zeike': '贼克法', 'biyong': '比用法', 'shehai': '涉害法',
    'maoxing': '昴星法', 'fuyin': '伏吟法', 'fanyin': '返吟法',
    'bieze': '别责法', 'bazhuan': '八专法',
}

# 三合局 → 驿马
YIMA = {'申子辰': '寅', '寅午戌': '申', '巳酉丑': '亥', '亥卯未': '巳'}

# 地支三刑（伏吟中末传取变用）
_XING = {'子': '卯', '卯': '子',
         '寅': '巳', '巳': '申', '申': '寅',
         '丑': '戌', '戌': '未', '未': '丑',
         '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'}
# 地支六冲（返吟/别责中末传取变用）
_CHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑',
          '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
          '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}

# 旬空（空亡）：六甲旬首地支 → 所空二支
_KONGWANG = {'子': ('戌', '亥'), '戌': ('申', '酉'), '申': ('午', '未'),
              '午': ('辰', '巳'), '辰': ('寅', '卯'), '寅': ('子', '丑')}
# 天干五合 → 合干（用于"日干六合支"：合干所寄之宫）
_GAN_HE = {'甲': '己', '乙': '庚', '丙': '辛', '丁': '壬', '戊': '癸',
            '己': '甲', '庚': '乙', '辛': '丙', '壬': '丁', '癸': '戊'}
# 地支六害
_DI_ZHI_LIUHAI = {'子': '未', '未': '子', '丑': '午', '午': '丑',
                   '寅': '巳', '巳': '寅', '卯': '辰', '辰': '卯',
                   '申': '亥', '亥': '申', '酉': '戌', '戌': '酉'}
# 天马（依月将三合局）
_TIANMA = {'寅': '戌', '午': '戌', '戌': '戌', '申': '子', '子': '子',
           '辰': '子', '亥': '寅', '卯': '寅', '未': '寅', '巳': '申',
           '酉': '申', '丑': '申'}
# 太阳黄经 → 月将（按中气切换；单位度）
_LAMBDA_TO_YUEJIANG = [
    (0, '戌'), (30, '酉'), (60, '申'), (90, '未'), (120, '午'),
    (150, '巳'), (180, '辰'), (210, '卯'), (240, '寅'), (270, '丑'),
    (300, '子'), (330, '亥'),
]


def _wuxing_ke(a, b):
    """返回 True 表示 a 五行克 b 五行。"""
    return WX_KE.get(a) == b


def _idx(seq, item):
    """取元素在序列中的下标，六壬盘中大量用于地支的"宫位序号"换算。

    天地盘旋转、天将顺逆布排都要把地支转成 0-11 的位置再做模 12 运算，
    此处仅是 list.index 的简写别名。

    Args:
        seq: 序列，实际调用中恒为 ZHI（十二地支）。
        item: 待定位的元素，即某个地支字。

    Returns:
        int: 元素下标。元素不存在时与 list.index 一致抛 ValueError。
    """
    return seq.index(item)


class LiuRenCalculator:
    """大六壬起课计算引擎。"""

    def __init__(self):
        """无状态构造：本引擎所有查表数据均为模块级常量，实例不持有任何状态。

        因此可安全复用同一实例，或每次起课新建，二者等价。
        """
        pass

    # ---------- 历法换算 ----------
    def ganzhi_day(self, y, m, d):
        """公历日期(y,m,d) → (日干, 日支)。1900-01-01 为甲戌日。"""
        # 距 1900-01-01 的天数
        base_y, base_m, base_d = 1900, 1, 1
        # 用简明日序差（与世纪基准无关，仅需相对差稳定）
        def ordinal(y, m, d):
            """公历年月日 → 连续日序号（儒略日式整数），用于求两日期相差天数。

            Args:
                y: 公历年。
                m: 公历月，1-12。
                d: 公历日。

            Returns:
                int: 该日的绝对日序号。绝对值本身无意义，只有两个日期
                    相减得到的差值才有用（差值不受基准选取影响）。
            """
            # 把 1、2 月视作上一年的 13、14 月，使闰日恒落在"年末"，
            # 这样闰年判断与下面的月长多项式才能统一成一条公式
            if m <= 2:
                y -= 1
                m += 12
            return (365 * y + y // 4 - y // 100 + y // 400
                    + (153 * m + 8) // 5 + d + 1721119)
        delta = ordinal(y, m, d) - ordinal(base_y, base_m, base_d)
        # 甲戌 = 干支序号 10（甲1…甲戌11 → 0-indexed 10）
        seq = (10 + delta) % 60
        gan = GAN[seq % 10]
        zhi = ZHI[seq % 12]
        return gan, zhi

    def hour_to_zhi(self, hour):
        """24 小时制 → 占时地支（子时 23-1 跨日，按晚子时归当日占时）。"""
        if hour == 23 or hour == 0:
            return '子'
        return ZHI[((hour + 1) // 2) % 12]

    def yue_jiang(self, year=None, month=None, day=None):
        """月将：按太阳过中气（太阳黄经）映射，而非公历月近似。

        当 year/month/day 三者齐备时，依据占问日期的太阳黄经确定月将
        （中气切换点：冬至→丑、大寒→子、雨水→亥、春分→戌……）；
        仅给 month（兼容旧调用）时回退到公历月近似表。
        """
        if year is not None and month is not None and day is not None:
            lam = self._solar_longitude(year, month, day)
            return self._yue_jiang_from_longitude(lam)
        return YUE_JIANG.get(month, '亥')

    @staticmethod
    def _solar_longitude(y, m, d):
        """计算太阳黄经（度，[0,360)），Meeus 低精度公式。"""
        import math
        if m <= 2:
            y -= 1
            m += 12
        a = y // 100
        b = 2 - a + a // 4
        jd = (int(365.25 * (y + 4716)) + int(30.6001 * (m + 1))
              + d + b - 1524.5)
        n = jd - 2451545.0  # J2000 起算天数
        L = (280.46646 + 0.98564736 * n) % 360.0
        g = (357.52911 + 0.98560028 * n) % 360.0
        gr = math.radians(g)
        lam = (L + 1.914602 * math.sin(gr) + 0.019993 * math.sin(2 * gr)
               + 0.000289 * math.sin(3 * gr)) % 360.0
        return lam

    @staticmethod
    def _yue_jiang_from_longitude(lam):
        """太阳黄经 → 月将地支（按中气区间）。"""
        lam = lam % 360.0
        for thr, zhi in reversed(_LAMBDA_TO_YUEJIANG):
            if lam >= thr:
                return zhi
        return _LAMBDA_TO_YUEJIANG[0][1]  # lam<0 不可达，兜底戌

    # ---------- 排盘主入口 ----------
    def calc(self, method='auto', year=None, month=None, day=None, hour=None,
             question='', ri_gan=None, ri_zhi=None, zhan_shi=None):
        """起一课完整六壬盘。

        Args:
            method: 三传取用法（见 GATE_METHODS），'auto' 由九宗门规则自动判定。
            year/month/day/hour: 占问公历时间，缺省取当前时辰。
            question: 所占之事（可选）。
            ri_gan/ri_zhi: 可手动指定日干支；缺省由日期换算。
            zhan_shi: 可手动指定占时地支；缺省由 hour 换算。
        Returns: 结构化结果 dict。
        """
        from datetime import datetime
        now = datetime.now()
        y = year if year is not None else now.year
        m = month if month is not None else now.month
        d = day if day is not None else now.day
        h = hour if hour is not None else now.hour

        if ri_gan is None or ri_zhi is None:
            ri_gan, ri_zhi = self.ganzhi_day(y, m, d)
        if zhan_shi is None:
            zhan_shi = self.hour_to_zhi(h)

        yj = self.yue_jiang(y, m, d)
        is_day = 5 <= h < 19  # 卯时至酉时前为昼

        di_pan = list(ZHI)  # 地盘（固定顺序 = 罗盘位）
        tian_pan = self._build_tian_pan(di_pan, yj, zhan_shi)

        # 四课
        gan_jigong = GAN_JIGONG.get(ri_gan, ri_zhi)
        si_ke = self._build_sike(tian_pan, gan_jigong, ri_zhi)

        # 三传
        san_chuan, gate_used = self._build_sanchuan(
            method, ri_gan, ri_zhi, si_ke, tian_pan, di_pan)

        # 十二天将
        tian_jiang = self._build_tianjiang(ri_gan, tian_pan, is_day)

        # 神煞
        shen_sha = self._build_shensha(ri_gan, ri_zhi, san_chuan, yj)

        return {
            'method': method,
            'method_name': GATE_NAMES.get(method, method),
            'question': question,
            'time': f'{y}年{m}月{d}日 {h:02d}:00',
            'ri_gan': ri_gan,
            'ri_zhi': ri_zhi,
            'ri_gan_wx': GAN_WX.get(ri_gan, ''),
            'yue_jiang': yj,
            'yue_jiang_name': YUE_JIANG_NAME.get(yj, ''),
            'zhan_shi': zhan_shi,
            'is_day': is_day,
            'di_pan': di_pan,
            'tian_pan': tian_pan,           # {地盘支: 天盘支}
            'si_ke': si_ke,
            'san_chuan': san_chuan,         # {chu,zhong,mo,gate}
            'tian_jiang': tian_jiang,       # [{pos, dizhi, tianpan, jiang}, ...]
            'shen_sha': shen_sha,
        }

    # ---------- 天地盘 ----------
    def _build_tian_pan(self, di_pan, yue_jiang, zhan_shi):
        """月将加占时：天盘[占时] = 月将，其余按地盘序顺推。"""
        idx_yj = _idx(ZHI, yue_jiang)
        idx_zs = _idx(ZHI, zhan_shi)
        tian_pan = {}
        for s, dizhi in enumerate(di_pan):
            # 将 月将 对齐到 占时 位，整体顺移
            tp = ZHI[(idx_yj + (s - idx_zs)) % 12]
            tian_pan[dizhi] = tp
        return tian_pan

    # ---------- 四课 ----------
    def _build_sike(self, tian_pan, gan_jigong, ri_zhi):
        """干上 / 干阴 / 支上 / 支阴（各含天地盘支与所乘天将名）。"""
        def entry(dizhi):
            """由地盘位取出该位的一课信息（地盘支、其上天盘支、天盘支五行）。

            "课"的本质就是"某地盘位上骑着哪个天盘支"，四课都用这一步构造。

            Args:
                dizhi: 地盘宫位的地支字。

            Returns:
                dict: {'dizhi': 地盘支, 'tianpan': 其上的天盘支,
                    'wx': 天盘支的五行}。天盘中查不到该位时以自身兜底
                    （相当于天地同位，即伏吟态）。
            """
            tp = tian_pan.get(dizhi, dizhi)
            return {'dizhi': dizhi, 'tianpan': tp,
                    'wx': ZHI_WX.get(tp, '')}

        gan_shang = entry(gan_jigong)      # 第一课：干上神
        gan_yin = entry(gan_shang['tianpan'])  # 第二课：干阴
        zhi_shang = entry(ri_zhi)           # 第三课：支上神
        zhi_yin = entry(zhi_shang['tianpan'])  # 第四课：支阴
        return {
            'gan_shang': gan_shang, 'gan_yin': gan_yin,
            'zhi_shang': zhi_shang, 'zhi_yin': zhi_yin,
        }

    # ---------- 三传（九宗门） ----------
    def _build_sanchuan(self, method, ri_gan, ri_zhi, si_ke, tian_pan, di_pan):
        """由四课推出三传（初传/中传/末传），即六壬断事的主干。

        三传代表事情的开端、经过与结局。取三传的规则合称"九宗门"，
        判定次第为：
        1. 贼克法 —— 四课中若有支克日干者为"贼"（外来相侵，优先），
           无贼则取日干所克者为"克"，据之定初传；
        2. 比用法 —— 上一步命中多个时，取与日干阴阳同类（比和）者；
        3. 涉害法 —— 仍不能决时，比较受克深浅取最深者；
        4. 若四课无贼无克，则转入昴星/伏吟/返吟/别责/八专等兜底门法
           （见 _no_zei_ke）。
        初传定后，中末传按各门法自身规则递推（见 _build_zhong_mo）。

        Args:
            method: 取用法。'auto' 走上述自动判定；'zeike'/'biyong'/'shehai'
                同样进入自动主路径但会标注对应门名；其余值走 _forced_gate 强制指定。
            ri_gan: 日干。
            ri_zhi: 日支。
            si_ke: _build_sike 产出的四课。
            tian_pan: 天盘映射 {地盘支: 天盘支}。
            di_pan: 地盘十二支列表（此处保留以对齐调用签名）。

        Returns:
            tuple: ({'chu','zhong','mo','gate'}, gate)。gate 为最终采用的
                门法代号，两处返回同一值，便于调用方按需取用。
        """
        k1 = si_ke['gan_shang']['tianpan']
        k2 = si_ke['gan_yin']['tianpan']
        k3 = si_ke['zhi_shang']['tianpan']
        k4 = si_ke['zhi_yin']['tianpan']
        ke_list = [k1, k2, k3, k4]
        ri_wx = GAN_WX.get(ri_gan, '')

        # 贼（课中克日干者）/ 克（日干所克者）
        zei = [k for k in ke_list if _wuxing_ke(ZHI_WX.get(k, ''), ri_wx)]
        ke = [k for k in ke_list if _wuxing_ke(ri_wx, ZHI_WX.get(k, ''))]

        gate = None
        chu = None
        # 十天干甲起，偶数位（0,2,4...）为阳干；阳日阴日的取用方向相反
        gan_yang = GAN.index(ri_gan) % 2 == 0

        if method in ('auto', 'zeike', 'biyong', 'shehai'):
            if zei:
                # 比用：取与日干阴阳奇偶相同（比和）者，而非五行相等
                bi = [k for k in zei if (ZHI.index(k) % 2 == 0) == gan_yang]
                chu = (bi[0] if bi else zei[0])
                gate = 'zeike'
                if method == 'shehai' and len(zei) >= 2:
                    # 涉害：取克日干而于地盘顺数至受克最深者（取首）
                    gate = 'shehai'
                elif method == 'biyong' and bi:
                    gate = 'biyong'
            elif ke:
                chu = ke[0]
                gate = 'biyong' if method == 'biyong' else 'zeike'
            else:
                chu, gate = self._no_zei_ke(method, ri_gan, ri_zhi,
                                              si_ke, k1, k3)
        else:
            # 指定门法
            chu, gate = self._forced_gate(method, ri_gan, ri_zhi,
                                            si_ke, k1, k3)

        # 所有门法均未定出初传时兜底取干上神，保证盘面完整不致崩溃
        if chu is None:
            chu = k1
            gate = gate or 'zeike'

        # 中传 / 末传：按门法取变（九宗门各自规则）
        zhong, mo = self._build_zhong_mo(gate, chu, ri_gan, ri_zhi,
                                          si_ke, tian_pan)
        return ({'chu': chu, 'zhong': zhong, 'mo': mo, 'gate': gate},
                gate)

    # ---------- 中末传（按门法取变） ----------
    def _build_zhong_mo(self, gate, chu, ri_gan, ri_zhi, si_ke, tian_pan):
        """依据九宗门门法，给定初传 chu 推导中传/末传。

        贼克/比用/涉害：连茹（天盘遁）。其余门法按《六壬大全》取变规则。
        """
        k1 = si_ke['gan_shang']['tianpan']   # 干上神
        k3 = si_ke['zhi_shang']['tianpan']   # 支上神
        gan_yang = GAN.index(ri_gan) % 2 == 0

        if gate in ('zeike', 'biyong', 'shehai'):
            # 连茹：中传取初传天盘所乘，末传取中传天盘所乘
            zhong = tian_pan.get(chu, chu)
            mo = tian_pan.get(zhong, zhong)
        elif gate == 'maoxing':
            # 昴星：阳日 初=支上、中=干上、末=支上；阴日 初=干上、中=支上、末=干上
            zhong = k1 if gan_yang else k3
            mo = chu
        elif gate == 'fuyin':
            # 伏吟：初=日支，中末传按三刑连传
            zhong = self._di_zhi_xing(ri_zhi)
            mo = self._di_zhi_xing(zhong)
        elif gate == 'fanyin':
            # 返吟：初=支上，中=日支，末=日支所冲
            zhong = ri_zhi
            mo = self._di_zhi_chong(ri_zhi)
        elif gate == 'bieze':
            # 别责：初=干上，中=日支所冲，末=日干
            zhong = self._di_zhi_chong(ri_zhi)
            mo = ri_gan
        elif gate == 'bazhuan':
            # 八专：初=干上，中=日干，末=日支
            zhong = ri_gan
            mo = ri_zhi
        else:
            zhong = tian_pan.get(chu, chu)
            mo = tian_pan.get(zhong, zhong)
        return zhong, mo

    @staticmethod
    def _di_zhi_xing(z):
        """地支三刑：子↔卯；寅→巳→申→寅；丑→戌→未→丑；辰午酉亥自刑。"""
        return _XING.get(z, z)

    @staticmethod
    def _di_zhi_chong(z):
        """地支六冲：子↔午、丑↔未、寅↔申、卯↔酉、辰↔戌、巳↔亥。"""
        return _CHONG.get(z, z)

    def _no_zei_ke(self, method, ri_gan, ri_zhi, si_ke, k1, k3):
        """无贼无克时的昴星 / 伏吟 / 返吟 / 别责 / 八专 兜底。"""
        gs = si_ke['gan_shang']['tianpan']
        gy = si_ke['gan_yin']['tianpan']
        zs = si_ke['zhi_shang']['tianpan']
        zy = si_ke['zhi_yin']['tianpan']
        gan_yang = GAN.index(ri_gan) % 2 == 0

        # 伏吟：天地同（干上==支上 且 干阴==支阴）；初传取日支，中末传按三刑
        if gs == zs and gy == zy:
            return ri_zhi, 'fuyin'
        # 返吟：干上==支阴 且 干阴==支上（天地冲）；初传取支上，中传日支，末传日支冲
        if gs == zy and gy == zs:
            return zs, 'fanyin'
        # 八专：干支同位（如 甲寅、丁未）且四课只有两课
        if ri_zhi == GAN_JIGONG.get(ri_gan, '') and gs == zs:
            return (k3 if gan_yang else k1), 'bazhuan'
        # 别责：干支不备（仅三课）取干上
        if gs == zs:
            return k1, 'bieze'
        # 昴星：阳日取支上、阴日取干上
        return ((k3 if gan_yang else k1), 'maoxing')

    def _forced_gate(self, method, ri_gan, ri_zhi, si_ke, k1, k3):
        """用户强制指定门法时，直接按该门法的起例定初传（跳过九宗门判定）。

        与 _no_zei_ke 的区别：那里是"自动判定走到无贼无克才落到兜底门法"，
        这里是"用户在界面上点名要用某门法"，即便盘面并不成立该门法之象
        也照排，供研习者对照不同取用法的结果。

        Args:
            method: 门法代号，见 GATE_METHODS。
            ri_gan: 日干。
            ri_zhi: 日支。
            si_ke: 四课。
            k1: 第一课干上神（天盘支）。
            k3: 第三课支上神（天盘支）。

        Returns:
            tuple[str, str]: (初传地支, 门法代号)。method 不在支持表中时
                回落到 (干上神, 'zeike')。
        """
        zs = si_ke['zhi_shang']['tianpan']
        gan_yang = GAN.index(ri_gan) % 2 == 0
        # 返回 (初传, 门法) 元组，避免解包崩溃
        forced = {
            'fuyin': (ri_zhi, 'fuyin'),
            'fanyin': (zs, 'fanyin'),
            'bazhuan': ((k3 if gan_yang else k1), 'bazhuan'),
            'bieze': (k1, 'bieze'),
            'maoxing': ((k3 if gan_yang else k1), 'maoxing'),
        }
        return forced.get(method, (k1, 'zeike'))

    # ---------- 十二天将 ----------
    def _build_tianjiang(self, ri_gan, tian_pan, is_day):
        """贵人起法：昼贵顺布、夜贵逆布。返回 12 宫位天将序列。"""
        guiren = (GUIREN_DAY if is_day else GUIREN_NIGHT).get(ri_gan, '丑')
        # 贵人所在天盘位
        gui_pos = None
        for pos, dz in tian_pan.items():
            if dz == guiren:
                gui_pos = pos
                break
        if gui_pos is None:
            gui_pos = guiren
        # 阳干/昼 → 顺布；阴干/夜 → 逆布
        gan_yang = GAN.index(ri_gan) % 2 == 0
        reverse = not (gan_yang == is_day)
        seq = []
        for i in range(12):
            offset = i if not reverse else -i
            pos = ZHI[(_idx(ZHI, gui_pos) + offset) % 12]
            seq.append({'pos': pos, 'dizhi': pos,
                        'tianpan': tian_pan.get(pos, pos),
                        'jiang': TIAN_JIANG[i]})
        return seq

    # ---------- 神煞 ----------
    def _build_shensha(self, ri_gan, ri_zhi, san_chuan, yue_jiang):
        """汇总本课的神煞，作为断课时的吉凶佐证。

        神煞是叠加在盘面上的标记，各有专断的事类：
        - 驿马：依日支三合局取，主奔走、迁移、外出；
        - 空亡（旬空）：日柱所在旬缺配的两个地支，落空亡者主事虚不实、
          谋而无成，是六壬断"不成"的关键依据；
        - 六合：日干五合之干所寄之宫，主和合、成事；
        - 六害：日支所害之支，主暗损、疑忌；
        - 天马：依月将三合局取，同主动象；
        - 旺相休囚死：日干在月令下的五种气势，衡量占者自身的力量强弱
          （旺=当令最强，相=次强，休=退气，囚=受制，死=最弱）。

        Args:
            ri_gan: 日干。
            ri_zhi: 日支。
            san_chuan: 三传字典，用于生成三传流转的展示串。
            yue_jiang: 月将地支，兼作月令用于旺相休囚死判定。

        Returns:
            dict: 神煞名 -> 对应地支或结论字符串。未命中的神煞（如日支
                不在任何三合局内的驿马）不会出现在返回值中。
        """
        sha = {}
        # 驿马：依日支三合局
        for trio, ma in YIMA.items():
            if ri_zhi in trio:
                sha['驿马'] = ma
                break
        # 三传
        chu = san_chuan.get('chu', '')
        zhong = san_chuan.get('zhong', '')
        mo = san_chuan.get('mo', '')
        sha['三传'] = f'{chu} → {zhong} → {mo}'
        # 空亡（旬空）
        kw = self._kongwang(ri_gan, ri_zhi)
        if kw:
            sha['空亡'] = '、'.join(kw)
        # 日干六合支（天干五合之寄宫）
        he_gan = _GAN_HE.get(ri_gan)
        if he_gan:
            sha['六合'] = GAN_JIGONG.get(he_gan, '')
        # 六害（日支所害之支）
        sha['六害'] = _DI_ZHI_LIUHAI.get(ri_zhi, '')
        # 天马（依月将三合局）
        sha['天马'] = _TIANMA.get(yue_jiang, '')
        # 旺相休囚死（日干在月令）
        sha['旺相休囚死'] = self._wang_xiu(ri_gan, yue_jiang)
        return sha

    def _kongwang(self, ri_gan, ri_zhi):
        """返回日柱所在旬的空亡二支（旬空）。"""
        g = GAN.index(ri_gan)
        z = ZHI.index(ri_zhi)
        # 由干支序号反推该日在六十甲子中的位置：干十支十二，二者错位 2，
        # 故 (g-z)/2 取模 6 即可定出落在六旬中的第几旬
        k = ((g - z) // 2) % 6
        seq = (g + 10 * k) % 60
        # 每旬十组，seq//10*10 归到旬首（甲某）的位置，再取其地支
        xun_shou_zhi = ZHI[(seq // 10 * 10) % 12]
        return _KONGWANG.get(xun_shou_zhi)

    def _wang_xiu(self, ri_gan, yue_jiang):
        """日干在月令（月将）的旺相休囚死。"""
        r = GAN_WX.get(ri_gan, '')
        m = ZHI_WX.get(yue_jiang, '')
        if not r or not m:
            return ''
        if r == m:
            return '旺'
        if WX_SHENG.get(r) == m:
            return '相'
        if WX_SHENG.get(m) == r:
            return '休'
        if WX_KE.get(m) == r:
            return '囚'
        if WX_KE.get(r) == m:
            return '死'
        return ''


# 便捷模块级函数（供 main_window 直接调用，镜像 meihua.time_divination 习惯）
def liuren_divination(method='auto', question='', year=None, month=None,
                      day=None, hour=None, ri_gan=None, ri_zhi=None,
                      zhan_shi=None):
    """模块级便捷函数：一行起一课六壬盘。

    供 main_window 等调用方免去自行实例化 LiuRenCalculator，
    形式上与 meihua.time_divination 保持一致，便于 UI 层统一调度。

    Args:
        method: 三传取用法，见 GATE_METHODS，默认 'auto' 由九宗门自动判定。
        question: 所占之事，仅原样带回结果供展示，不参与运算。
        year/month/day/hour: 占问的公历时间；任一缺省则取当前系统时间对应项。
        ri_gan/ri_zhi: 手动指定日干、日支；缺省由日期换算。
        zhan_shi: 手动指定占时地支；缺省由 hour 换算。

    Returns:
        dict: 与 LiuRenCalculator.calc 相同的结构化排盘结果。
    """
    return LiuRenCalculator().calc(
        method=method, year=year, month=month, day=day, hour=hour,
        question=question, ri_gan=ri_gan, ri_zhi=ri_zhi, zhan_shi=zhan_shi)
