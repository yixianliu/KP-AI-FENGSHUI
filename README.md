# KP-AI-FENGSHUI — AI 风水命理分析系统

> 中国传统命理学 x 现代 AI 大模型 · 桌面端专业命理分析工具

基于 Python + PySide6 开发的桌面端风水命理分析软件，将八字排盘、梅花易数等传统命理学与现代 AI 大模型（Agnes AI / agnes-2.5-flash）深度结合，提供从命理计算、数据分析到 AI 智能解读的一站式解决方案。

---

## 功能特性

### 核心功能

- **八字排盘**：支持真太阳时修正（均时差+经度修正）、节气精准计算、早晚子时处理，生成完整四柱八字
- **五行分析**：细化藏干能量分值（本气0.6、中气0.3、余气0.1），月令扶抑权重，通根强弱判定
- **十神分析**：基于藏干能量的十神权重计算，正偏印/食伤/财星/官杀/比劫全维度分析
- **命理特征**：神煞（天德、月德、文昌、桃花等）、纳音五行、空亡判定、干支冲合害刑
- **大运流年**：大运方向计算、起运年龄推算、流年运势分析、小运及五行制衡交互
- **格局分析**：正格/变格自动判定，格局层次评估
- **AI 智能解读**：传统规则引擎与 AI 大模型融合，生成性格、事业、婚姻、健康、财富等多维度报告
- **梅花易数**：支持时间起卦、报数起卦、方位起卦、文字起卦，本卦/互卦/变卦/错卦/综卦完整解卦

### 辅助功能

- **报告导出**：支持 PDF、Excel、CSV 多格式分析报告导出
- **历史记录**：自动保存排盘记录和 AI 分析到本地 SQLite 数据库，支持查询追溯
- **知识库注入**：AI 分析前自动注入命理知识库上下文，增强专业性
- **异步非阻塞**：基于 QThread 的异步 AI 分析，UI 永不卡顿

---

## 系统架构

```
+------------------------------------------------------------------+
|                     UI 表现层 (PySide6)                           |
|  MainWindow -> Tab: 八字排盘 / 梅花易数 / 历史记录 /              |
|              AI 分析结果                                           |
+----------------------------------------+-------------------------+
                                         | 用户交互 & 信号槽机制
+----------------------------------------v-------------------------+
|                 业务逻辑层 (core/)                                |
|  +-------------+  +--------------+  +---------------------------+ |
|  | 八字排盘引擎  |  | 五行/十神分析 |  |  大运流年计算             | |
|  | BaZiCalc   |  | WuXing/ShiShen|  |  YunShiCalc             | |
|  +-------------+  +--------------+  +---------------------------+ |
|  +-------------+  +--------------+  +---------------------------+ |
|  | 命理特征分析  |  |  梅花易数引擎 |  |  AI 分析管线              | |
|  | MingLi     |  |  MeiHua      |  |  Pipeline (分析管线)    | |
|  +-------------+  +--------------+  +---------------------------+ |
+----------------------------------------+-------------------------+
                                         | 数据请求 & 分析结果
+----------------------------------------v-------------------------+
|                  基础设施层                                         |
|  SQLite (本地数据库)  .  Agnes AI API                            |
+------------------------------------------------------------------+
```

### 八字分析工作流

```
用户输入（姓名/性别/生日/时辰/城市）
        |
        v
  1. 数据验证 (data_validator)
        |
        v
  2. 八字排盘 (baazi + bazi_calculator)
      公历->农历 -> 节气判定 -> 四柱推算 -> 真太阳时修正
        |
        v
  3. 并行特征提取
      +----------+----------+----------+----------+
      | 五行分析  | 十神分析  | 命理特征  | 大运流年  |
      | wuxing   | shishen   | mingli   | yunshi   |
      +----------+----------+----------+----------+
        |
        v
  4. 数据整合 (data_integration)
      数据清洗 -> 格式统一 -> 知识库注入 -> 构建 500+ 行结构化 Prompt
        |
        v
  5. AI 异步分析 (analysis_pipeline + agnes_client)
      QThread 后台执行 -> 调用 Agnes AI API -> 结果存入本地 SQLite
        |
        v
  6. 前端轮询 & 展示 (ResultPanel)
      状态回调驱动 -> 渐进式渲染 AI 报告
```

---

## 技术栈

| 类别 | 技术 | 版本要求 |
|------|------|---------|
| 编程语言 | Python | 3.10+ |
| GUI 框架 | PySide6 (Qt for Python) | 6.6+ |
| 数据库 | SQLite（本地） | 内置 |
| AI 模型 | Agnes AI | agnes-2.5-flash |
| 农历转换 | lunarcalendar | 0.0.9 |

---

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
venv/Scripts/activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

> 注意：项目还使用了 `requests`、`urllib3` 等库，请确保已安装。

### 2. 数据库配置

本工具使用本地 **SQLite** 数据库，无需安装 MySQL，也无需配置连接串。

- 打包运行：首次启动自动从内置种子库 `data/fengshui.db` 初始化；
- 源码运行：数据库文件自动创建于用户目录
  `C:\Users\<你>\.kp-fengshui\data\fengshui.db`。

### 3. 配置 AI 接口（龙虎山大师兄）

本工具已内置**唯一的** AI 后端：**龙虎山大师兄（Agnes AI，`agnes-2.5-flash`）**，
端点固定为 `https://api.agnes-ai.cn/v1/chat/completions`，无需也不支持切换其他模型。

首次使用请在软件内配置密钥：

1. 打开「设置 → 龙虎山大师兄配置」；
2. 在 **API 密钥** 输入框中粘贴你的密钥（可点右侧「显示 / 隐藏」图标）；
3. 点击「测试连接」验证密钥有效性，再点「保存并应用」。

配置仅保存在本机 `ai_config.json`（设备指纹混淆存储），不会写入任何源码或分发文件。

### 4. 运行程序

```bash
python main.py
```

---

## 项目结构

```
KP-AI-FENGSHUI/
├── main.py                          # 程序入口
├── requirements.txt                 # Python 依赖清单
├── README.md                        # 项目文档（本文件）
│
├── core/                            # 核心业务逻辑层
│   ├── baazi.py                     # 八字排盘核心算法
│   ├── bazi_calculator.py           # 八字计算器统一入口（门面）
│   ├── wuxing.py                    # 五行分析器（藏干加权+月令扶抑）
│   ├── shishen.py                   # 十神分析器（正偏/阴阳权重）
│   ├── mingli.py                    # 命理特征分析（神煞/纳音/空亡/冲合）
│   ├── yunshi.py                    # 大运流年计算（顺逆/起运/小运）
│   ├── geju_analyzer.py             # 格局分析器（正格/变格判定）
│   ├── meihua.py                    # 梅花易数起卦（时间/数字/方位/文字）
│   ├── hexagram_data.py             # 六十四卦静态数据
│   ├── hexagram_analyzer.py         # 卦象分析器（体用/五行生克）
│   ├── analysis_pipeline.py         # AI 分析主流程编排
│   ├── data_integration.py          # 数据整合 & Prompt 构建
│   ├── analysis_storage.py          # 分析报告持久化（SQLite）
│   ├── knowledge_base.py            # 命理知识库上下文注入
│   ├── solar_time.py                # 真太阳时计算（均时差+经度修正）
│   ├── calendar_utils.py            # 日历工具（节气/均时差计算）
│   ├── lunar_converter.py           # 农历/公历转换
│   ├── data_validator.py            # 数据验证器
│   ├── database_manager.py          # SQLite 访问层（单例）
│   ├── location_db.py               # 城市经纬度数据库
│   ├── errors.py                    # 异常定义与错误码
│   └── __init__.py                  # 模块统一导出
│
├── ui/                              # PySide6 GUI 界面
│   ├── main_window.py               # 主窗口（SplitPane + Tab 导航）
│   ├── styles.py                    # 国风设计系统（配色/字体/间距）
│   ├── components/                  # UI 组件模块
│   │   ├── input_panel.py           # 八字输入面板（公历/农历/城市选择）
│   │   ├── result_panel.py          # 分析结果面板（四柱/五行/十神/AI报告）
│   │   ├── meihua_input.py          # 梅花易数输入面板
│   │   ├── meihua_result_panel.py   # 梅花易数结果面板
│   │   ├── ai_analysis_worker.py    # AI 分析工作线程（QThread）
│   │   ├── settings_dialog.py       # 龙虎山大师兄配置（极简 AI 密钥设置）
│   │   └── export_dialog.py         # 导出格式选择对话框
│   └── export/                      # 导出模块
│       ├── base_exporter.py         # 导出基类
│       ├── pdf_exporter.py          # PDF 导出
│       ├── excel_exporter.py        # Excel 导出
│       └── csv_exporter.py          # CSV 导出
│
├── api/                             # AI 接口层
│   └── agnes_client.py              # Agnes AI API 客户端（OpenAI 兼容）
│
├── database/                        # 数据库 Schema
│   └── base.sql                     # 完整数据库建表脚本（SQLite，37 张表）
│
└── tests/                           # 测试
    └── test_all.py                  # 综合测试
```

---

## 数据库设计

数据库名：`ai_fengshui`，包含 **30+ 张表**，分为以下几大类：

### 业务数据表

| 表名 | 说明 |
|------|------|
| `users` | 用户账号信息 |
| `pan_records` | 排盘历史记录 |
| `analysis_reports` | AI 分析报告（JSON 存储完整分析数据） |
| `analysis_logs` | 分析日志 |

### 命理知识库表（部分）

| 表名 | 数据内容 |
|------|---------|
| `tian_gan` | 十天干（五行/阴阳/方位/数理/运势） |
| `di_zhi` | 十二地支（五行/藏干/时辰/生肖/方位） |
| `di_zhi_he` / `di_zhi_chong` / `di_zhi_xing` | 地支合/冲/刑关系 |
| `di_zhi_hidden_gan` | 地支藏干明细 |
| `sixty_jiazi` | 六十甲子干支组合 |
| `nayin_wuxing` | 纳音五行 |
| `shensha_terms` | 神煞术语（天德/月德/文昌/桃花等） |
| `jie_qi` | 二十四节气时间表 |
| `wuxing_relations` | 五行生克关系 |
| `hexagram_64` | 六十四卦完整数据 |
| `city_coords` | 中国城市经纬度 |
| ... | 更多表见 `database/base.sql` |

---

## 核心算法说明

### 八字排盘

| 柱 | 算法 | 备注 |
|----|------|------|
| **年柱** | `(year - 4) % 60` 映射干支序 | 按立春分界 |
| **月柱** | 二十四节气划分月建 + 五虎遁推月干 | 非简单月份映射 |
| **日柱** | 公历日期 -> 甲子循环序 | 儒略日计算 |
| **时柱** | 真太阳时修正 + 五鼠遁推时干 | 支持早晚子时 |

### 真太阳时

采用 **均时差 + 经度修正** 的双重算法，而非简单的 15°/时辰近似。

### 五行能量评分

```
天干能量 = 天干五行固定分值
地支藏干能量 = 求和(藏干权重 * 对应五行分值)
  - 本气: 权重 0.6
  - 中气: 权重 0.3
  - 余气: 权重 0.1

月令修正系数:
  - 当令五行: x1.5
  - 生月令五行: x1.2
  - 克月令五行: x0.8
```

### AI 智能分析

1. **数据整合**：`DataIntegrator` 将 20+ 字段的不同数据类型统一清洗
2. **知识库注入**：从本地知识库预加载五行特性、十神含义等上下文
3. **Prompt 构建**：生成 500+ 行结构化自然语言 Prompt
4. **异步执行**：`QThread` 后台调用 Agnes AI API，不阻塞 UI
5. **状态回调**：pending -> analyzing -> completed，前端实时获取结果
6. **持久化存储**：完整分析报告以 JSON 格式存入本地 SQLite

---

## API 参考

### 八字计算

```python
from core.bazi_calculator import BaziCalculator

calc = BaziCalculator()

# 计算八字（支持公历/农历，自动真太阳时修正）
bazi = calc.calculate(year, month, day, hour, minute, longitude, is_lunar=False)

# 五行分析
wuxing = calc.get_wuxing(bazi)

# 十神分析
shishen = calc.get_shishen(bazi)

# 命理特征（神煞/纳音/空亡/格局）
mingli = calc.get_mingli(bazi)

# 大运（需指定性别以判断顺逆）
dayun = calc.get_dayun(bazi, gender='男', birth_year=2000)

# 流年
liunian = calc.get_liunian(bazi, year=2024, count=10)
```

### 梅花易数

```python
from core.meihua import MeiHuaCalculator

meihua = MeiHuaCalculator()

# 时间起卦
hexagram = meihua.time_divination(2024, 6, 23, 10, question='事业发展')

# 数字起卦
hexagram = meihua.number_divination(8, 6, question='财运')
```

### AI 分析管线

```python
from core.analysis_pipeline import AnalysisPipeline

pipeline = AnalysisPipeline()
result = pipeline.run_bazi_analysis(
    name='张三',
    gender='男',
    birth_date='2000-01-15',
    birth_time='12:30',
    city='北京',
    report_type='bazi'
)
```

---

## 测试

```bash
# 运行全部测试（unittest）
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 配置

本工具**无需任何配置文件**。数据库使用本地 SQLite（自动初始化），AI 后端为内置固定的
龙虎山大师兄（Agnes AI），仅需在软件内「设置 → 龙虎山大师兄配置」中填写 API 密钥即可。

- AI 密钥：保存在本机 `ai_config.json`（设备指纹混淆存储），不落盘明文、不写源码、不分发；
- 数据库：自动创建于用户目录 `C:\Users\<你>\.kp-fengshui\data\fengshui.db`。

> **安全提示**：API 密钥由你自己持有，请妥善保管，不要提交到版本控制系统或分享给他人。

---

## 开发与贡献

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解（Type Hints）
- 添加详细中文注释和模块文档字符串
- 保持代码模块化，职责单一

### 添加新功能

1. 核心算法在 `core/` 目录下实现
2. UI 组件在 `ui/components/` 目录下实现
3. 知识库数据通过 `database/base.sql` 维护
4. AI 配置通过「设置 → 龙虎山大师兄配置」GUI 管理，密钥落盘于本机 `ai_config.json`

---

## 许可证

MIT License

---

## 免责声明

本程序仅为传统民俗文化参考工具，测算结果不具备绝对定论，仅供娱乐参考。命理分析属于传统文化范畴，不应作为人生决策的唯一依据。

---

**版本**: v5.0
**最后更新**: 2026年6月29日
**语言**: Python 3.10+
**框架**: PySide6 (Qt 6)
**数据库**: SQLite（本地，内置）
