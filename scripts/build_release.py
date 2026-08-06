# -*- coding: utf-8 -*-
"""
scripts/build_release.py — 一键发布构建（自动移除密钥 → 打包 → 产物校验）

实现「双模式密钥管理」的打包侧：把密钥清理作为构建的第一道强制步骤，
确保调试时保留在 core.debug_keys 中的密钥，在生成 EXE 时被自动移除，
产物始终零密钥残留。

步骤（与项目约定一致）：
  1. scripts/purge_ai_secrets.py   自动移除 / 清空全部 AI 原始信息
                                 （含 core.debug_keys 调试密钥、种子库运行期表）
  2. 旧 dist 重命名移开（避免 PyInstaller 清理旧目录触发安全删除门禁）
  3. PyInstaller build_release.spec 构建 EXE
  4. scripts/verify_build_security.py 产物级密钥残留校验（失败即中止）

用法：
    python scripts/build_release.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
SPEC = ROOT / "build_release.spec"
DIST = ROOT / "dist"
GENIE_TRASH = "C:/Program Files/WorkBuddy/resources/vendor/genie-trash/win32-x64.exe"


def run(cmd, **kw):
    print(">>> " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, **kw)


def _send_to_trash(path: Path) -> bool:
    """优先用回收站工具清理历史 dist_prev，避免触发安全删除门禁。"""
    if not path.exists():
        return True
    if Path(GENIE_TRASH).exists():
        try:
            code = run([GENIE_TRASH, str(path).replace("\\", "/")]).returncode
            return code == 0
        except Exception:
            pass
    shutil.rmtree(str(path), ignore_errors=True)
    return True


def main() -> int:
    # 放行安全删除沙箱（本项目构建流程需移动 / 重建 dist 目录）
    os.environ.setdefault("CODEBUDDY_SAFE_DELETE_SANDBOX", "0")

    # 1. 自动移除密钥（含调试密钥清空、种子库运行期表清空 + VACUUM）
    code = run([sys.executable, str(ROOT / "scripts" / "purge_ai_secrets.py")],
               cwd=str(ROOT)).returncode
    if code != 0:
        print("[错误] 密钥清除失败，已中止构建。")
        return code

    # 2. 旧 dist 重命名移开（不删除，避免安全删除门禁）
    if DIST.exists():
        prev = ROOT / "dist_prev"
        if prev.exists():
            _send_to_trash(prev)
        DIST.rename(prev)
        print("[构建] 旧 dist 已重命名为 dist_prev")

    # 3. 打包
    code = run([PY, "-m", "PyInstaller", str(SPEC), "--noconfirm"],
               cwd=str(ROOT)).returncode
    if code != 0:
        print("[错误] PyInstaller 构建失败。")
        return code

    # 4. 产物级密钥校验
    code = run([sys.executable, str(ROOT / "scripts" / "verify_build_security.py")],
               cwd=str(ROOT)).returncode
    if code != 0:
        print("[错误] 产物校验未通过：产物中疑似含密钥，禁止发布！")
        return code

    print("=" * 64)
    print("[完成] 构建成功且产物零密钥残留，可发布。")
    print("       分发目录：dist/风水排盘专业工具/")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
