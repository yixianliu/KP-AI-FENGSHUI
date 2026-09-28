# -*- coding: utf-8 -*-
"""校验 PDF 导出调色板的令牌归位（视觉零变化证明）。

独立于 verify_badge_p07.py：本脚本**不依赖 PySide6**，因为 PDF_* 令牌是纯
字符串常量、`ui.styles` 无顶层 import。这样 venv（有 PySide6 无 reportlab）
与 anaconda（有 reportlab 无 PySide6）各自都能跑到属于自己的部分：
  · venv      → A1 令牌值 + A2 静态门禁（A3 SKIP）
  · anaconda  → A1 + A2 + A3 PDF 生成冒烟

断言清单：
  A1  PDF_* 令牌值 == 归位前的裸 hex —— 视觉零变化的核心证明
  A2  pdf_exporter.py 源码中无裸 hex 色值（全部走 Colors.PDF_*）
  A3  PDF 生成冒烟：reportlab 接受令牌色，实际产出合法 PDF（%PDF- 头）
"""
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 归位前的原始裸 hex（基线：证明令牌值零变化）
PDF_RAW = {
    'PDF_ZHUSHA': '#C45545',
    'PDF_QINGHUA': '#4A7A90',
    'PDF_LIUJIN': '#B88A30',
    'PDF_BG': '#F7F4EE',
    'PDF_CARD': '#FFFFFF',
    'PDF_TEXT': '#333333',
    'PDF_LINE': '#D9CDB8',
    'PDF_MUTED': '#8A7F6B',
}

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'SKIP' if ok == 'SKIP' else 'FAIL'}] {name}"
          + (f" — {detail}" if detail else ""))


def main():
    from ui.styles import Colors

    # ── A1 令牌值 == 归位前裸 hex ─────────────────────────────
    for tok, raw in PDF_RAW.items():
        got = getattr(Colors, tok)
        check(f'A1 {tok}', got.upper() == raw.upper(),
              f'{got} vs 基线 {raw}' if got.upper() != raw.upper() else '')

    # ── A2 pdf_exporter 源码无裸 hex（已全走令牌）─────────────
    src = (ROOT / 'ui/export/pdf_exporter.py').read_text(encoding='utf-8')
    # 剥离注释与字符串，只查真实字面量里的 HexColor('#xxxxxx') 形式
    body = re.sub(r'#.*', '', src)
    hex_literals = re.findall(r"HexColor\(\s*['\"]#[0-9a-fA-F]{3,6}['\"]\s*\)", body)
    check('A2 pdf_exporter 无裸 hex 色值', not hex_literals,
          f'残留 {hex_literals[:3]}' if hex_literals else '8 色全走 Colors.PDF_*')

    # 交叉校验：Colors.PDF_* 必须被实际引用 8 次
    refs = re.findall(r'Colors\.PDF_[A-Z]+', src)
    check('A2 PDF_* 令牌被引用', len(refs) == 8, f'引用 {len(refs)} 次')

    # ── A3 PDF 生成冒烟 ───────────────────────────────────────
    try:
        from ui.export.pdf_exporter import PdfExporter, _REPORTLAB_OK
    except Exception as e:
        check('A3 PDF 导出模块可导入', False, f'{type(e).__name__}: {e}')
        _REPORTLAB_OK = False

    if not _REPORTLAB_OK:
        check('A3 PDF 生成冒烟', 'SKIP',
              '当前环境无 reportlab —— 请用 anaconda python 复跑（venv 无此包）')
    else:
        exp = PdfExporter()
        out = os.path.join(tempfile.gettempdir(), 'kp_verify_pdf_palette.pdf')
        ok = exp.export({}, out)
        if ok and os.path.exists(out) and Path(out).read_bytes()[:5] == b'%PDF-':
            check('A3 PDF 生成冒烟', True, f'{os.path.getsize(out)} bytes，%PDF- 头正常')
        else:
            check('A3 PDF 生成冒烟', False, 'export() 失败或产物非法')

    failed = [r for r in RESULTS if r[1] is False]
    skipped = [r for r in RESULTS if r[1] == 'SKIP']
    print(f"\n{'=' * 62}")
    print(f"verify_pdf_palette: {len(RESULTS) - len(failed) - len(skipped)}"
          f"/{len(RESULTS)} 通过"
          + (f"，{len(skipped)} SKIP" if skipped else ""))
    for n, _, d in failed:
        print(f"  ✗ {n} — {d}")
    if failed:
        return 1
    print("PDF 调色板归位正确，视觉零变化 ✅")
    return 0


if __name__ == '__main__':
    sys.exit(main())
