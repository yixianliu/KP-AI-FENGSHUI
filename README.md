# AI风水命理分析系统

基于Python开发的专业命理分析工具，集成八字排盘、五行分析、十神分析、神煞命理、大运流年、AI智能分析及梅花易数等功能，提供完整的命理分析解决方案。

## 功能特性

### 核心功能

- **八字排盘**：支持真太阳时修正、节气精准计算、早晚子时处理，生成完整四柱八字
- **五行分析**：细化藏干能量分值（本气0.6、中气0.3、余气0.1），增加月令扶抑权重和通根强弱判定
- **十神分析**：基于藏干能量的十神权重计算，完善十神力量分析和综合评分
- **命理特征**：神煞（天德、月德、文昌、桃花等）、纳音五行、空亡判定、干支关系
- **大运流年**：大运方向计算、流年运势分析、五行制衡交互分析
- **AI智能分析**：双模型融合校验（传统规则引擎 + AI模型），生成性格、事业、婚姻、健康等多维度分析报告
- **梅花易数**：支持时间起卦、报数起卦等多种方式，提供本卦、互卦、变卦的完整解卦

### 辅助功能

- **术语词典**：完整的命理术语解释和查询
- **图表分析**：可视化展示五行分布、十神权重等数据
- **报告导出**：支持PDF、Excel、CSV多种格式导出
- **历史记录**：自动保存分析报告到数据库，支持查询和追溯

## 技术栈

- **语言**：Python 3.10+
- **GUI框架**：PySide6 6.6+
- **数据库**：MySQL 8.0+（PyMySQL）
- **AI模型**：百度千帆ERNIE / 讯飞星火大模型
- **日历工具**：lunarcalendar（农历转换）
- **真太阳时**：pyephem（天文计算）

## 安装与配置

### 环境要求

- Python 3.10 或更高版本
- MySQL 8.0 或更高版本

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd KP-AI-FENGSHUI
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置数据库**

编辑 `config.ini` 文件，配置数据库连接：

```ini
[database]
host = 127.0.0.1
user = root
password = your_password
database = ai_fengshui
charset = utf8mb4
```

4. **配置AI接口**

编辑 `config.ini` 文件，配置AI模型API：

```ini
[ernie]
api_url = https://qianfan.baidubce.com/v2/chat/completions
api_key = Bearer your_api_key
model = deepseek-v3.1-250821
max_retries = 2
retry_delay = 2
timeout = 60
```

5. **运行程序**

```bash
python main.py
```

## 使用说明

### 八字排盘

1. 选择「八字排盘」功能
2. 输入姓名、性别、出生日期、出生时间、出生地
3. 点击「开始排盘」按钮
4. 系统将自动计算：
   - 八字四柱（年柱、月柱、日柱、时柱）
   - 五行分布和强弱分析
   - 十神数量和权重分析
   - 神煞、纳音、空亡等命理特征
   - 大运走势和流年运势
5. 点击「AI分析」获取智能分析报告

### 梅花易数

1. 选择「梅花易数」功能
2. 输入求测问题和起卦方式
3. 点击「起卦」按钮
4. 系统将生成：
   - 本卦、互卦、变卦
   - 动爻分析
   - 五行生克关系
   - 综合吉凶判断

### 术语词典

1. 选择「术语词典」功能
2. 在搜索框输入命理术语
3. 查看术语解释和详细说明

### 图表分析

1. 完成八字排盘后选择「图表分析」
2. 查看五行分布饼图、十神权重柱状图等可视化数据

## 核心功能演示

### 八字排盘示例

```python
from core.bazi_calculator import BaziCalculator

# 创建计算器实例
calc = BaziCalculator()

# 计算八字（公历2000年1月15日12:30，北京经度116.4）
bazi = calc.calculate(2000, 1, 15, 12, 30, 116.4)

# 获取五行分析
wuxing = calc.get_wuxing(bazi)

# 获取十神分析
shishen = calc.get_shishen(bazi)

# 获取命理特征
mingli = calc.get_mingli(bazi)

# 获取大运（男命）
dayun = calc.get_dayun(bazi, '男', 2000)

# 获取流年
liunian = calc.get_liunian(bazi, 2024, 10)

# AI智能分析
from core.ai_analyzer import AIAnalyzer
analyzer = AIAnalyzer()
result = analyzer.analyze(bazi, wuxing, shishen, mingli)
```

### 梅花易数示例

```python
from core.meihua import MeiHuaCalculator

# 创建计算器实例
meihua = MeiHuaCalculator()

# 时间起卦
hexagram = meihua.time_divination(2024, 6, 23, 10, question='事业发展')

# 解析卦象
from core.hexagram_analyzer import HexagramAnalyzer
analyzer = HexagramAnalyzer()
analysis = analyzer.analyze(hexagram)
```

## API接口文档

### 八字分析API

#### 计算八字

```python
def calculate(year, month, day, hour, minute=0, longitude=120.0, is_lunar=False)
```

**参数**:
- `year`: 公历年
- `month`: 公历月
- `day`: 公历日
- `hour`: 小时
- `minute`: 分钟（用于真太阳时精确计算）
- `longitude`: 经度（用于真太阳时修正）
- `is_lunar`: 是否为农历

**返回**: 包含年柱、月柱、日柱、时柱、日主等信息的字典

#### 五行分析

```python
def get_wuxing(bazi)
```

**返回**: 包含五行分值、占比、强度、通根情况等信息的字典

#### 十神分析

```python
def get_shishen(bazi)
```

**返回**: 包含十神数量、权重、综合分析等信息的字典

#### 命理分析

```python
def get_mingli(bazhi)
```

**返回**: 包含神煞、纳音、空亡、格局等信息的字典

#### 大运计算

```python
def get_dayun(bazhi, gender, birth_year)
```

**参数**:
- `bazhi`: 八字字典
- `gender`: 性别（'男'或'女'）
- `birth_year`: 出生年份

**返回**: 包含大运方向、起运年龄、各步大运等信息的字典

### AI分析API

#### 智能分析

```python
def analyze(bazhi, wuxing_result, shishen_result, mingli_result=None)
```

**返回**: 包含性格、事业、婚姻、健康、建议、格局分析、五行平衡、十神分析等字段的字典

## 项目结构

```
KP-AI-FENGSHUI/
├── core/                    # 核心命理计算模块
│   ├── baazi.py             # 八字排盘核心算法
│   ├── bazi_calculator.py   # 八字计算器统一入口
│   ├── wuxing.py            # 五行分析器
│   ├── shishen.py           # 十神分析器
│   ├── mingli.py            # 命理特征分析（神煞、纳音、空亡）
│   ├── yunshi.py            # 大运流年计算
│   ├── ai_analyzer.py       # AI智能分析器
│   ├── data_integration.py  # 数据整合模块
│   ├── analysis_storage.py  # 分析报告存储
│   ├── analysis_pipeline.py # 数据分析主流程
│   ├── knowledge_base.py    # 命理知识库
│   ├── meihua.py            # 梅花易数计算器
│   ├── hexagram_analyzer.py # 卦象分析器
│   ├── hexagram_data.py     # 卦象数据
│   ├── solar_time.py        # 真太阳时计算
│   ├── lunar_converter.py   # 农历转换器
│   ├── calendar_utils.py    # 日历工具函数
│   ├── location_db.py       # 城市数据库
│   ├── data_validator.py    # 数据验证器
│   ├── chart_generator.py   # 图表生成器
│   ├── term_explainer.py    # 术语解释器
│   ├── geju_analyzer.py     # 格局分析器
│   ├── backtest.py          # 回测模块
│   ├── database_manager.py  # 数据库管理器
│   ├── local_database.py    # 本地数据库
│   ├── errors.py            # 异常定义
│   ├── utils.py             # 工具函数
│   └── __init__.py          # 模块导出
├── ui/                      # PySide6 GUI界面
│   ├── main_window.py       # 主窗口
│   ├── styles.py            # 样式定义
│   ├── components/          # UI组件
│   │   ├── input_panel.py          # 八字输入面板
│   │   ├── result_panel.py         # 分析结果面板
│   │   ├── meihua_input.py         # 梅花易数输入
│   │   ├── meihua_result_panel.py  # 梅花易数结果
│   │   ├── term_dictionary_panel.py # 术语词典
│   │   ├── chart_widget.py         # 图表组件
│   │   ├── ai_analysis_worker.py   # AI分析工作线程
│   │   ├── login_dialog.py         # 登录对话框
│   │   ├── home_page.py            # 首页
│   │   └── export_dialog.py        # 导出对话框
│   └── export/              # 导出模块
│       ├── base_exporter.py    # 导出基类
│       ├── pdf_exporter.py     # PDF导出
│       ├── excel_exporter.py   # Excel导出
│       └── csv_exporter.py     # CSV导出
├── api/                     # AI接口客户端
│   ├── ernie_client.py       # ERNIE客户端
│   └── ai_ERNIE_X1_Turbo.py  # ERNIE X1 Turbo客户端
├── utils/                   # 工具函数
│   ├── calendar.py           # 日历工具
│   └── solar_time.py         # 真太阳时计算
├── tests/                   # 测试文件
│   └── test_all.py           # 综合测试
├── main.py                  # 程序入口
├── requirements.txt         # 依赖列表
├── config.ini               # 配置文件
└── README.md                # 项目文档
```

## 核心算法说明

### 八字排盘算法

1. **年柱**：按立春分界，使用干支纪年法计算
2. **月柱**：按节气划分月建，根据年干确定月干（五虎遁）
3. **日柱**：基于公历日期计算，使用甲子循环
4. **时柱**：基于真太阳时，根据日干确定时干（五鼠遁），支持早晚子时处理

### 五行分析算法

1. **天干五行**：直接映射（甲木、乙木、丙火等）
2. **地支五行**：直接映射（子水、丑土、寅木等）
3. **藏干能量**：本气0.6、中气0.3、余气0.1
4. **月令权重**：根据月令调整各五行能量（当令者强，失令者弱）
5. **通根判定**：判断日主在地支是否有根气

### 十神分析算法

1. **十神类型**：生我（印星）、我生（食伤）、克我（官杀）、我克（财星）、同我（比劫）
2. **正偏区分**：根据阴阳属性区分正印/偏印、食神/伤官等
3. **权重计算**：基于天干+藏干的综合能量计算各十神权重

### AI分析算法

1. **数据整合**：收集原始数据、中间处理结果、历史记录、知识库上下文
2. **提示词构建**：构建包含完整命理特征的结构化提示词
3. **双模型融合**：传统规则引擎作为基准约束AI输出
4. **动态权重**：根据全局五行制衡关系自动调整各十神影响权重

## 开发与贡献

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解
- 添加详细中文注释
- 保持代码模块化

### 测试

运行测试文件：

```bash
python -m pytest tests/test_all.py -v
```

### 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License

## 免责声明

本程序仅为传统民俗文化参考工具，测算结果不具备绝对定论，仅供娱乐参考。命理分析属于传统文化范畴，不应作为人生决策的唯一依据。

---

**版本**: v4.0  
**最后更新**: 2026年6月  
**作者**: KP-AI-FENGSHUI开发团队