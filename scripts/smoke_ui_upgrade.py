# -*- coding: utf-8 -*-
"""
scripts/smoke_ui_upgrade.py — UI 升级离屏冒烟（M1–M7 验收）

在 offscreen 平台下构造 UI 升级清单引入的全部新组件，验证：
  M1 设计令牌（Colors 语义化 / Spacing 8-4 / Fonts 7 级 / Stylesheets 附加）
  M2 图表模块可导入（matplotlib 缺失时跳过而非失败）
  M3 TLabel 8 级工厂 + FONT_SCALE QSS 非空
  M4 ListItem / Badge / EmptyState / LoadingState / ErrorState
  M5 IconButton / DataCard / DIALOG QSS / 按钮 6 态 / 输入 4 态
  M6 animation 令牌 + CollapsibleCard 折叠动画
  M7 对比度审计（独立脚本，此处仅校验色值合法）

用法：
    python scripts/smoke_ui_upgrade.py
退出码：0 = 全通过；1 = 存在失败项。
"""
import os
import sys
import traceback

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# matplotlib 验证便利路径：本机安装到 build/vendor_libs 时，M2 图表检查可真实执行
_VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'build', 'vendor_libs')
if os.path.isdir(_VENDOR):
    sys.path.insert(0, _VENDOR)

_results = []


def check(name, fn):
    """执行单项检查，记录通过/失败。"""
    try:
        fn()
        _results.append((name, True, ''))
        print(f"  [OK]   {name}")
    except Exception as e:  # noqa: BLE001
        _results.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"  [FAIL] {name} -> {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)


def main():
    from PySide6.QtWidgets import QApplication
    # 仅确保 Qt app 实例存在（offscreen 平台已设置）；返回值未消费。
    QApplication.instance() or QApplication(sys.argv)
    print("=== UI 升级离屏冒烟 (M1–M7) ===")

    # ---------- M1 设计令牌 ----------
    from ui.styles import Colors, Fonts, Spacing, Stylesheets

    def m1_semantic():
        for attr in ('BRAND', 'ACCENT', 'SEMANTIC_SUCCESS', 'SEMANTIC_WARNING',
                     'SEMANTIC_DANGER', 'SEMANTIC_INFO', 'DANGER_DARK'):
            assert getattr(Colors, attr), f"Colors.{attr} 缺失"
        # 旧名降级为别名，值须与语义名一致
        assert Colors.QINGHUA == Colors.BRAND
        assert Colors.LIUJIN == Colors.BRAND
        assert Colors.ZHUSHA == Colors.ACCENT

    def m1_spacing():
        for i in range(9):
            v = getattr(Spacing, f'S{i}')
            assert isinstance(v, int), f"Spacing.S{i} 应为 int，实为 {type(v)}"
        assert Spacing.S0 == 0 and Spacing.S8 == 48
        # 圆角令牌（整数版命名：XS/SM_INT/INT/LG_INT/XL_INT/PILL）
        # 注：SM 的整数版为 RADIUS_SM_INT，避免被下方字符串别名 RADIUS_SM='6px' 覆盖
        for r in ('RADIUS_XS', 'RADIUS_SM_INT', 'RADIUS_INT',
                  'RADIUS_LG_INT', 'RADIUS_XL_INT', 'RADIUS_PILL'):
            v = getattr(Spacing, r)
            assert isinstance(v, int), f"Spacing.{r} 应为 int，实为 {type(v).__name__}={v!r}"
        assert Spacing.RADIUS_PILL == 999

    def m1_fonts():
        for lv in ('FS_HERO', 'FS_H1', 'FS_H2', 'FS_H3',
                   'FS_BODY', 'FS_CAPTION', 'FS_MICRO'):
            v = getattr(Fonts, lv)
            assert isinstance(v, int), f"Fonts.{lv} 应为 int"
        assert Fonts.FS_HERO > Fonts.FS_MICRO
        assert str(Fonts.W_BOLD) in ('600', '700')

    def m1_stylesheets():
        assert Stylesheets.FONT_SCALE, "Stylesheets.FONT_SCALE 为空（M3 注入失败）"
        for attr in ('DIALOG',):
            assert getattr(Stylesheets, attr), f"Stylesheets.{attr} 缺失"
        for attr in ('BTN_6STATE_PRIMARY', 'BTN_6STATE_SECONDARY',
                     'BTN_6STATE_GHOST', 'BTN_6STATE_DANGER', 'INPUT_4STATE'):
            assert getattr(Stylesheets, attr), f"Stylesheets.{attr} 缺失"

    check('M1 Colors 语义化命名 + 别名', m1_semantic)
    check('M1 Spacing 8-4 基准', m1_spacing)
    check('M1 Fonts 7 级 Scale', m1_fonts)
    check('M1 Stylesheets 附加（FONT_SCALE/DIALOG/BTN/INPUT）', m1_stylesheets)

    # ---------- M3 TLabel 排版 ----------
    def m3_tlabel():
        from ui.components.typography import TLabel
        for lv in ('hero', 'h1', 'h2', 'h3', 'body', 'caption', 'micro', 'value'):
            lbl = getattr(TLabel, lv)('测试文本')
            assert lbl.objectName() == f't-{lv}', \
                f"TLabel.{lv} objectName={lbl.objectName()} 期望 t-{lv}"
            assert lbl.text() == '测试文本'

    check('M3 TLabel 8 级工厂', m3_tlabel)

    # ---------- M4 列表 / 徽章 / 三态 ----------
    def m4_listitem():
        from ui.components.list_item import ListItem
        it = ListItem(icon='◆', title='主标题', subtitle='副标题',
                      value='42', badge_color='success')
        it.setProperty('state', 'hover')
        assert it.property('state') == 'hover'
        assert it.height() >= 0

    def m4_badge():
        from ui.components.badge import Badge
        for sem in ('success', 'danger', 'warning', 'info', 'brand', 'accent'):
            b = Badge('标签', semantic=sem)
            # Badge 刻意在文本首尾加空格做药丸内边距
            assert b.text().strip() == '标签'
            b.set_text('更新')
            assert b.text().strip() == '更新'

    def m4_states():
        from ui.components.states import EmptyState, LoadingState, ErrorState
        EmptyState.empty('暂无排盘记录')
        LoadingState('正在推演…', '请稍候')
        ErrorState.of('AI 推演失败', '网络异常')

    check('M4 ListItem 4 态', m4_listitem)
    check('M4 Badge 6 语义色', m4_badge)
    check('M4 EmptyState/LoadingState/ErrorState', m4_states)

    # ---------- M5 图标按钮 / 数据卡 ----------
    def m5_iconbutton():
        from ui.components.icon_button import IconButton
        btn = IconButton(icon_name='copy', tooltip='复制结果')
        assert btn.toolTip() == '复制结果'
        assert btn.accessibleName(), "IconButton 缺少 accessibleName（A11y）"

    def m5_datacard():
        from ui.components.data_card import DataCard
        DataCard(title='综合评分', value='88', unit='分', badge='吉')

    def m5_icons():
        from ui.components.icons import icon
        # 缺失图标须回退不崩溃
        ic = icon('__not_exist__', size=24)
        assert ic is not None
        icon('copy', size=16)

    check('M5 IconButton 6 态 + A11y', m5_iconbutton)
    check('M5 DataCard', m5_datacard)
    check('M5 icons 回退不崩溃', m5_icons)

    # ---------- M6 动效 ----------
    def m6_animation():
        from ui import animation as A
        from PySide6.QtCore import QEasingCurve
        assert A.EASING_STANDARD == QEasingCurve.InOutCubic
        assert A.DURATION_NORMAL == 300
        assert A.DURATION_INSTANT == 100
        assert isinstance(A.ANIMATION_MAP, dict) and A.ANIMATION_MAP

    def m6_collapsible():
        from ui.components.collapsible_card import CollapsibleCard
        card = CollapsibleCard('测试分组')
        card.toggle()
        card.toggle()

    check('M6 animation 令牌', m6_animation)
    check('M6 CollapsibleCard 折叠动画', m6_collapsible)

    # ---------- M2 图表（matplotlib 可选） ----------
    def m2_chart():
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            print("       (跳过：本环境无 matplotlib)")
            return
        from ui.components.ai_metrics_chart import AIMetricsChart
        AIMetricsChart()

    check('M2 图表模块（可选依赖）', m2_chart)

    # ---------- M7 色值合法性 ----------
    def m7_colors():
        import re
        pat = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for name in dir(Colors):
            if name.startswith('_'):
                continue
            v = getattr(Colors, name)
            if isinstance(v, str) and v.startswith('#'):
                assert pat.match(v), f"Colors.{name}={v} 非合法 #RRGGBB"

    check('M7 Colors 色值合法（#RRGGBB）', m7_colors)

    # ---------- 汇总 ----------
    total = len(_results)
    passed = sum(1 for _, ok, _ in _results if ok)
    print('-' * 52)
    if total == 0:
        print("smoke_ui_upgrade: ⚠️ 未执行任何检查（0/0 假绿）❌")
        return 1
    if passed == total:
        print(f"smoke_ui_upgrade: {passed}/{total} 全通过 ✅")
        return 0
    print(f"smoke_ui_upgrade: {passed}/{total} 通过，{total - passed} 失败 ❌")
    for name, ok, err in _results:
        if not ok:
            print(f"  - {name}: {err}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
