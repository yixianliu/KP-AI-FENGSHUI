# -*- coding: utf-8 -*-
"""scripts/verify_build_security.py — 已迁移的兼容薄壳（不做任何独立校验）

真正的发布门禁已迁至 tests/ui/verify_build_security.py：
  - 允许随包分发的官方公开后端（api.agnes-ai.cn / agnes-2.5-flash）；
  - 读 server/.env 做机密指纹比对；
  - 产物目录为空时判红（防空转假绿）。

本文件保留仅为兼容可能存在的外部引用，**不再维护独立规则**，运行时会
转发到权威实现并透传其退出码。这样任何仍指向本路径的自动化都能拿到正确
结论，不会因为两份规则分叉而出现「旧版把官方端点判为泄漏 / 空目录判绿」
这类误判。

用法（参数与退出码同 tests/ui 版）：
    python scripts/verify_build_security.py [--dist dist] [--env server/.env]
退出码：0 = 通过；1 = 发现机密残留；2 = 参数或环境错误 / 迁移目标缺失
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

# 权威实现位置（本项目内唯一维护点）
AUTHORITY = Path(__file__).resolve().parent.parent / "tests" / "ui" / "verify_build_security.py"


def main() -> int:
    """转发执行权威实现；目标缺失时 fail-closed 返回 2，绝不假装通过。

    Returns:
        int: 权威实现的退出码；目标缺失时返回 2。
    """
    if not AUTHORITY.exists():
        print(f"[错误] 迁移后的门禁脚本不存在：{AUTHORITY}", file=sys.stderr)
        print("[错误] 拒绝以本薄壳作为有效门禁（fail-closed）。", file=sys.stderr)
        return 2

    print(f"[提示] 本文件已迁移，转发执行权威实现：{AUTHORITY}", file=sys.stderr)
    # run_name='__main__' 触发权威实现的 sys.exit(main())，退出码原样透传
    runpy.run_path(str(AUTHORITY), run_name="__main__")
    return 0  # 正常路径上不会到达（SystemExit 已在 run_path 内抛出）


if __name__ == "__main__":
    sys.exit(main())
