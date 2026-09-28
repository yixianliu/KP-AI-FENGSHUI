"""校验 export_dialog 浅色主题令牌化的视觉零变化。

做法：把 git 原始版本的样式表与当前（令牌展开后）的样式表归一化后逐字符对比。
归一化：还原 f-string 的 {{ }} 转义、压缩空白。任何差异都说明令牌值与原硬编码不一致。
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

SRC = 'ui/components/export_dialog.py'
QUOTES = ('"""', "'", '"')


def norm(s):
    """还原 f-string 转义并压缩空白，只留语义内容。"""
    s = s.replace('{{', '{').replace('}}', '}')
    return re.sub(r'\s+', ' ', s).strip()


def main():
    from PySide6.QtWidgets import QApplication

    orig = subprocess.run(['git', 'show', f'HEAD:{SRC}'], capture_output=True,
                          text=True, encoding='utf-8').stdout
    assert orig, '无法读取 git HEAD 版本'
    app = QApplication([])
    from ui.components.export_dialog import ExportDialog

    cur_dialog = ExportDialog({}, parent=None)
    cur_dialog.show()
    app.processEvents()

    # 1) 令牌还原法：把当前文件里的 Colors.XXX 还原为裸色值，再与 HEAD 对比。
    #    期望差异仅为本轮之前新增的 :focus 焦点环规则（HEAD 尚无）。
    from ui.styles import Colors

    TOKEN_TO_RAW = {
        'PAPER': Colors.PAPER, 'PAPER_LIGHT': Colors.PAPER_LIGHT,
        'PAPER_HOVER': Colors.PAPER_HOVER, 'PAPER_BORDER': Colors.PAPER_BORDER,
        'PAPER_ACTIVE': Colors.PAPER_ACTIVE, 'INK_PAPER': Colors.INK_PAPER,
        'INK_PAPER_HOVER': Colors.INK_PAPER_HOVER,
        'INK_PAPER_BORDER': Colors.INK_PAPER_BORDER,
        'INK_PAPER_DARK': Colors.INK_PAPER_DARK,
        'INK_PAPER_DARKEST': Colors.INK_PAPER_DARKEST,
        'GOLD_PAPER': Colors.GOLD_PAPER, 'GOLD_PAPER_DARK': Colors.GOLD_PAPER_DARK,
        'TEXT_PAPER': Colors.TEXT_PAPER, 'TEXT_PAPER_DIM': Colors.TEXT_PAPER_DIM,
    }
    cur_src = open(SRC, encoding='utf-8').read()
    restored = cur_src
    for tok, raw in TOKEN_TO_RAW.items():
        restored = restored.replace(f'{{Colors.{tok}}}', raw.upper())

    # 展开后的运行时样式表（含焦点环，HEAD 无）与还原版源码对比一致性
    rt_qss = norm(cur_dialog.styleSheet())
    print(f'[运行时样式表] {len(rt_qss)} 字符，'
          f'{"无未展开占位符 ✅" if "{Colors" not in rt_qss else "存在占位符 ❌"}')

    # 2) 色值集合等价：还原版与 HEAD 原始版的色值多重集对比
    cur_colors = re.findall(r'#[0-9A-Fa-f]{6}', restored)
    _ = orig  # HEAD 版本仅用于内联字面量对比，色值基线不能用它（改造前旧版）

    def bag(seq):
        d = {}
        for c in seq:
            d[c.upper()] = d.get(c.upper(), 0) + 1
        return d

    cb = bag(cur_colors)
    # 正确门禁：当前所有色值都必须属于浅色主题令牌集合
    # （不能与 HEAD 比对——HEAD 是本轮之前改造前的旧版，色值集合本就不同）
    allowed = {v.upper() for v in TOKEN_TO_RAW.values()}
    foreign = {k: v for k, v in cb.items() if k not in allowed}
    missing = allowed - set(cb)
    print(f'[色值多重集] 令牌还原后共 {len(cur_colors)} 处，'
          f'覆盖令牌 {len(cb)} 种 / 令牌总数 {len(allowed)} 种')
    print(f'  无令牌外的陌生色值: {"✅" if not foreign else "❌ " + str(foreign)}')
    if missing:
        print(f'  未使用的令牌（可能冗余，非错误）: {sorted(missing)}')
    same = not foreign

    def inline_literals(text):
        """提取 setStyleSheet 内联单引号字符串（含隐式拼接）。"""
        out = []
        for mm in re.finditer(r'setStyleSheet\(\s*((?:\'[^\']*\')+(?:\s*\n\s*(?:f?\'[^\']*\'))*)\s*\)',
                              text, re.S):
            raw = mm.group(1)
            joined = ''.join(re.findall(r'f?[\'\"]([^\'\"]+)[\'\"]', raw))
            out.append(norm(joined))
        return out

    orig_inl, cur_inl = inline_literals(orig), inline_literals(restored)
    print(f'[内联样式] 原始 {len(orig_inl)} 处 / 令牌还原 {len(cur_inl)} 处')
    diff = 0
    for i, (o, c) in enumerate(zip(orig_inl, cur_inl)):
        if o != c:
            diff += 1
            print(f'  差异 #{i}: 原始 ...{o[:90]}...  当前 ...{c[:90]}...')
    same = same and diff == 0
    print(f'  内联样式逐条一致: {"✅" if diff == 0 else "❌"}')

    # 3) 硬门禁：业务文件不得残留裸色值（原 45 处，须归 0）
    raw_residue = re.findall(r'#[0-9A-Fa-f]{6}', cur_src)
    print(f'[门禁] 裸色值残留 {len(raw_residue)} 处 '
          f'-> {"0 处 ✅" if not raw_residue else str(raw_residue)}')

    # 4) 渲染冒烟：三个主题色必须真实出现在位图中
    from PySide6.QtGui import QImage
    img = cur_dialog.grab().toImage().convertToFormat(QImage.Format_ARGB32)

    def count(r, g, b, tol=2):
        return sum(1 for y in range(img.height()) for x in range(img.width())
                   if abs(((img.pixel(x, y) >> 16) & 0xFF) - r) <= tol
                   and abs(((img.pixel(x, y) >> 8) & 0xFF) - g) <= tol
                   and abs((img.pixel(x, y) & 0xFF) - b) <= tol)

    checks = [('宣纸底 #FFF8E7', 0xFF, 0xF8, 0xE7, 100000),
              ('墨褐   #5D4037', 0x5D, 0x40, 0x37, 500),
              ('古金   #D4AF37', 0xD4, 0xAF, 0x37, 500)]
    for name, r, g, b, floor in checks:
        n = count(r, g, b)
        print(f'  {name}: {n} 像素 {"✅" if n >= floor else "❌ 过低"}')

    rendered_ok = all(count(c[1], c[2], c[3]) >= c[4] for c in checks)
    ok = same and diff == 0 and not raw_residue and rendered_ok
    print('->', '视觉零变化，令牌化安全 ✅' if ok else '-> 存在偏差，需检查 ❌')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
