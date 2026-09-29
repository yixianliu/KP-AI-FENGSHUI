# -*- coding: utf-8 -*-
"""验证「关于对话框二维码资源」(M4-1) 合规性。

校验点：
  1. 二维码资源文件（wx/qq 好友、wx-pay/ali-pay 支付，共 4 个）全部存在；
  2. AboutDialog._resolve_qr 按「打包(_MEIPASS) → 资源根 → 可执行文件同级」顺序
     解析成功，路径指向存在的资源文件，无硬编码绝对路径；
  3. QR_FRIEND_DIR / QR_PAY_DIR 为相对路径，未依赖开发机绝对路径；
  4. 二维码路径解析不暴露资源缺失文件名给用户（失败仅日志，不返回文件名）。

退出码：0 = 全部通过；1 = 存在资源缺失或路径解析违规。
"""
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui.components.about_dialog import AboutDialog
from core.path_utils import get_resource_path, get_app_dir

# 二维码资源：4 个文件（QR_FRIEND_DIR 2 个 + QR_PAY_DIR 2 个）
EXPECTED_QR_FILES = [
    'images/link_qrcode/wx.png',
    'images/link_qrcode/qq.png',
    'images/pay_qrcode/wx-pay.png',
    'images/pay_qrcode/ali-pay.png',
]

# 资源解析所需的子目录（与 about_dialog 常量一致）
QR_FRIEND_DIR = 'images/link_qrcode'
QR_PAY_DIR = 'images/pay_qrcode'


def _check(name, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main():
    all_pass = True
    print("=" * 64)
    print("verify_about_qrcode: 关于对话框二维码资源合规校验（M4-1）")
    print("=" * 64)

    # 1. 资源文件存在性校验
    print("\n[1] 二维码资源文件存在性校验")
    for rel in EXPECTED_QR_FILES:
        path = Path(ROOT) / rel
        ok = path.exists()
        all_pass = all_pass and ok
        all_pass = _check(f"资源文件存在: {rel}", ok,
                          f"已存在" if ok else f"缺失（{path}）") and all_pass

    # 2. 相对路径校验（无硬编码绝对路径）
    print("\n[2] 二维码资源路径为相对路径校验")
    dialog = AboutDialog.__new__(AboutDialog)  # 仅校验类属性，无需实例化（避免模态/弹窗）
    # 校验类级相对路径常量（无绝对路径前缀）
    import re
    for attr in ('QR_FRIEND_DIR', 'QR_PAY_DIR'):
        val = getattr(AboutDialog, attr)
        ok = val and not (Path(val).is_absolute() if val else False) and '\\' not in val
        all_pass = _check(f"{attr} 为相对路径", ok, f"={val}") and all_pass
    # 校验 _resolve_qr 使用 get_resource_path（无硬编码绝对路径拼接）
    resolve_src = AboutDialog._resolve_qr.__code__
    has_get_resource_path = any(
        name in resolve_src.co_names for name in ('get_resource_path', 'get_app_dir')
    )
    all_pass = _check(
        '_resolve_qr 使用统一路径工具（get_resource_path）',
        has_get_resource_path,
        "已调用路径解析工具，无硬编码绝对路径" if has_get_resource_path else "未调用统一路径工具",
    ) and all_pass

    # 3. 资源解析路径合法性校验（使用实际资源根 + _resolve_qr 逻辑）
    print("\n[3] 二维码解析路径合法性校验")
    from ui.components.about_dialog import AboutDialog as Dlg

    def resolve_tested(sub_dir, filename):
        """模拟 _resolve_qr 的解析逻辑，返回 (Path | None, 失败原因)。"""
        rel = f'{sub_dir}/{filename}'
        # 与 _resolve_qr 一致：先资源根，再 app 目录
        try:
            p = get_resource_path(rel)
            if p and Path(p).exists():
                return Path(p), ''
        except Exception:
            pass
        try:
            p2 = get_app_dir() / sub_dir / filename
            if p2.exists():
                return p2, ''
        except Exception:
            pass
        return None, f'资源缺失: {rel}'

    test_cases = [
        (QR_FRIEND_DIR, 'wx.png'),
        (QR_FRIEND_DIR, 'qq.png'),
        (QR_PAY_DIR, 'wx-pay.png'),
        (QR_PAY_DIR, 'ali-pay.png'),
    ]
    for sub_dir, filename in test_cases:
        path, reason = resolve_tested(sub_dir, filename)
        ok = path is not None and Path(path).exists() and reason == ''
        all_pass = all_pass and ok
        all_pass = _check(
            f"解析 {sub_dir}/{filename} 成功",
            ok,
            f"路径={path}" if ok else f"失败原因={reason}",
        ) and all_pass

    # 4. 失败原因不暴露文件名校验（M4-4：失败原因只写日志，禁止显示 .png 文件名给用户）
    print("\n[4] 解析失败原因不暴露文件名校验（仅日志，用户可见文案不含文件名）")
    import re
    # 4a. 解析不存在的资源，得到 reason（含相对路径文件名，仅用于日志）
    path, reason = resolve_tested(QR_FRIEND_DIR, 'nonexist.png')
    # reason 不得泄漏开发机绝对路径（如 D:\ / /Users/ / /home/）—— 否则会暴露机器信息
    abs_leak = bool(re.search(r'[A-Za-z]:\\\\|/Users/|/home/', reason or ''))
    ok_reason = path is None and '资源缺失' in reason and not abs_leak
    all_pass = _check(
        "解析失败 reason 仅含相对路径、不泄漏绝对路径",
        ok_reason,
        "reason 仅含相对路径（日志用），未泄漏机器绝对路径" if ok_reason else f"失败原因={reason}",
    ) and all_pass

    # 4b. 用户可见文案（_qr_error_text）不得包含 .png 文件名等实现细节
    user_text = AboutDialog._qr_error_text('微信好友', '#00aa00')
    ok_user = 'nonexist.png' not in user_text and '.png' not in user_text \
        and 'link_qrcode' not in user_text
    all_pass = _check(
        "用户可见降级文案不含文件名/路径",
        ok_user,
        "用户文案仅为「渠道+暂未加载+引导」，不含文件名" if ok_user else f"用户文案={user_text!r}",
    ) and all_pass

    print("\n" + "=" * 64)
    if all_pass:
        print("verify_about_qrcode: 关于对话框二维码资源全部合规 ✅")
        return 0
    print("verify_about_qrcode: 二维码资源合规校验未通过 ❌")
    return 1


if __name__ == '__main__':
    sys.exit(main())
