# -*- coding: utf-8 -*-
"""
ui/animation.py — 统一动效令牌（缓动曲线 + 时长常量）

UI 升级方案 M6：所有动效参数收敛到本模块，作为全项目「动效真相源」。
组件（CollapsibleCard / ListItem / 卡片 hover / AI 流式 / 板块切换）统一引用
本模块的 EASING_* 与 DURATION_* 常量，禁止各自硬编码时长/缓动。

规范（对齐实施计划阶段 6）：
    - 默认过渡      300ms  IN_OUT_CUBIC（EASING_STANDARD）
    - 消失          入向   IN_CUBIC（EASING_IN）
    - 出现          出向   OUT_CUBIC（EASING_OUT）
    - 键盘/即时反馈 100ms  LINEAR
    - hover 切换   200ms
    - 卡片折叠     300ms  IN_OUT_CUBIC
    - 页面切换     500ms
"""
from PySide6.QtCore import QEasingCurve

# ===== 缓动曲线（统一） =====
EASING_STANDARD = QEasingCurve.InOutCubic   # 默认过渡（进出对称）
EASING_IN = QEasingCurve.InCubic            # 消失 / 离场
EASING_OUT = QEasingCurve.OutCubic          # 出现 / 入场
EASING_LINEAR = QEasingCurve.Linear         # 线性（hover 背景/即时反馈）
EASING_OVERSHOOT = QEasingCurve.OutBack     # 弹性回弹（数值弹跳等点缀）

# ===== 时长常量（毫秒，统一） =====
DURATION_INSTANT = 100     # 键盘反馈 / 即时响应
DURATION_FAST = 200        # hover 切换
DURATION_NORMAL = 300      # 默认动画（卡片折叠、板块切换）
DURATION_SLOW = 500        # 卡片折叠（长内容）
DURATION_SLOWER = 800      # 页面切换 / 大区块过渡

# ===== 应用映射（组件 → 属性/时长/缓动） =====
# 供审计脚本与组件文档引用，集中登记每类动效的规范参数。
ANIMATION_MAP = {
    'collapsible_height': {'property': 'maximumHeight', 'duration': DURATION_NORMAL, 'easing': EASING_STANDARD},
    'list_item_bg':       {'property': 'background',    'duration': DURATION_INSTANT, 'easing': EASING_LINEAR},
    'card_shadow_hover':  {'property': 'color',         'duration': DURATION_FAST, 'easing': EASING_IN},
    'ai_stream_append':   {'property': 'opacity',        'duration': DURATION_INSTANT, 'easing': EASING_LINEAR},
    'section_switch':     {'property': 'opacity',        'duration': DURATION_NORMAL, 'easing': EASING_STANDARD},
    'timeline_hover':     {'property': 'scale',          'duration': DURATION_FAST, 'easing': EASING_OUT},
}
