# 文件移动脚本：将 core/ 根目录散落的 .py 文件移入功能子包
# 执行前请确认 git 工作区干净，便于回滚

$root = "d:\PythonProject\KP-AI-FENGSHUI"
$core = "$root\core"

# 移动到 core/bazi/
$baziFiles = @(
    "bazi_calculator.py",
    "bazi_types.py",
    "bazi_batch.py",
    "wuxing.py",
    "shishen.py",
    "mingli.py",
    "geju_analyzer.py",
    "yunshi.py",
    "yuncheng.py",
    "_baazi_compat.py"
)

# 移动到 core/divination/
$divinationFiles = @(
    "meihua.py",
    "hexagram_analyzer.py",
    "hexagram_data.py",
    "liuren.py"
)

# 移动到 core/knowledge/
$knowledgeFiles = @(
    "knowledge_base.py",
    "rag_knowledge.py",
    "analysis_storage.py",
    "analysis_fallback.py",
    "data_integration.py",
    "data_validator.py",
    "data_validator_v2.py"
)

function Move-FileGroup($files, $targetDir) {
    Write-Host "`n=== 移动到 $targetDir ===" -ForegroundColor Cyan
    foreach ($f in $files) {
        $src = Join-Path $core $f
        $dst = Join-Path $targetDir $f
        if (-not (Test-Path $src)) {
            Write-Warning "  源文件不存在: $src （可能已移动过）"
            continue
        }
        if (Test-Path $dst) {
            Write-Warning "  目标已存在: $dst （跳过）"
            continue
        }
        Move-Item -Path $src -Destination $dst
        Write-Host "  已移动: $f -> $(Split-Path $targetDir -Leaf)/"
    }
}

Move-FileGroup $baziFiles "$core\bazi"
Move-FileGroup $divinationFiles "$core\divination"
Move-FileGroup $knowledgeFiles "$core\knowledge"

Write-Host "`n=== 移动完成，验证 core/ 剩余根级 .py 文件 ===" -ForegroundColor Green
Get-ChildItem -Path $core -Filter "*.py" -File | ForEach-Object {
    Write-Host "  保留: $($_.Name)"
}

Write-Host "`n=== 各子包文件列表 ===" -ForegroundColor Green
foreach ($sub in @("bazi", "divination", "knowledge")) {
    Write-Host "`n--- core/$sub ---"
    Get-ChildItem -Path "$core\$sub" -Filter "*.py" -File | ForEach-Object {
        Write-Host "  $($_.Name)"
    }
}
