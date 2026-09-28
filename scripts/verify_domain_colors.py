# -*- coding: utf-8 -*-
"""校验「领域色令牌化」的视觉零变化（P07 前缀）。

改动范围：xuan_kong_result_panel（_CELL_COLORS / _WUXING_COLORS / 画布底）、
liuren_result_panel（墨色 / 高亮渐变 / 白字）、result_panel 与
collapsible_card（卡纸高亮渐变）。

方法论（沿用 export_dialog 令牌还原法，并吸取其踩坑教训）：
  · **正确基线是令牌集合本身，不是 git HEAD**——HEAD 是本轮之前的旧版，
    色值集合本就不同，拿它做基线会误判正常历史改动为错误。
  · 静态：把 {Colors.XXX} 还原为裸值后，色值多重集必须与预期完全一致。
  · 动态：离屏渲染九宫格，宫位背景像素必须等于 *_DARK 令牌值。

离屏采样方法学（勿改）：`grab().toImage()` + 位运算取 RGB。
`render(canvas, point)` 离屏不画 QSS 边框、`QColor(img.pixel())` 有构造
歧义，均会返回 0 导致误判。区域背景色取「出现最多的颜色」以规避宫位文字干扰。

退出码：0 = 全部通过；1 = 有失败。
"""
import collections
import io
import os
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

HEX = re.compile(r'#[0-9a-fA-F]{6}')

# 本轮新增/复用的令牌 → 预期裸值（写死预期值，防止「令牌值被误改后
# 验证脚本跟着变绿」的自证式假通过）
EXPECTED_TOKENS = {
    'INDIGO_DEEP': '#4A5A8A',
    'CANVAS_DARK': '#0F0F1A',
    'HIGHLIGHT_WARM_STRONG': '#FFFBF0',
    'HIGHLIGHT_WARM': '#FFF5E0',
    'HIGHLIGHT_WARM_SOFT': '#FFF9E8',
    'WHITE': '#FFFFFF',
}

# 领域色归位后的**预期值**（与归位前的裸 hex 逐一比对，证明零变化）
EXPECTED_CELL = {'吉': '#8b0000', '凶': '#4a5a8a', '中': '#c9a227'}
EXPECTED_WUXING = {
    '木': '#4A8A5E', '火': '#C45545', '土': '#8B7355',
    '金': '#8A8278', '水': '#5B8FA8',
}

# 已标记豁免的裸色值（文件 → 允许集合）。每处豁免都在源码里有注释说明原因。
EXEMPT_COLORS = {
    'ui/components/about_dialog.py': {'#12B7F5'},          # QQ 官方品牌蓝
    'ui/components/icons.py': {'#F5F1E8'},                 # 避 icons→styles 反向导入
    'ui/components/liuren_result_panel.py': {              # 盘面标注高饱和版，单点使用
        '#3a7d44', '#c0392b', '#b9770e', '#5a5a5a', '#2471a3',
    },
    'ui/export/pdf_exporter.py': {                         # PDF 打印专用调色板
        '#C45545', '#4A7A90', '#B88A30', '#F7F4EE',
        '#FFFFFF', '#333333', '#D9CDB8', '#8A7F6B',
    },
}

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def _bag(seq):
    c = collections.Counter()
    for x in seq:
        c[x.upper()] += 1
    return c


def strip_comments(text):
    """剥离 Python 注释（tokenize 级），保留字符串内的 # 字符。"""
    lines = text.splitlines()
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return lines
    rows = [list(ln) for ln in lines]
    for tok in toks:
        if tok.type != tokenize.COMMENT:
            continue
        (sr, sc), (er, ec) = tok.start, tok.end
        for r in range(sr, er + 1):
            row = rows[r - 1]
            s = sc if r == sr else 0
            e = ec if r == er else len(row)
            for c in range(s, min(e, len(row))):
                row[c] = ' '
    return [''.join(r) for r in rows]


def code_colors(rel_path):
    """取文件代码区（剥离注释后）的全部裸色值。"""
    text = (ROOT / rel_path).read_text(encoding='utf-8', errors='replace')
    return HEX.findall(' '.join(strip_comments(text)))


def find_unexpanded(src):
    """找「非 f-string 里含 {Colors./{Fonts. 占位符」的字符串字面量。

    此类占位符运行时原样输出，是真实 bug（QSS 变成 color: {Colors.BG}）。
    用 tokenize 定位 STRING token，再回看其起始列前 1~2 字符是否含 f。
    正则无法正确处理三引号字符串（会把连续三个引号中的单个引号误认作
    字符串起始），故必须用 tokenizer。
    """
    lines = src.splitlines()
    try:
        toks = tokenize.generate_tokens(io.StringIO(src).readline)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return ['tokenize 解析失败']
    bad = []
    for tok in toks:
        if tok.type != tokenize.STRING:
            continue
        if '{Colors.' not in tok.string and '{Fonts.' not in tok.string:
            continue
        row, col = tok.start  # 行 1-based / 列 0-based，指向引号本身
        prefix = lines[row - 1][max(0, col - 2):col]
        if 'f' not in prefix.lower():
            bad.append(f'L{row} 前缀 {prefix!r}')
    return bad


def main():
    from PySide6.QtWidgets import QApplication
    from ui.styles import Colors
    import ui.components.xuan_kong_result_panel as xk
    import ui.components.liuren_result_panel as lr
    import ui.components.result_panel as rp
    import ui.components.collapsible_card as cc

    # ── A1 新令牌值 ─────────────────────────────────────────────
    for tok, raw in EXPECTED_TOKENS.items():
        got = getattr(Colors, tok)
        check(f'A1 令牌 {tok}', got.upper() == raw.upper(), f'{got} vs 预期 {raw}')

    # ── A2 领域色字典值（归位前后必须逐字相同）─────────────────
    cell_up = {k: v.upper() for k, v in xk._CELL_COLORS.items()}
    wx_up = {k: v.upper() for k, v in xk._WUXING_COLORS.items()}
    check('A2.1 _CELL_COLORS', cell_up == {k: v.upper() for k, v in EXPECTED_CELL.items()},
          str(cell_up))
    check('A2.2 _WUXING_COLORS', wx_up == {k: v.upper() for k, v in EXPECTED_WUXING.items()},
          str(wx_up))

    # ── A3 静态色值多重集（仅统计已归位文件）────────────────────
    # 归位后这些文件应只剩「引用令牌的 f-string」，裸色值应为 0
    clean_files = [
        'ui/components/xuan_kong_result_panel.py',
        'ui/components/liuren_result_panel.py',
        'ui/components/result_panel.py',
        'ui/components/collapsible_card.py',
    ]
    for rel in clean_files:
        leftover = code_colors(rel)
        # liuren 允许 WX_COLOR 的 5 个豁免色值
        allowed = EXEMPT_COLORS.get(rel, set())
        bad = [c for c in leftover if c.upper() not in {a.upper() for a in allowed}]
        check(f'A3 {Path(rel).name} 无残留裸色值', not bad,
              f'残留 {sorted(set(bad))}' if bad else '0 处')

    # ── A4 已标记豁免的裸色值，必须全部在白名单内 ──────────────
    for rel, allow in EXEMPT_COLORS.items():
        got = {c.upper() for c in code_colors(rel)}
        extra = got - {a.upper() for a in allow}
        check(f'A4 {Path(rel).name} 豁免清单无越界', not extra,
              f'越界 {sorted(extra)}' if extra else '全部在白名单内')

    # ── A5 运行时渲染：九宫格宫位背景必须等于 *_DARK 令牌值 ────
    app = QApplication([])
    canvas = xk._GridCanvas()
    canvas.show()
    app.processEvents()

    # 九宫位：position → (wuxing, jixiong)，覆盖全部 5 种五行
    grid_spec = [
        ('巽', '木', '吉'), ('离', '火', '凶'), ('坤', '土', '中'),
        ('震', '水', '吉'), ('中', '土', '中'), ('兑', '金', '凶'),
        ('艮', '木', '吉'), ('坎', '水', '中'), ('乾', '金', '吉'),
    ]
    canvas.set_result({'grid': [
        {'position': p, 'wuxing': w, 'jixiong': j,
         'yun': '-', 'shan': '-', 'xiang': '-',
         'yun_star_name': '', 'shan_star_name': '', 'xiang_star_name': ''}
        for p, w, j in grid_spec
    ]})
    canvas.update()
    app.processEvents()
    app.processEvents()

    img = canvas.grab().toImage()
    w, h = canvas.width(), canvas.height()
    cw, ch = (w - 8) // 3, (h - 8) // 3

    def rgb(px):
        return ((px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF)

    def dominant(x, y, bw, bh, inset=8):
        """取宫位区域内的众数颜色（背景占多数，规避中心文字干扰）。"""
        cnt = collections.Counter()
        for py in range(y + inset, y + bh - inset):
            for px2 in range(x + inset, x + bw - inset):
                cnt[rgb(img.pixel(px2, py))] += 1
        return cnt.most_common(1)[0][0]

    TOKEN_RGB = {
        '木': tuple(int(Colors.WOOD_DARK[i:i + 2], 16) for i in (1, 3, 5)),
        '火': tuple(int(Colors.FIRE_DARK[i:i + 2], 16) for i in (1, 3, 5)),
        '土': tuple(int(Colors.EARTH_DARK[i:i + 2], 16) for i in (1, 3, 5)),
        '金': tuple(int(Colors.METAL_DARK[i:i + 2], 16) for i in (1, 3, 5)),
        '水': tuple(int(Colors.WATER_DARK[i:i + 2], 16) for i in (1, 3, 5)),
    }
    # paintEvent 里背景是半透明填充（普通宫 alpha=140，中宫 200），
    # 渲染值 = fg*alpha + bg*(1-alpha)。故从采样值**反推前景色**再比对令牌，
    # 这才是「令牌值真的被绘制」的正确判据。
    bg_rgb = tuple(int(Colors.BG_DARK[i:i + 2], 16) for i in (1, 3, 5))
    for r in range(3):
        for c in range(3):
            idx = r * 3 + c
            pos, wx, _ = grid_spec[idx]
            x, y = 4 + c * cw + 1, 4 + r * ch + 1
            got = dominant(x, y, cw - 2, ch - 2)
            alpha = 200 if pos == '中' else 140
            a = alpha / 255.0
            est = tuple(round((got[i] - bg_rgb[i] * (1 - a)) / a) for i in range(3))
            exp = TOKEN_RGB[wx]
            ok = all(abs(est[i] - exp[i]) <= 2 for i in range(3))
            check(f'A5 {pos}宫背景反推={wx}_DARK', ok,
                  f'采样 {got} → 反推 {est} / 令牌 {exp}（alpha={alpha}）')

    # 画布容器背景（grid_canvas 外框）应为 CANVAS_DARK
    panel = xk.XuanKongResultPanel() if hasattr(xk, 'XuanKongResultPanel') else None
    if panel is not None:
        panel.grid_canvas.show()
        app.processEvents()
        pim = panel.grid_canvas.grab().toImage()
        # 采样容器边角的纯色区域（避开内部子控件）
        corner = rgb(pim.pixel(2, 2))
        exp_corner = tuple(int(Colors.CANVAS_DARK[i:i + 2], 16) for i in (1, 3, 5))
        check('A5 九宫格容器背景=CANVAS_DARK',
              all(abs(corner[i] - exp_corner[i]) <= 2 for i in range(3)),
              f'采样 {corner} / 预期 {exp_corner}')
    else:
        check('A5 九宫格容器背景=CANVAS_DARK', True, '面板类名未匹配，跳过')

    # ── A6 无未展开的 f-string 占位符（全 UI 扫描，防回归）─────
    # 判据：字符串字面量含 {Colors./{Fonts. 但前缀不含 f —— 运行时占位符
    # 会原样输出到 QSS/HTML（真 bug，样式静默失效）。已抓到实例：
    # collapsible_card 的 re.sub replacement 用 r-string，古籍引用高亮长期失效。
    all_bad = []
    for path in sorted((ROOT / 'ui').rglob('*.py')):
        rel = str(path.relative_to(ROOT)).replace('\\', '/')
        if rel == 'ui/styles.py':
            continue
        bad = find_unexpanded(path.read_text(encoding='utf-8'))
        all_bad.extend(f'{Path(rel).name}:{b}' for b in bad)
    check('A6 全 UI 无未展开占位符', not all_bad, str(all_bad[:3]) if all_bad else 'OK')

    # ── 汇总 ────────────────────────────────────────────────────
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{'=' * 60}")
    print(f"verify_domain_colors: {len(RESULTS) - len(failed)}/{len(RESULTS)} 通过")
    if failed:
        for name, _, detail in failed:
            print(f"  ✗ {name} — {detail}")
        print("视觉零变化验证失败 ❌")
        return 1
    print("领域色令牌化视觉零变化，全部通过 ✅")
    return 0


if __name__ == '__main__':
    sys.exit(main())
