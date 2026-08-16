# 风水排盘专业工具

> 传承中国传统命理学精髓的本地化专业排盘分析工具  
> 开源 · 免费 · 本地运行 · 数据不上云

---

## 目标用户

**短期用户**

- 八字、梅花易数、大六壬等术数初学者，需要规范排盘辅助入门
- 有一定基础的爱好者，希望快速校验四柱、十神、格局等基础参数
- 执业命理师，需要将排盘结果整合为可视化专业细盘用于咨询展示

**长期用户**

- 命理学研究与教学者，需要可复现、可验证的算法级排盘工具
- 文化技术从业者，希望将传统命理逻辑与现代 AI 能力结合的产品探索者
- 重视数据隐私的严肃用户，拒绝将出生时辰、出生地点等敏感信息上传至云端工具

---

## 核心痛点

1. **排盘算法门槛高**  
   节气换月、立春分界、真太阳时修正、早晚子时边界、五虎遁/五鼠遁，任何一步理解偏差都会导致四柱错误。用户无法自行验证，只能"信任工具"，缺乏透明度。

2. **云端工具不可信**  
   多数在线排盘工具要求上传出生时间、地点，甚至用于 AI 训练。用户无法确认本地算法逻辑是否正确，也无法确认自己的隐私数据如何处理。

3. **传统工具缺乏现代体验**  
   笔记本、纸笔或网页工具无法直接导出 PDF/Excel，界面过时，分析逻辑封闭不可复现，难以与教学、咨询、研究场景衔接。

4. **AI 解读昂贵且不可控**  
   市面上专业 AI 命理解读服务普遍订阅制收费，且无法自定义分析 prompt；多数工具不开放底层排盘数据接口，AI 只能"黑盒"输出。

---

## 解决方案

**KP-AI-FENGSHUI** 针对上述痛点提供一套完整、透明、本地的术数排盘与 AI 解读工作流：

### 核心技术栈

| 能力 | 实现 |
|------|------|
| 八字四柱 | 节气天文算法 + 立春年柱 + 真太阳时经度修正 + 早晚子时边界 |
| 五行 / 十神 / 格局 | 月令加权 + 藏干本气/中气/余气权重 + 专旺 / 从格 / 扶抑 / 中和四级判定 |
| 梅花易数 | 时间 / 数字 / 方位 / 文字 / 笔画 / 铜钱六种起卦方式，含体用生克与五卦联立 |
| 大六壬 | 太阳黄经月将 + 九宗门三传 + 十二天将 + 神煞系统 |
| AI 深度解读 | 可选接入龙虎山大师兄接口，以本地排盘数据为唯一输入，输出结构化 JSON 分析报告 |
| 数据导出 | PDF / Excel / CSV，支持教学存档、咨询归档 |

### 设计原则

1. **算法透明**  
   八字、神煞、纳音、六十甲子等核心数据全部源自本地 SQLite 库，用户可以查阅 `database/` 下的 schema 与 `core/` 下的计算逻辑，不依赖"黑盒"。

2. **隐私优先**  
   排盘全程本地计算，出生时间、地点、性别等数据从未离开用户设备。AI 解读为可选功能，需用户主动配置 API 密钥，且密钥经设备指纹混淆存储，不暴露明文。

3. **前后端一致**  
   底层 `core/` 算法与 `ui/` 展示层严格分离，每一次展示的柱、干、支、藏干、纳音、空亡、十神、格局均来自同一数据源，排除"算一套、画一套"的风险。

4. **学术级回归测试**  
   内置 `tests/` 含 53 项单测，锁定万年历锚点（如 1900-01-01 = 甲戌）、六壬九宗门门法、藏干权重等逻辑，确保重构与改进可回退验证。

---

## 功能特性

### 八字排盘
- 公历 / 农历输入，自动互转
- 真太阳时经度修正（可精确到分钟）
- 四柱（年 / 月 / 日 / 时）+ 藏干 + 纳音 + 空亡 + 十神
- 五行能量量化（含月令权重、藏干本气 0.6 / 中气 0.3 / 余气 0.1）
- 格局判定（专旺 / 从格 / 扶抑 / 中和）+ 特殊格局（伤官见官、官杀混杂等）
- 大运排列（顺逆由月柱阴阳与性别决定）+ 流年分析 + 十二长生

### 梅花易数
- 六种起卦方式：时间 / 数字 / 方位 / 文字 / 笔画 / 铜钱
- 本卦 + 互卦 + 变卦 + 错卦 + 综卦
- 体用生克判断、动爻分析

### 大六壬
- 太阳黄经天文算法定月将（非经验表）
- 天地盘（月将加占时）+ 四课（干上神 / 干阴 / 支上神 / 支阴）
- 九宗门三传（贼克 / 比用 / 涉害 / 昴星 / 伏吟 / 返吟 / 别责 / 八专）
- 十二天将布排 + 神煞系统（驿马 / 空亡 / 六合 / 六害 / 天马 / 旺相休囚死）

### AI 智能解读（可选）
- 可选接入龙虎山大师兄接口
- 以本地排盘数据为唯一输入，输出结构化 JSON 分析报告
- 支持八字 / 梅花 / 六壬三类分析 prompt 分支
- 本地结果缓存，避免重复请求

---

## 项目结构

```
KP-AI-FENGSHUI/
├── main.py                 # 程序入口
├── requirements.txt        # Python 依赖
├── build_release.spec      # PyInstaller 打包规格
├── pyi_rth_ssl.py          # SSL 运行时钩子（打包用）
│
├── core/                   # 业务核心层
│   ├── _baazi_compat.py    # 兼容垫片（不可删除）
│   ├── bazi_calculator.py  # 八字统一入口
│   ├── calendar_utils.py   # 真太阳时 / 节气 / 干支计算器
│   ├── geju_analyzer.py    # 格局判定（专旺/从格/扶抑/中和）
│   ├── shishen.py          # 十神能量分析
│   ├── wuxing.py           # 五行量化 + 旺衰 + 通根
│   ├── mingli.py           # 藏干 / 纳音 / 空亡 / 神煞 / 主星
│   ├── yunshi.py           # 大运流年（节气起运 + 五虎/五鼠遁）
│   ├── yuncheng.py         # 运程总结（事业/财运/健康/感情）
│   ├── sqlite_db.py        # SQLite 连接唯一入口
│   ├── database_manager.py # 数据库管理器（表读取 / 缓存）
│   ├── analysis_storage.py # AI 分析报告持久化
│   ├── ai_config.py        # AI 配置管理器（端点 / 模型 / 密钥）
│   └── ...
│
├── ui/                     # 界面层（PySide6）
│   ├── main_window.py      # 主窗口（三大板块切换）
│   ├── components/         # 面板 / 对话框 / 导出
│   │   ├── input_panel.py
│   │   ├── result_panel.py
│   │   ├── meihua_*.py
│   │   ├── liuren_*.py
│   │   └── export_dialog.py
│   └── export/             # PDF / Excel / CSV 导出器
│
├── api/
│   └── agnes_client.py     # 龙虎山大师兄 REST 客户端
│
├── database/
│   ├── schema_sqlite.sql   # SQLite 建库 Schema（权威源）
│   └── base.sql            # MySQL 源 Schema（生成用）
│
├── data/
│   └── fengshui.db         # 运行时 SQLite 库（gitignore）
│
├── tests/
│   └── test_all.py         # 统一测试入口（53 项单测）
│
├── scripts/
│   ├── convert_mysql_to_sqlite.py  # Schema 转换工具
│   ├── purge_ai_secrets.py         # 打包前密钥清理
│   └── verify_build_security.py    # 构建后安全扫描
│
└── docs/                   # 架构 / 路线图 / 方案归档
```

---

## 快速开始

### 环境要求

- Python >= 3.13
- PySide6 >= 6.5
- 依赖见 `requirements.txt`

### 安装与运行

```bash
git clone https://github.com/your-org/KP-AI-FENGSHUI.git
cd KP-AI-FENGSHUI
pip install -r requirements.txt
python main.py
```

### 运行测试

```bash
pytest tests/test_all.py -v
# 53 passed
```

---

## 构建与发布

### 打包为 Windows exe

```bash
# 1. 清理密钥
python scripts/purge_ai_secrets.py

# 2. 打包
python -m PyInstaller build_release.spec

# 3. 安全扫描（必须通过）
python scripts/verify_build_security.py
```

产物位于 `dist/风水排盘专业工具/`。  
默认使用 managed Python 3.13.12，请勿替换为系统 Python。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request。

1. Fork 本仓库
2. 创建特性分支 `git checkout -b feature/amazing-feature`
3. 提交修改 `git commit -m 'Add amazing feature'`
4. 推送到分支 `git push origin feature/amazing-feature`
5. 提交 Pull Request

**代码规范**
- 遵循 PEP 8
- 新增逻辑须补充单测（`tests/test_all.py`）
- 修改 `database/base.sql` 后需重新运行 `scripts/convert_mysql_to_sqlite.py`

---

## 路线图

- [x] v5.0 八字排盘深度分析 + 梅花易数六种起卦 + 大六壬九宗门
- [x] v5.0.1 AI 结构化输出契约 + 六壬独立 prompt 分支
- [ ] v5.1 排盘历史记录管理（分类 / 搜索 / 标签）
- [ ] v5.2 专业细盘 PDF 模板定制（用户可调五行图 / 十神表布局）
- [ ] v5.3 支持 macOS / Linux 平台打包

---

## 免责声明

**本工具仅供传统文化研究与娱乐参考，不构成任何医疗、法律、财务或人生决策依据。**  
命理学尚未被现代科学证实。如使用 AI 解读功能，请确保 API 密钥来源合法并自行承担第三方数据处理风险。

---

## 开源协议

GPL v3 — 2026 KP-AI-FENGSHUI Team