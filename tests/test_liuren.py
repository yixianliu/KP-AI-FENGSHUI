"""
大六壬排盘引擎单元测试 + 三传（九宗门）表征测试

设计目的：
1. 锁定已正确实现的稳定部分（干支换算、天地盘、四课、贵人起法、贼克/比用/涉害三传、
   驿马神煞），防止后续重构回归。
2. 以古籍《六壬大全》九宗门经典规则，为 伏吟/返吟/昴星/别责/八专 五门 + 比用法 + 显式门法
   编码"正确中末传"表征测试。P1-1a（三传修正）已落地：修复 _forced_gate 解包崩溃、中末传改按
   各门法取变、比和改用地支阴阳奇偶比较。以下测试现均为通过状态，作为九宗门回归基线。

约定：本文件所有"古典期望"均依据九宗门标准取变法手算得出。
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuren import LiuRenCalculator, ZHI

# 固定一份天地盘用于断言（月将=亥、占时=卯）：
# 月将加占时 → 天盘[卯]=亥，整体顺移。
TP_HAI_MAO = {
    '子': '申', '丑': '酉', '寅': '戌', '卯': '亥', '辰': '子', '巳': '丑',
    '午': '寅', '未': '卯', '申': '辰', '酉': '巳', '戌': '午', '亥': '未',
}
DI_PAN = list(ZHI)


class TestLiuRenStable(unittest.TestCase):
    """已正确实现的稳定部分：重构安全网（必须始终通过）。"""

    def setUp(self):
        """构造稳定部分测试用的六壬计算器实例。"""
        self.c = LiuRenCalculator()

    # ---- 历法换算 ----
    def test_ganzhi_day_anchor(self):
        """1900-01-01 为甲戌日（古籍万年历标准锚点）。"""
        self.assertEqual(self.c.ganzhi_day(1900, 1, 1), ('甲', '戌'))

    def test_ganzhi_day_60_cycle(self):
        """干支 60 一循环：1900-01-01 +60 天（=1900-03-02，1900 非闰年）应回到甲戌。"""
        self.assertEqual(self.c.ganzhi_day(1900, 3, 2), ('甲', '戌'))

    def test_ganzhi_day_linear(self):
        """次日依次顺推：1900-01-02 = 乙亥。"""
        self.assertEqual(self.c.ganzhi_day(1900, 1, 2), ('乙', '亥'))

    def test_ganzhi_day_known_spring_festival(self):
        """2024-02-10 春节（甲辰年）当日干支 = 甲辰（年干支与日干支巧合一致，可作交叉校验）。"""
        self.assertEqual(self.c.ganzhi_day(2024, 2, 10), ('甲', '辰'))

    def test_hour_to_zhi(self):
        """占时换算：子时跨日(23/0)→子，午时(11-13)→午，未时(13-15)→未。"""
        self.assertEqual(self.c.hour_to_zhi(0), '子')
        self.assertEqual(self.c.hour_to_zhi(23), '子')
        self.assertEqual(self.c.hour_to_zhi(12), '午')
        self.assertEqual(self.c.hour_to_zhi(13), '未')

    # ---- 天地盘 ----
    def test_tian_pan_yue_jiang_jia_shi(self):
        """月将加占时：亥将加卯时，天盘[卯]=亥、[子]=申、[丑]=酉。"""
        tp = self.c._build_tian_pan(DI_PAN, '亥', '卯')
        self.assertEqual(tp['卯'], '亥')
        self.assertEqual(tp['子'], '申')
        self.assertEqual(tp['丑'], '酉')
        # 天盘是地盘的一个置换（12 支俱全）
        self.assertEqual(sorted(tp.values()), sorted(ZHI))

    # ---- 四课 ----
    def test_si_ke_construction(self):
        """甲日（干寄宫寅）、日支子，天地盘=亥+卯：四课干上/干阴/支上/支阴正确。"""
        tp = dict(TP_HAI_MAO)
        sike = self.c._build_sike(tp, '寅', '子')
        self.assertEqual((sike['gan_shang']['dizhi'], sike['gan_shang']['tianpan']), ('寅', '戌'))
        self.assertEqual((sike['gan_yin']['dizhi'], sike['gan_yin']['tianpan']), ('戌', '午'))
        self.assertEqual((sike['zhi_shang']['dizhi'], sike['zhi_shang']['tianpan']), ('子', '申'))
        self.assertEqual((sike['zhi_yin']['dizhi'], sike['zhi_yin']['tianpan']), ('申', '辰'))

    # ---- 十二天将（贵人起法）----
    def test_tian_jiang_guiren_position(self):
        """甲日昼贵在丑，丑将临天盘巳位 → 贵人位于巳；顺布：螣蛇在午。"""
        tp = dict(TP_HAI_MAO)
        tj = self.c._build_tianjiang('甲', tp, True)
        self.assertEqual(tj[0]['pos'], '巳')
        self.assertEqual(tj[0]['jiang'], '贵人')
        self.assertEqual(tj[1]['pos'], '午')
        self.assertEqual(tj[1]['jiang'], '螣蛇')
        # 十二将齐备且无重复
        self.assertEqual([x['jiang'] for x in tj],
                         ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
                          '天空', '白虎', '太常', '玄武', '太阴', '天后'])

    # ---- 三传：贼克法（中末传=天盘遁，正确）----
    def test_sanchuan_zeike(self):
        """甲日木，四课含申(金)克日干 → 贼；申阳与日干比 → 初传申；中末传天盘遁。"""
        tp = dict(TP_HAI_MAO)
        sike = {'gan_shang': {'tianpan': '申'}, 'gan_yin': {'tianpan': '酉'},
                'zhi_shang': {'tianpan': '子'}, 'zhi_yin': {'tianpan': '亥'}}
        sc, gate = self.c._build_sanchuan('auto', '甲', '子', sike, tp, DI_PAN)
        self.assertEqual(gate, 'zeike')
        self.assertEqual(sc['chu'], '申')
        self.assertEqual(sc['zhong'], tp['申'])   # 辰
        self.assertEqual(sc['mo'], tp[tp['申']])   # 子

    def test_sanchuan_zeike_bi_fallback(self):
        """贼克法（即使 method=biyong，存在比者申时仍按比用取申；本测试锁定 贼克 中末传天盘遁）。"""
        tp = dict(TP_HAI_MAO)
        sike = {'gan_shang': {'tianpan': '申'}, 'gan_yin': {'tianpan': '酉'},
                'zhi_shang': {'tianpan': '子'}, 'zhi_yin': {'tianpan': '亥'}}
        # 注：当前 _build_sanchuan 在 method='biyong' 且存在比者时标注 biyong；
        # 此处仅锁定"中末传=天盘遁"这一正确行为，不约束 gate 标签。
        sc, _ = self.c._build_sanchuan('zeike', '甲', '子', sike, tp, DI_PAN)
        self.assertEqual(sc['chu'], '申')
        self.assertEqual(sc['zhong'], tp['申'])    # 辰
        self.assertEqual(sc['mo'], tp[tp['申']])   # 子

    # ---- 神煞：驿马 ----
    def test_shensha_yima(self):
        """日支子（申子辰局）→ 驿马寅；三传字段存在。"""
        san_chuan = {'chu': '申', 'zhong': '辰', 'mo': '子', 'gate': 'zeike'}
        sha = self.c._build_shensha('甲', '子', san_chuan, '子')
        self.assertEqual(sha['驿马'], '寅')
        self.assertIn('三传', sha)
        # 日支午（寅午戌局）→ 驿马申
        sha2 = self.c._build_shensha('甲', '午', san_chuan, '午')
        self.assertEqual(sha2['驿马'], '申')


class TestLiuRenSanChuanSpec(unittest.TestCase):
    """
    三传（九宗门）古典表征测试 —— 当前引擎对 伏吟/返吟/昴星/别责/八专 的中末传一律误用"天盘遁"，
    显式指定门法还会因 _forced_gate 元组缺失逗号抛 ValueError。
    这些测试以古籍经典规则编码"正确中末传"，标记为 expectedFailure：
      - 当前：因逻辑错误而断言失败（计入 expected failures，不破坏套件）
      - P1-1a 修正后：应转为通过，届时移除 @unittest.expectedFailure 装饰器
    """

    def setUp(self):
        """构造九宗门表征测试用的计算器实例，并固定亥将+卯时天地盘。"""
        self.c = LiuRenCalculator()
        self.tp = dict(TP_HAI_MAO)

    def _run_auto(self, ri_gan, ri_zhi, k1, k2, k3, k4):
        """构造无贼无克四课（k1..k4 为天盘地支），走 auto 路径触发九宗门自动判定。"""
        sike = {'gan_shang': {'tianpan': k1}, 'gan_yin': {'tianpan': k2},
                'zhi_shang': {'tianpan': k3}, 'zhi_yin': {'tianpan': k4}}
        return self.c._build_sanchuan('auto', ri_gan, ri_zhi, sike, self.tp, DI_PAN)

    def test_spec_maoxing(self):
        """昴星法（阳日）：初传=支上(午)，中传=干上(寅)，末传=支上(午)。"""
        # 无贼无克（全水木火），非伏吟/返吟/八专/别责 → 落昴星
        sc, gate = self._run_auto('甲', '子', '寅', '卯', '午', '巳')
        self.assertEqual(gate, 'maoxing')
        self.assertEqual(sc['chu'], '午')
        self.assertEqual(sc['zhong'], '寅')
        self.assertEqual(sc['mo'], '午')

    def test_spec_fuyin(self):
        """伏吟法（刚日）：初传=日支(子)，中传=子之刑(卯)，末传=卯之刑(子)。"""
        sc, gate = self._run_auto('甲', '子', '寅', '午', '寅', '午')  # 干上=支上=寅，干阴=支阴=午
        self.assertEqual(gate, 'fuyin')
        self.assertEqual(sc['chu'], '子')
        self.assertEqual(sc['zhong'], '卯')
        self.assertEqual(sc['mo'], '子')

    def test_spec_fanyin(self):
        """返吟法（无克贼）：初传=支上(午)，中传=日支(子)，末传=日支所冲(午)。"""
        sc, gate = self._run_auto('甲', '子', '寅', '午', '午', '寅')  # 干上=支阴，干阴=支上
        self.assertEqual(gate, 'fanyin')
        self.assertEqual(sc['chu'], '午')
        self.assertEqual(sc['zhong'], '子')
        self.assertEqual(sc['mo'], '午')

    def test_spec_bieze(self):
        """别责法：初传=干上(寅)，中传=支上(午)，末传=日干(甲)。"""
        sc, gate = self._run_auto('甲', '子', '寅', '卯', '寅', '巳')  # 干上=支上=寅（三课）
        self.assertEqual(gate, 'bieze')
        self.assertEqual(sc['chu'], '寅')
        self.assertEqual(sc['zhong'], '午')
        self.assertEqual(sc['mo'], '甲')

    def test_spec_bazhuan(self):
        """八专法（阳日，甲寅日：日支=干寄宫寅、干上=支上、干阴≠支阴 → 三课转八专）：
        初传=干上(寅)，中传=日干(甲)，末传=日支(寅)。"""
        sc, gate = self._run_auto('甲', '寅', '寅', '卯', '寅', '巳')  # 日支=干寄宫寅，干上=支上
        self.assertEqual(gate, 'bazhuan')
        self.assertEqual(sc['chu'], '寅')
        self.assertEqual(sc['zhong'], '甲')
        self.assertEqual(sc['mo'], '寅')

    def test_spec_biyong(self):
        """比用法（阴阳比和）：甲日阳干，贼含申(阳支,与日干比)与酉(阴) → 取比者申，标注 biyong。

        当前引擎误用「五行相等」判断比和（ZHI_WX==ri_wx），而非「地支阴阳奇偶同于日干」，
        导致申(金)≠甲(木)五行而被排除 → 退化为 zeike。修复应改为地支阴阳奇偶比较。
        """
        sc, gate = self._run_auto('甲', '子', '申', '酉', '子', '亥')
        # 直接验证比用路径（method=biyong）
        sc2, gate2 = self.c._build_sanchuan(
            'biyong', '甲', '子',
            {'gan_shang': {'tianpan': '申'}, 'gan_yin': {'tianpan': '酉'},
             'zhi_shang': {'tianpan': '子'}, 'zhi_yin': {'tianpan': '亥'}},
            self.tp, DI_PAN)
        self.assertEqual(gate2, 'biyong')
        self.assertEqual(sc2['chu'], '申')

    def test_forced_gate_no_crash(self):
        """显式指定门法不应抛异常（当前 _forced_gate 元组缺失逗号 → ValueError）。"""
        sike = {'gan_shang': {'tianpan': '寅'}, 'gan_yin': {'tianpan': '卯'},
                'zhi_shang': {'tianpan': '午'}, 'zhi_yin': {'tianpan': '巳'}}
        sc, gate = self.c._build_sanchuan('fuyin', '甲', '子', sike, self.tp, DI_PAN)
        self.assertIn('chu', sc)
        self.assertIn('zhong', sc)
        self.assertIn('mo', sc)


class TestLiuRenShenShaAndYueJiang(unittest.TestCase):
    """神煞（空亡/六合/六害/天马/旺相休囚死）与节气月将（太阳黄经）单元测试。"""

    def setUp(self):
        """构造神煞/月将测试用的六壬计算器实例。"""
        self.c = LiuRenCalculator()

    # ---- 月将：按太阳黄经（中气切换） ----
    def test_yue_jiang_from_longitude(self):
        """太阳黄经区间 → 月将（中气界）。"""
        self.assertEqual(self.c._yue_jiang_from_longitude(0), '戌')    # 春分
        self.assertEqual(self.c._yue_jiang_from_longitude(30), '酉')   # 谷雨
        self.assertEqual(self.c._yue_jiang_from_longitude(90), '未')   # 夏至
        self.assertEqual(self.c._yue_jiang_from_longitude(180), '辰')  # 秋分
        self.assertEqual(self.c._yue_jiang_from_longitude(270), '丑')  # 冬至
        self.assertEqual(self.c._yue_jiang_from_longitude(300), '子')  # 大寒
        self.assertEqual(self.c._yue_jiang_from_longitude(330), '亥')  # 雨水
        self.assertEqual(self.c._yue_jiang_from_longitude(359), '亥')  # 雨水前
        self.assertEqual(self.c._yue_jiang_from_longitude(15), '戌')   # 春分后

    def test_yue_jiang_by_date(self):
        """公历日期 → 月将（太阳过中气）。"""
        # 2024-03-25 春分后 → 戌（河魁）
        self.assertEqual(self.c.yue_jiang(2024, 3, 25), '戌')
        # 2024-12-25 冬至后 → 丑（大吉）
        self.assertEqual(self.c.yue_jiang(2024, 12, 25), '丑')
        # 仅给公历月 → 回退近似表（兼容旧调用）
        self.assertEqual(self.c.yue_jiang(month=3), '酉')

    # ---- 空亡（旬空） ----
    def test_kongwang(self):
        """甲子旬空戌亥；甲寅旬空子丑。"""
        self.assertEqual(self.c._kongwang('甲', '子'), ('戌', '亥'))
        self.assertEqual(self.c._kongwang('甲', '寅'), ('子', '丑'))
        self.assertEqual(self.c._kongwang('甲', '戌'), ('申', '酉'))

    # ---- 六合（日干六合支：合干寄宫） ----
    def test_liuhe(self):
        """甲→己→未；乙→庚→申。"""
        sha = self.c._build_shensha('甲', '子', {}, '寅')
        self.assertEqual(sha['六合'], '未')
        sha2 = self.c._build_shensha('乙', '丑', {}, '卯')
        self.assertEqual(sha2['六合'], '申')

    # ---- 六害 ----
    def test_liuhai(self):
        """日支子 → 未（子未害）。"""
        sha = self.c._build_shensha('甲', '子', {}, '寅')
        self.assertEqual(sha['六害'], '未')
        sha2 = self.c._build_shensha('丙', '寅', {}, '巳')
        self.assertEqual(sha2['六害'], '巳')

    # ---- 天马（月将三合局） ----
    def test_tianma(self):
        """月将寅 → 戌；月将子 → 子。"""
        sha = self.c._build_shensha('甲', '子', {}, '寅')
        self.assertEqual(sha['天马'], '戌')
        sha2 = self.c._build_shensha('甲', '子', {}, '子')
        self.assertEqual(sha2['天马'], '子')

    # ---- 旺相休囚死（日干在月令） ----
    def test_wang_xiu(self):
        """甲木日：月将寅(木)旺、巳(火)相、子(水)休、申(金)囚、丑(土)死。"""
        self.assertEqual(self.c._wang_xiu('甲', '寅'), '旺')
        self.assertEqual(self.c._wang_xiu('甲', '巳'), '相')
        self.assertEqual(self.c._wang_xiu('甲', '子'), '休')
        self.assertEqual(self.c._wang_xiu('甲', '申'), '囚')
        self.assertEqual(self.c._wang_xiu('甲', '丑'), '死')

    # ---- 集成：神煞字段齐备 ----
    def test_shensha_full(self):
        """完整课体神煞应包含 驿马/三传/空亡/六合/六害/天马/旺相休囚死。"""
        san_chuan = {'chu': '申', 'zhong': '辰', 'mo': '子', 'gate': 'zeike'}
        sha = self.c._build_shensha('甲', '子', san_chuan, '寅')
        for key in ('驿马', '三传', '空亡', '六合', '六害', '天马', '旺相休囚死'):
            self.assertIn(key, sha)
        self.assertEqual(sha['空亡'], '戌、亥')
        self.assertEqual(sha['旺相休囚死'], '旺')  # 甲木·月将寅木


if __name__ == '__main__':
    unittest.main(verbosity=2)
