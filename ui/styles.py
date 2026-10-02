"""
风水排盘专业工具 - 新中式玄中易设计系统 v6.0
主色调：深靛蓝 #1a1a2e / 古金 #c9a227 / 朱红 #8b0000
深底色配金色/朱红点缀 · 水墨纹理背景 · 宋体/楷体标题 · 微软雅黑正文
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - 仅供字符串注解解析，运行期不求值
    from PySide6.QtWidgets import QGraphicsDropShadowEffect


class Colors:
    """全局色彩体系（新中式玄中易深色体系）

    v6.1 设计令牌收敛：
    - 引入语义化权威命名（BRAND / ACCENT / SEMANTIC_*），作为新代码的首选引用源。
    - 旧有命名（QINGHUA / LIUJIN / ZHUSHA / SUCCESS / WARNING / DANGER / INFO / YU / SHANHU 等）
      全部降级为「兼容别名」，值保持不变，保证既有引用零破坏，后续逐步迁移下线。
    使用规则（详见 docs/design-tokens.md）：
    - BRAND  用于「导航 + 强调 + 图表主色」，禁止用作按钮背景。
    - ACCENT 仅用于「主操作按钮」，一个页面最多 2 个。
    - SEMANTIC_* 只用于「状态提示」，禁止装饰性使用。
    - 五行领域色（WOOD/FIRE/EARTH/METAL/WATER）仅出现在八字/玄空领域区域。
    """

    # ========== 主色调（项目规范） ==========
    INK = '#1a1a2e'          # 深靛蓝（主色）
    GOLD = '#c9a227'         # 古金（强调/高亮）
    ZHONGYI = '#8b0000'      # 朱红（主操作/点缀）

    # ========== 语义化权威命名（v6.1 单一真相源，新代码首选） ==========
    # 品牌金：导航 / 选中 / 强调 / 图表主色
    BRAND = GOLD                     # #c9a227
    BRAND_LIGHT = '#e8d08a'
    BRAND_DARK = '#8f751c'
    BRAND_GLOW = 'rgba(201, 162, 39, 0.22)'
    # 主操作朱红：主按钮 / 主操作 / 警报
    ACCENT = ZHONGYI                 # #8b0000
    ACCENT_LIGHT = '#C97A6A'
    ACCENT_DARK = '#5E0000'
    ACCENT_GLOW = 'rgba(139, 0, 0, 0.25)'
    # 语义色（状态提示专用）
    SEMANTIC_SUCCESS = '#5DAF74'     # 成功 / 吉
    SEMANTIC_WARNING = '#D8A94E'     # 警告 / 需留意
    SEMANTIC_DANGER = '#C45545'      # 危险 / 凶
    DANGER_DARK = '#A03E32'          # 危险按钮专用深底（M7：浅字对比度 5.76:1）
    SEMANTIC_INFO = '#7FB3C8'        # 信息 / 中性

    # ========== 底色系 - 深靛蓝水墨 ==========
    BG = '#1a1a2e'
    BG_DARK = '#12121f'
    CARD = '#21213a'
    HOVER = '#262640'
    CARD_HOVER = '#28284a'
    CARD_SELECTED = '#2c2c4e'

    # ========== 三色点缀 - 国风主题（保留，已等价于语义色） ==========
    # 朱红（主操作）= ACCENT
    ZHUSHA = ACCENT
    ZHUSHA_LIGHT = ACCENT_LIGHT
    ZHUSHA_DARK = ACCENT_DARK
    ZHUSHA_GLOW = ACCENT_GLOW

    # 古金（导航/选中）= BRAND
    QINGHUA = BRAND
    QINGHUA_LIGHT = BRAND_LIGHT
    QINGHUA_DARK = BRAND_DARK
    QINGHUA_GLOW = BRAND_GLOW

    # 古金（高亮/强调）= BRAND（与 QINGHUA 同值，收敛别名）
    LIUJIN = BRAND
    LIUJIN_LIGHT = BRAND_LIGHT
    LIUJIN_DARK = BRAND_DARK
    LIUJIN_GLOW = BRAND_GLOW

    # ========== 文字色彩（深底配浅色字） ==========
    TEXT = '#F5F1E8'
    TEXT2 = '#D8D3C8'
    TEXT3 = '#9C97A8'
    TEXT4 = '#918C9E'       # 四级灰阶（M7：提亮至 WCAG AA ≥4.5:1；原 #6B6678 仅 2.83:1）
    TEXT_INV = '#12121f'
    # 纯白：仅用于彩色标签底上的文字（如大六壬五行 chip），勿作正文用
    WHITE = '#FFFFFF'

    # ========== 边框与分割 ==========
    BORDER = '#33335A'
    BORDER2 = '#45456E'
    DIVIDER = '#2E2E4C'
    DIVIDER_LIGHT = '#262640'

    # ========== 状态色彩（深色底优化对比度） ==========
    SUCCESS = SEMANTIC_SUCCESS
    SUCCESS_LIGHT = '#2A4A38'
    WARNING = SEMANTIC_WARNING
    WARNING_LIGHT = '#4A3E20'
    DANGER = SEMANTIC_DANGER
    DANGER_LIGHT = '#4A2626'
    INFO = SEMANTIC_INFO
    INFO_LIGHT = '#1E3A4A'

    # ========== 渐变（深色水墨） ==========
    GRADIENT_WARM = '#1a1a2e'
    GRADIENT_COOL = '#141428'
    GRADIENT_NAV_START = '#1a1a2e'
    GRADIENT_NAV_END = '#12121f'

    # ========== 水墨纹理（低透明度，深底微纹理） ==========
    WATERMARK = 'rgba(201, 162, 39, 0.03)'

    # ========== 五行色彩（深色底提亮以保可读性） ==========
    WOOD = '#7CB48E'
    WOOD_LIGHT = '#A8D8B8'
    WOOD_DARK = '#4A8A5E'
    FIRE = '#E88870'
    FIRE_LIGHT = '#F0B8A0'
    FIRE_DARK = '#C45545'
    EARTH = '#C0A878'
    EARTH_LIGHT = '#D8C8A0'
    EARTH_DARK = '#8B7355'
    METAL = '#B8B0A0'
    METAL_LIGHT = '#D8D0C0'
    METAL_DARK = '#8A8278'
    WATER = '#8AC8E8'
    WATER_LIGHT = '#B0D8F0'
    WATER_DARK = '#5B8FA8'

    # ========== 新中式扩展色彩（视觉层次补充） ==========
    # 宣纸色（浅色区域 / 选中态背景）
    XUANZHI = '#F5F0E6'
    XUANZHI_LIGHT = '#FAF7F0'
    XUANZHI_DARK = '#E8E0CC'

    # 墨色（次级边框 / 次要文字）
    MO = '#2C2C3A'
    MO_LIGHT = '#3A3A50'
    MO_DARK = '#1E1E2E'

    # ========== 领域专用色（面板局部，不与品牌色冲突）==========
    # 深靛蓝凶星色：玄空飞星「凶」的盘面着色，深底可读的蓝灰。
    # 区别于 BRAND/INK（品牌靛蓝）与 SEMANTIC_INFO（浅蓝灰）。
    INDIGO_DEEP = '#4A5A8A'
    # 九宫飞星盘画布底：比 BG 更深一档，突出盘面与卡片的层次。
    CANVAS_DARK = '#0F0F1A'

    # ========== 卡纸高亮渐变（关键柱/标题专用，暖宣纸色）==========
    # 三面板复用同一渐变（result_panel 日柱 / meihua / liuren 高亮块），
    # 原为三处独立硬编码，易漂移——统一归此。渐变方向 stop0→stop1：
    HIGHLIGHT_WARM_STRONG = '#FFFBF0'   # 渐变起点（更亮）
    HIGHLIGHT_WARM = '#FFF5E0'          # 渐变终点（略暗）
    HIGHLIGHT_WARM_SOFT = '#FFF9E8'     # 折叠卡标题渐变中段

    # ========== 浅色国风主题（导出对话框专用，语义化令牌）==========
    # 设计意图：模拟纸质报告，与主界面深色主题形成「编辑态 / 成品态」对比。
    # 这是**有意设计**（勿改为深色主题）；改视觉请改令牌值，
    # 业务文件不得写裸色值（原 export_dialog 有 45 处硬编码色值，
    # Colors/Fonts 令牌 0 引用，属设计孤岛——已归位到此）。
    # 宣纸系
    PAPER = '#FFF8E7'             # 宣纸底
    PAPER_LIGHT = '#FFF3D6'       # 卡片浅底
    PAPER_HOVER = '#FBF3DD'       # 悬停宣纸
    PAPER_BORDER = '#E5D9B8'      # 宣纸分隔线
    PAPER_ACTIVE = '#F3E9CF'      # 按压 / 激活底
    # 墨褐系（浅色主题的主色，区别于深色主题的深靛蓝 INK）
    INK_PAPER = '#5D4037'         # 墨褐主色
    INK_PAPER_HOVER = '#6B4423'   # 悬停墨褐
    INK_PAPER_BORDER = '#4A3428'  # 按压态边
    INK_PAPER_DARK = '#3D2A20'    # 渐变终止
    INK_PAPER_DARKEST = '#2D1F18' # 最深墨褐
    # 宣纸上的金（区别于深色主题的 GOLD #c9a227）
    GOLD_PAPER = '#D4AF37'        # 边框 / 进度条
    GOLD_PAPER_DARK = '#B08D3C'   # 暗金，次级强调
    # 宣纸底文字
    TEXT_PAPER = '#333333'        # 正文
    TEXT_PAPER_DIM = '#8A8278'    # 次要说明

    # ========== PDF 导出专用调色板（打印介质） ==========
    # 服务对象是导出成品（PDF / 打印），与上面的 PAPER_* 同为纸质系但用途
    # 不同：那边是导出对话框界面，这边是最终报告排版。
    # 色值比屏幕版更「实」（偏暗/偏饱和）以保证打印对比度：
    #   PDF_LIUJIN #B88A30 vs 屏幕 GOLD #c9a227；PDF_TEXT #333333 vs TEXT #F5F1E8。
    # 注意命名冲突：PDF_QINGHUA 是真正的青（#4A7A90），而 Colors.QINGHUA
    # 已收敛为古金别名（= BRAND），二者语义不同，故 PDF_ 前缀独立命名。
    # 8 个中 3 个与既有令牌同值（ZHUSHA/WHITE/TEXT_PAPER），5 个为打印专用。
    PDF_ZHUSHA = '#C45545'        # 朱砂，标题强调（= FIRE_DARK / SEMANTIC_DANGER）
    PDF_QINGHUA = '#4A7A90'       # 青华，次级强调（比屏幕版更沉稳）
    PDF_LIUJIN = '#B88A30'        # 流金，装饰线与分隔（比 GOLD 更暗）
    PDF_BG = '#F7F4EE'            # 页面底色（近 XUANZHI，更暖）
    PDF_CARD = '#FFFFFF'          # 卡片 / 表格底（= WHITE）
    PDF_TEXT = '#333333'          # 正文墨色（= TEXT_PAPER）
    PDF_LINE = '#D9CDB8'          # 表格线 / 分隔线
    PDF_MUTED = '#8A7F6B'         # 次要文字（比 TEXT_PAPER_DIM 略偏红褐）

    # 玉色（吉星 / 正面信息，与 SUCCESS/SEMANTIC_SUCCESS 同义统一命名）
    YU = SEMANTIC_SUCCESS
    YU_LIGHT = SUCCESS_LIGHT

    # 珊瑚色（警示 / 特殊标记，与 WARNING/SEMANTIC_WARNING 同义统一命名）
    SHANHU = SEMANTIC_WARNING
    SHANHU_LIGHT = WARNING_LIGHT

    # 靛青（辅助强调色，替代部分 QINGHUA 使用场景）= INFO/SEMANTIC_INFO
    DIANQING = SEMANTIC_INFO
    DIANQING_LIGHT = INFO_LIGHT

    # 水墨纹理透明度（用于背景装饰）
    INK_WASH_LOW = 'rgba(201, 162, 39, 0.04)'
    INK_WASH_MID = 'rgba(201, 162, 39, 0.08)'

    # ========== 旧版兼容别名 ==========
    BACKGROUND = BG
    PRIMARY = QINGHUA
    PRIMARY_LIGHT = QINGHUA_LIGHT
    PRIMARY_DARK = QINGHUA_DARK
    ACCENT = ZHUSHA
    ACCENT_LIGHT = ZHUSHA_LIGHT
    ACCENT_DARK = ZHUSHA_DARK
    HIGHLIGHT = LIUJIN
    HIGHLIGHT_LIGHT = LIUJIN_LIGHT
    HIGHLIGHT_DARK = LIUJIN_DARK
    HIGHLIGHT_GLOW = LIUJIN_GLOW
    TEXT_PRIMARY = TEXT
    TEXT_SECONDARY = TEXT2
    TEXT_TERTIARY = TEXT3
    TEXT_INVERSE = TEXT_INV
    # 副标题/辅助说明文字色（加载面板副标题等场景使用）
    TEXT_SUB = TEXT2
    BORDER_LIGHT = DIVIDER
    HOVER_BG = HOVER
    INPUT_BG = CARD
    PARCHMENT = BG
    PARCHMENT_LIGHT = BG
    PARCHMENT_DARK = '#12121f'
    BRONZE = '#8A7A5A'
    BRONZE_LIGHT = '#B0A070'
    BRONZE_DARK = '#5A5A40'


class Shadows:
    """统一阴影体系（QGraphicsDropShadowEffect 参数，供卡片/导航复用）

    每项 spec 字段：
      - hex:    阴影主色（不带 alpha 的十六进制，如 '#000000' / '#C9A227'）
      - alpha:  不透明度 0~1（QColor 第 4 通道按 0~255 整数换算）
      - offset: (x, y) 偏移像素
      - radius: 模糊半径（blurRadius）
    """

    # 卡片基础阴影
    CARD = {'hex': '#000000', 'alpha': 0.35, 'offset': (0, 4), 'radius': 12}
    # 卡片悬浮阴影（金色发光）
    CARD_HOVER = {'hex': '#C9A227', 'alpha': 0.25, 'offset': (0, 6), 'radius': 16}
    # 概率统计行阴影（prob-row，比卡片更「轻」；alpha 用 18/255、32/255 保留
    # 原实现精确的 0~255 通道值，令牌化后视觉零变化）
    ROW = {'hex': '#000000', 'alpha': 18 / 255, 'offset': (0, 2), 'radius': 10}
    ROW_HOVER = {'hex': '#000000', 'alpha': 32 / 255, 'offset': (0, 4), 'radius': 18}
    # 导航栏阴影
    NAVBAR = {'hex': '#000000', 'alpha': 0.5, 'offset': (0, 2), 'radius': 4}


def apply_shadow(spec: dict, eff: 'QGraphicsDropShadowEffect') -> None:
    """把 Shadows 参数表写进**已存在**的 effect 实例（幂等，供 hover 切换用）。

    为什么单独提供：`setGraphicsEffect(new)` 会让 Qt 删除旧 effect（Qt 接管所有权），
    拿「两个 effect 实例来回换装」做 hover 切换必然踩悬空指针。改为只换参数——
    setColor / setOffset / setBlurRadius 都会触发 QGraphicsEffect::changed() 重绘，
    效果等价且不产生新对象。

    Args:
        spec: Shadows 中任一 dict（CARD / CARD_HOVER / ROW / ROW_HOVER / NAVBAR）。
        eff:  已经装在 widget 上的 effect 实例。
    """
    if eff is None:
        return
    try:
        from PySide6.QtGui import QColor
        # QColor 无法解析 CSS rgba(...) 字符串，必须用 hex + 独立 alpha
        color = QColor(spec['hex'])
        color.setAlphaF(float(spec.get('alpha', 0.5)))
        eff.setColor(color)
        eff.setOffset(*spec['offset'])
        eff.setBlurRadius(spec['radius'])
    except RuntimeError:
        # effect 已被 Qt 删除（控件销毁或所有权变更），静默忽略避免崩溃
        pass


def make_shadow(spec: dict) -> 'QGraphicsDropShadowEffect':
    """按 Shadows 参数表生成 QGraphicsDropShadowEffect 实例。

    Args:
        spec: Shadows 中任一 dict。

    Returns:
        配置好的 QGraphicsDropShadowEffect。
    """
    from PySide6.QtWidgets import QGraphicsDropShadowEffect
    eff = QGraphicsDropShadowEffect()
    apply_shadow(spec, eff)
    return eff


class Fonts:
    """字体体系（规范：标题宋体/楷体，正文微软雅黑）

    v6.1 Font Scale 强化：
    - 引入 7 级 Font Scale（FS_HERO ~ FS_MICRO）作为新代码首选字号源。
    - 旧 SZ_* 别名保留，值不变。
    - 引入数字字重 W_REGULAR / W_MEDIUM / W_SEMIBOLD / W_BOLD，
      旧 W_LIGHT / W_NORMAL / W_MEDIUM / W_BOLD 保留为别名。
    """

    # 标题字体（宋体/楷体，新中式玄中易规范）
    TITLE = '"KaiTi", "SimSun", "STKaiti", "Noto Serif CJK SC", "Source Han Serif SC", serif'
    # 正文字体（微软雅黑，新中式玄中易规范）
    BODY = '"Microsoft YaHei", "微软雅黑", "PingFang SC", "Noto Sans CJK SC", sans-serif'
    # 等宽字体（数据/数值）
    MONO = '"Cascadia Code", "Consolas", "SF Mono", Monaco, monospace'

    # ===== Font Scale（v6.1 7 级，px 逻辑像素） =====
    FS_HERO = 28      # 首页大标题（Hero 场景）
    FS_H1 = 20        # 主标题
    FS_H2 = 17        # 页内标题
    FS_H3 = 15        # 小标题 / 卡片标题
    FS_BODY = 13      # 正文
    FS_CAPTION = 12   # 辅助说明
    FS_MICRO = 11     # 极小字（时间戳、单位）

    # 兼容旧别名（值不变）
    SZ_HERO = '20px'
    SZ_TITLE = '17px'
    SZ_SECTION = '15px'
    SZ_BODY = '13px'
    SZ_SMALL = '12px'
    SZ_MICRO = '11px'

    # 字重（旧版字符串别名，值不变 —— 全项目 QSS 依赖）
    W_LIGHT = '300'
    W_NORMAL = 'Normal'
    W_MEDIUM = '500'
    W_BOLD = '600'
    W_BOLD_NUM = 700

    # 字重（v6.1 数字字重，新代码首选）
    W_REGULAR = 400
    W_MEDIUM_NUM = 500
    W_SEMIBOLD_NUM = 600
    W_BOLD_NUM = 700
    W_SEMIBOLD = 600

    # 旧版兼容
    FAMILY_CN = BODY
    FAMILY_KAI = TITLE
    FAMILY_SONG = TITLE
    FAMILY_SERIF = TITLE
    FAMILY_EN = MONO
    SIZE_TITLE = SZ_TITLE
    SIZE_SECTION = SZ_SECTION
    SIZE_KEY = '24px'
    SIZE_BODY = SZ_BODY
    SIZE_SMALL = SZ_SMALL
    SIZE_MICRO = SZ_MICRO
    WEIGHT_NORMAL = W_NORMAL
    WEIGHT_BOLD = W_BOLD

    # ===== DPI 字号缩放（UI 升级 M1-1） =====
    # 由 MainWindow._init_fonts() 按 devicePixelRatio 写入：>=1.5 → 1.125。
    # 默认 1.0（不缩放），保证纯逻辑/离屏环境下字号与改造前完全一致。
    FS_SCALE_FACTOR = 1.0

    @staticmethod
    def px(size: int) -> int:
        """按 DPI 缩放因子返回实际 px（偶数对齐，避免半像素字形模糊）。"""
        try:
            return int(round(float(size) * float(Fonts.FS_SCALE_FACTOR) / 2.0)) * 2
        except (TypeError, ValueError):
            return int(size)


class Spacing:
    """间距与圆角体系

    v6.1 引入 8-4 基准（整数像素 S0~S8 + 圆角/间距/内边距/控件尺寸令牌）。
    字符串值令牌（RADIUS/PAD/GAP 等，带 px）保留为旧版别名，值不变。
    """

    # ===== 8-4 基准体系（v6.1 整数像素，新代码首选） =====
    S0 = 0
    S1 = 4     # 图标-文字
    S2 = 8      # 内边距紧
    S3 = 12     # 控件间距
    S4 = 16     # 常规间距
    S5 = 20     # 卡片内边距
    S6 = 24     # 面板内边距
    S7 = 32     # 板块间距
    S8 = 48     # 大分区

    # ===== 额外间距令牌（覆盖调用方散落的非 4 倍数间距值，令牌化红线） =====
    # 纯新增令牌，不改动 S0~S8 既有值，保证回滚零破坏（方案 §7）。
    S_MIN = 2      # 最小间距（比 S0 大 2px）
    S_PAD_SM = 6   # 小内边距
    S_MARGIN_XS = 10  # 紧凑间距
    S_PAD_XS = 14  # 次内边距
    S_GAP_SM = 18  # 次间距
    S_MARGIN_EXTRA = 22  # 额外间距

    # 圆角（整数，4 的倍数，触控友好）
    # 注意：RADIUS_SM 的整数版命名为 RADIUS_SM_INT，避免被下方字符串别名段
    #      （RADIUS_SM = '6px'，供 QSS 模板使用）覆盖。RADIUS_INT/LG_INT/XL_INT 同理。
    RADIUS_XS = 4
    RADIUS_SM_INT = 6
    RADIUS_INT = 10
    RADIUS_LG_INT = 14
    RADIUS_XL_INT = 18
    RADIUS_PILL = 999

    # 行高 / 字距
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT = 1.6
    LINE_HEIGHT_LOOSE = 1.75
    LETTER_SPACING = 0.5   # px

    # 控件最小尺寸（整数像素）
    CONTROL_H_SM = 28
    CONTROL_H = 36
    CONTROL_H_LG = 44
    BUTTON_H = 40
    BUTTON_W_MIN = 100

    # ===== 旧版别名（字符串值，全项目 QSS 依赖，值不变） =====
    RADIUS = '10px'
    RADIUS_SM = '6px'
    RADIUS_LG = '14px'
    RADIUS_XL = '18px'
    PAD = '20px'
    PAD_LG = '28px'
    GAP = '14px'
    GAP_SM = '8px'

    # 旧版兼容
    CARD_RADIUS = RADIUS
    CONTROL_RADIUS = RADIUS_SM
    CARD_PADDING = PAD
    MODULE_GAP = GAP
    LINE_HEIGHT_STR = '1.6'
    LETTER_SPACING_STR = '0.5px'
    CONTROL_VERTICAL_GAP = '12px'
    BUTTON_MIN_HEIGHT = '40px'
    BUTTON_MIN_WIDTH = '100px'

    # ===== 栅格与密度档（UI 升级 M1-1） =====
    # 说明：本段为**纯新增**，不改动上表 S0~S8 / RADIUS / PAD 等既有值，
    #      保证「M1 令牌为纯新增，删除不影响既有值」的回滚承诺（方案 §7）。
    GRID_UNIT = 8                 # 基准网格（8px）
    COL_MAX_TEXT = 720            # 正文列最大宽度（px）—— 约 45 汉字 ×2 行宽上限
    COL_MAX_CARD = 1080           # 卡片区最大宽度（px）

    # 密度档：(页面边距, 卡片间距, 卡片内距, 正文行高)
    # 索引常量见下方 DENSITY_KEYS；元组顺序与 §4.2「三档密度」表格一一对应。
    DENSITY = {
        'compact': (20, 12, 16, 1.6),
        'normal': (24, 16, 20, 1.7),
        'spacious': (32, 16, 20, 1.75),
    }
    # 元组字段索引（避免调用方写魔法数字 0/1/2/3）
    D_PAD, D_GAP, D_INNER, D_LINE_HEIGHT = 0, 1, 2, 3

    LINE_HEIGHT_BODY = 1.7        # 正文统一行高（取代散落的 1.7/1.8/1.9/170%）
    LINE_HEIGHT_TITLE = 1.3

    # 响应式断点（窗口宽度 px）—— 与 §4.4 四档断点一致
    BP_XS = 900                   # < 900：单栏（splitter 转纵向）
    BP_S = 1100                   # 900–1099：紧凑双栏
    BP_L = 1440                   # ≥ 1440：宽屏（页面边距 S7）

    # 高 DPI 阈值：≥1.5 时整体降为 compact 档（字号放大由 Fonts.FS_SCALE_FACTOR 负责）
    DPI_SCALE_THRESHOLD = 1.5

    @staticmethod
    def density_for(width: int, dpi: float = 1.0) -> tuple:
        """按窗口宽度（+ DPI）返回密度档元组 (页面边距, 卡片间距, 卡片内距, 行高)。

        Args:
            width: 窗口宽度 px；<=0 时按标准档处理（离屏/未布局场景兜底）。
            dpi:   设备像素比；>= DPI_SCALE_THRESHOLD 时降级为 compact（高 DPI
                   小屏上 normal 档的 24px 边距会挤占正文列）。

        Returns:
            Spacing.DENSITY 中的某个 4 元组。
        """
        try:
            w = int(width or 0)
        except (TypeError, ValueError):
            w = 0
        if w > 0 and w < Spacing.BP_S:
            return Spacing.DENSITY['compact']
        if dpi >= Spacing.DPI_SCALE_THRESHOLD:
            return Spacing.DENSITY['compact']
        if w < Spacing.BP_L:
            return Spacing.DENSITY['normal']
        return Spacing.DENSITY['spacious']

    @staticmethod
    def scale(v: int, factor: float) -> int:
        """DPI 缩放：结果对齐到 4px 半格（8-4 体系）。"""
        try:
            return int(round(float(v) * float(factor) / 4.0)) * 4
        except (TypeError, ValueError, ZeroDivisionError):
            return int(v)


# ==================== 密度档应用（UI 升级 M1-1 / M3-1） ====================
# 四结果面板的内容区边距曾各写一套（result_panel 24 / meihua·liuren 0），
# 切板块时留白跳变（方案 Q03）。此处提供**唯一入口**，面板只允许通过它设置
# 内容布局的边距与间距，杜绝双层 padding 叠加与再次漂移。
DEFAULT_DENSITY = Spacing.DENSITY['normal']


def content_margins(density: tuple) -> tuple:
    """按密度档返回内容区 QLayout 边距 (left, top, right, bottom)。

    Args:
        density: Spacing.DENSITY 中的 4 元组。非法输入回退 DEFAULT_DENSITY。

    Returns:
        四元组边距；左右取「页面边距」pad，上下同值（内容区上下等距，
        与方案 §3.2「内容区左右边距一致性」验收项直接对应）。
    """
    if not density or len(density) < 2:
        density = DEFAULT_DENSITY
    pad = density[Spacing.D_PAD]
    return (pad, pad, pad, pad)


def apply_density(layout, density: tuple = None) -> None:
    """统一设置内容布局的边距与间距（全项目唯一入口）。

    Args:
        layout: QLayout 实例；None 时静默返回（防御性，面板未初始化场景）。
        density: Spacing.DENSITY 4 元组；None 时取 DEFAULT_DENSITY。
    """
    if layout is None:
        return
    if not density or len(density) < 2:
        density = DEFAULT_DENSITY
    pad = density[Spacing.D_PAD]
    gap = density[Spacing.D_GAP]
    layout.setContentsMargins(pad, pad, pad, pad)
    layout.setSpacing(gap)


def _build_font_scale_qss():
    """构建并填充 Stylesheets.FONT_SCALE（委托 typography 单一真相源）。

    延迟调用以避免 styles → typography → styles 循环导入。
    纯逻辑环境（无 PySide6）下优雅降级，不阻塞 import。
    """
    try:
        from ui.components.typography import _qss_font_scale
        Stylesheets.FONT_SCALE = _qss_font_scale()
        return Stylesheets.FONT_SCALE
    except ImportError:
        # 无 PySide6 环境（managed python / 纯脚本）下保留空占位
        return ''


# ==================== 键盘焦点环（P17 可访问性） ====================
# 实测结论（scripts/probe_qss_outline.py）：Qt QSS 有两条「静默失效」陷阱——
# ① **不支持 `outline` 属性**：写了被忽略（贴边金色像素 0），border 正常（708）
# ② **不支持 `:not()` 复合伪状态**：`:focus:not(:disabled)` 整条规则失效（0 像素），
#    单独 `:focus` 才生效。disabled 控件本就不可聚焦，无需 :not 保护。
# 故焦点环必须写 `QPushButton:focus { border: FOCUS_BORDER; }`。
# Qt 采用 border-box 盒模型，加粗 border 不改变控件外部尺寸，无需补偿 padding。
FOCUS_BORDER = f'2px solid {Colors.BRAND}'


class Stylesheets:
    """全局样式表集合"""

    # ==================== 排版 Font Scale（M3） ====================
    # 按 objectName 选择器（#t-hero ~ #t-value）的 Font Scale QSS。
    # 模块加载后由 _build_font_scale_qss() 填充为真实 QSS 字符串。
    FONT_SCALE = ''

    # ==================== 主窗口 ====================
    MAIN = f"""
        QMainWindow {{
            background-color: {Colors.BG};
        }}
        QWidget {{
            font-family: {Fonts.BODY};
        }}
        QToolTip {{
            background: {Colors.CARD};
            color: {Colors.TEXT};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            padding: 10px 14px;
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
        }}
    """

    # ==================== 顶部导航栏 ====================
    NAVBAR = f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFFFFF, stop:1 {Colors.GRADIENT_NAV_END});
            border-bottom: 1px solid {Colors.DIVIDER};
        }}
    """
    NAVBAR_LOGO = f"""
        QLabel {{
            font-size: 24px;
            color: {Colors.LIUJIN};
        }}
    """
    NAVBAR_TITLE = f"""
        QLabel {{
            font-size: 20px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 2px;
        }}
    """
    NAVBAR_BUTTON = f"""
        QPushButton {{
            background: transparent;
            color: {Colors.TEXT2};
            border: none;
            border-radius: {Spacing.RADIUS};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 8px 24px;
            min-height: 36px;
        }}
        QPushButton:hover {{
            color: {Colors.TEXT};
            background: {Colors.CARD};
        }}
        QPushButton:checked {{
            color: {Colors.TEXT_INV};
            background: {Colors.QINGHUA};
            font-weight: {Fonts.W_MEDIUM};
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """
    NAVBAR_ICON_BUTTON = f"""
        QPushButton {{
            background: transparent;
            color: {Colors.QINGHUA};
            border: 1px solid {Colors.QINGHUA_LIGHT};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 12px;
            padding: 2px;
            min-width: 24px;
            min-height: 24px;
        }}
        QPushButton:hover {{
            background: {Colors.QINGHUA_GLOW};
        }}
        QPushButton:pressed {{
            background: {Colors.QINGHUA};
            color: {Colors.TEXT_INV};
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """

    # ==================== 竖排侧边导航栏 ====================
    NAV_SIDEBAR = f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.BG}, stop:1 {Colors.BG_DARK});
            border-right: 1px solid {Colors.DIVIDER};
        }}
    """
    NAV_SIDEBAR_BUTTON = f"""
        QPushButton {{
            background: transparent;
            color: {Colors.TEXT3};
            border: none;
            border-radius: {Spacing.RADIUS};
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
            padding: 8px 12px;
            min-height: 44px;
            text-align: left;
        }}
        QPushButton:hover {{
            color: {Colors.TEXT};
            background: {Colors.HOVER};
        }}
        QPushButton:checked {{
            color: {Colors.LIUJIN};
            background: {Colors.QINGHUA_GLOW};
            border-left: 3px solid {Colors.LIUJIN};
            padding-left: 9px;
            font-weight: {Fonts.W_MEDIUM};
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """
    NAV_SIDEBAR_ICON = f"""
        QLabel {{
            font-size: 20px;
            color: {Colors.LIUJIN};
        }}
    """
    NAV_SIDEBAR_DIVIDER = f"background-color: {Colors.DIVIDER}; height: 1px;"

    # ==================== 卡片 ====================
    CARD = f"""
        QFrame {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS};
        }}
        QFrame:hover {{
            border-color: {Colors.BORDER2};
        }}
    """

    # ==================== 主按钮（朱砂红） ====================
    BTN_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.ZHUSHA};
            color: {Colors.TEXT_INV};
            border: none;
            border-radius: {Spacing.RADIUS_SM};
            font-size: 14px;
            font-weight: {Fonts.W_MEDIUM};
            font-family: {Fonts.BODY};
            padding: 10px 28px;
            min-height: 40px;
        }}
        QPushButton:hover {{
            background-color: {Colors.ZHUSHA_DARK};
        }}
        QPushButton:pressed {{
            background-color: {Colors.ZHUSHA_DARK};
        }}
        QPushButton:disabled {{
            background-color: {Colors.BORDER};
            color: {Colors.TEXT3};
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """

    # ==================== 次按钮 ====================
    BTN_SECONDARY = f"""
        QPushButton {{
            background-color: {Colors.CARD};
            color: {Colors.TEXT2};
            border: 1px solid {Colors.BORDER2};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 13px;
            font-family: {Fonts.BODY};
            padding: 10px 22px;
            min-height: 40px;
        }}
        QPushButton:hover {{
            background-color: {Colors.CARD_HOVER};
            border-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA};
        }}
        QPushButton:pressed {{
            background-color: {Colors.HOVER};
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """

    # ==================== 切换按钮 ====================
    BTN_SWITCH = f"""
        QPushButton {{
            background-color: {Colors.CARD};
            color: {Colors.TEXT2};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 12px;
            font-family: {Fonts.BODY};
            padding: 6px 16px;
        }}
        QPushButton:hover {{
            border-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA};
            background-color: {Colors.CARD_HOVER};
        }}
        QPushButton:checked {{
            background-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA_DARK};
            border-color: {Colors.QINGHUA};
            font-weight: {Fonts.W_BOLD};
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """

    # ==================== 分组框 ====================
    GROUPBOX = f"""
        QGroupBox {{
            background-color: transparent;
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            margin-top: 8px;
            padding-top: 12px;
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            top: 0px;
            padding: 0 6px;
            color: {Colors.TEXT};
        }}
    """

    # ==================== 输入框 ====================
    INPUT = f"""
        QLineEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 8px 12px;
            min-height: 36px;
            color: {Colors.TEXT};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
        }}
        QLineEdit:focus {{
            border: 1.5px solid {Colors.QINGHUA};
            background-color: {Colors.CARD_HOVER};
        }}
        QLineEdit:hover:!focus {{
            border-color: {Colors.BORDER2};
        }}
        QLineEdit::placeholder {{
            color: {Colors.TEXT3};
        }}
    """

    # ==================== 下拉框 ====================
    COMBO = f"""
        QComboBox {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 7px 28px 7px 12px;
            min-height: 36px;
            color: {Colors.TEXT};
        }}
        QComboBox:focus {{
            border: 1.5px solid {Colors.QINGHUA};
        }}
        QComboBox:hover:!focus {{
            border-color: {Colors.BORDER2};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
            subcontrol-origin: padding;
            subcontrol-position: right center;
            padding-right: 8px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Colors.TEXT3};
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {Colors.QINGHUA};
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            background: {Colors.CARD};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
            padding: 6px;
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            /* 原 `outline: none` 已移除：Qt QSS 不支持 outline，该行从未生效 */
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: 6px;
            min-height: 30px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {Colors.HOVER};
        }}
    """

    # ==================== 单选按钮 ====================
    RADIO = f"""
        QRadioButton {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 6px 14px;
            min-height: 32px;
            color: {Colors.TEXT};
        }}
        QRadioButton:hover {{
            border-color: {Colors.BORDER2};
            background-color: {Colors.CARD_HOVER};
        }}
        QRadioButton:checked {{
            border: 1.5px solid {Colors.QINGHUA};
            background-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA};
            font-weight: {Fonts.W_BOLD};
        }}
        QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border-radius: 7px;
            border: 1.5px solid {Colors.BORDER2};
        }}
        QRadioButton::indicator:checked {{
            background-color: {Colors.QINGHUA};
            border-color: {Colors.QINGHUA};
        }}
        QRadioButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """

    # ==================== 日期选择 ====================
    DATE = f"""
        QDateEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 7px 12px;
            min-height: 36px;
            color: {Colors.TEXT};
        }}
        QDateEdit:focus {{
            border: 1.5px solid {Colors.QINGHUA};
        }}
        QDateEdit:hover:!focus {{
            border-color: {Colors.BORDER2};
        }}
        QDateEdit::drop-down {{
            border: none;
            width: 22px;
        }}
        QDateEdit::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Colors.TEXT3};
        }}
        QDateEdit QCalendarWidget {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS};
        }}
        QDateEdit QCalendarWidget QToolButton {{
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
            padding: 6px;
            border-radius: {Spacing.RADIUS_SM};
        }}
        QDateEdit QCalendarWidget QToolButton:hover {{
            background-color: {Colors.HOVER};
        }}
        QDateEdit QCalendarWidget QAbstractItemView:enabled {{
            color: {Colors.TEXT};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
        }}
    """

    # ==================== 滚动条 ====================
    SCROLL = f"""
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 12px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.BORDER2};
            border-radius: 6px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Colors.QINGHUA};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 12px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {Colors.BORDER2};
            border-radius: 6px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {Colors.QINGHUA};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """

    # ==================== 状态栏 ====================
    STATUS = f"""
        QStatusBar {{
            background: {Colors.CARD};
            color: {Colors.TEXT3};
            border-top: 1px solid {Colors.DIVIDER};
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
            padding: 4px 16px;
            min-height: 30px;
        }}
        QStatusBar::item {{
            border: none;
        }}
    """

    # ==================== 提示框 ====================
    # Note: TOOLTIP is now included in MAIN, so we don't need to define it separately here.
    # But we keep it for compatibility if needed elsewhere.
    TOOLTIP = f"""
        QToolTip {{
            background: {Colors.CARD};
            color: {Colors.TEXT};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            padding: 10px 14px;
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
        }}
    """

    # ==================== 多行文本 ====================
    TEXT_EDIT = f"""
        QTextEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 8px 12px;
            color: {Colors.TEXT};
        }}
        QTextEdit:focus {{
            border: 1.5px solid {Colors.QINGHUA};
        }}
    """

    # ==================== 图标按钮 ====================
    BTN_ICON = f"""
        QPushButton {{
            background: transparent;
            color: {Colors.TEXT3};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
            padding: 6px 14px;
            min-height: 30px;
        }}
        QPushButton:hover {{
            background: {Colors.HOVER};
            color: {Colors.TEXT2};
            border-color: {Colors.BORDER2};
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """

    # ==================== 标签页/分组标题 ====================
    SECTION_HEADER = f"""
        QLabel {{
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
        }}
    """

    # ==================== 分割线 ====================
    DIVIDER_STYLE = f"background-color: {Colors.DIVIDER};"

    # ==================== 弹窗统一样式（M5） ====================
    # 三区分明：header / body / footer，全局 QDialog 继承
    DIALOG = f"""
        QDialog {{
            background: {Colors.BG};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
            font-size: {Fonts.SZ_BODY};
        }}
        QDialog QFrame#dialog-header {{
            background: {Colors.CARD};
            border-bottom: 1px solid {Colors.DIVIDER};
            border-radius: {Spacing.RADIUS_LG} {Spacing.RADIUS_LG} 0 0;
            padding: {Spacing.S5}px {Spacing.S6}px;
        }}
        QDialog QFrame#dialog-body {{
            background: {Colors.BG};
            padding: {Spacing.S6}px;
        }}
        QDialog QFrame#dialog-footer {{
            background: {Colors.CARD};
            border-top: 1px solid {Colors.DIVIDER};
            border-radius: 0 0 {Spacing.RADIUS_LG} {Spacing.RADIUS_LG};
            padding: {Spacing.S4}px {Spacing.S6}px;
        }}
    """

    # ==================== 按钮 6 态统一模型（M5 ButtonStates） ====================
    # 统一 default/hover/pressed/checked/disabled/focus 六态，供全局 QPushButton 注入
    def _btn_base(bg, fg, border):
        return f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: {Spacing.RADIUS_SM};
                padding: 0 20px;
                min-height: {Spacing.BUTTON_H}px;
                font-size: {Fonts.FS_BODY}px;
                font-family: {Fonts.BODY};
                font-weight: {Fonts.W_MEDIUM};
            }}
            QPushButton:hover {{
                background: {Colors.CARD_HOVER};
                border-color: {Colors.BRAND_LIGHT};
                color: {Colors.BRAND};
            }}
            QPushButton:pressed {{
                background: {Colors.BG_DARK};
            }}
            QPushButton:checked {{
                background: {Colors.BRAND};
                color: {Colors.TEXT_INV};
                border-color: {Colors.BRAND};
                font-weight: {Fonts.W_SEMIBOLD};
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT4};
                border-color: {Colors.BORDER};
            }}
            QPushButton:focus {{
                border: {FOCUS_BORDER};
            }}
        """

    BTN_6STATE_PRIMARY = _btn_base(Colors.ACCENT, Colors.TEXT, Colors.ACCENT_DARK)
    BTN_6STATE_SECONDARY = _btn_base(Colors.CARD, Colors.TEXT, Colors.BORDER2)
    BTN_6STATE_GHOST = _btn_base('transparent', Colors.TEXT2, 'transparent')
    BTN_6STATE_DANGER = _btn_base(Colors.DANGER_DARK, Colors.TEXT, '#8B3A2E')

    # ==================== 输入控件 4 态统一模型（M5） ====================
    # default/hover/focus/disabled，供输入类控件注入
    def _input_4state():
        return f"""
            QLineEdit, QComboBox, QDateEdit {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.FS_BODY}px;
                font-family: {Fonts.BODY};
                min-height: {Spacing.CONTROL_H}px;
                color: {Colors.TEXT};
            }}
            QLineEdit:hover:!focus, QComboBox:hover:!focus, QDateEdit:hover:!focus {{
                border-color: {Colors.BORDER2};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 1.5px solid {Colors.BRAND};
                background-color: {Colors.CARD_HOVER};
            }}
            QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled {{
                background: {Colors.BG_DARK};
                color: {Colors.TEXT4};
                border-color: {Colors.BORDER};
            }}
        """

    INPUT_4STATE = _input_4state()

    # ==================== 旧版兼容别名 ====================
    GOLD_DIVIDER = DIVIDER_STYLE
    SECTION_CARD = CARD
    LINE_EDIT = INPUT
    BUTTON_PRIMARY = BTN_PRIMARY
    BUTTON_SECONDARY = BTN_SECONDARY
    BUTTON_SWITCH = BTN_SWITCH
    COMBO_BOX = COMBO
    SCROLL_AREA = SCROLL
    SCROLL_BOOK = SCROLL
    LEFT_PANEL = f"background-color: {Colors.BG};"
    RIGHT_PANEL = f"background-color: {Colors.BG};"
    PARCHMENT_PANEL = f"background-color: {Colors.BG};"
    SEAL_BUTTON = BTN_PRIMARY
    WADANG_BUTTON = BTN_SECONDARY
    GUA_CARD = BTN_SWITCH
    SWITCH_BUTTON = BTN_SWITCH
    PARCHMENT_INPUT = INPUT
    SCROLL_COMBO = COMBO
    ANCIENT_DATE = DATE
    CLOUD_DIVIDER = DIVIDER_STYLE
    WOOD_FRAME = DIVIDER_STYLE
    MAIN_WINDOW = MAIN
    BOOK_PAGE = CARD
    PAN_TYPE_CARD = BTN_SWITCH
    GENDER_CARD = BTN_SWITCH
    BUTTON_HOUR = BTN_SWITCH
    TOGGLE_SWITCH = ""
    MEANDER_BORDER = ""
    WOOD_SEPARATOR = DIVIDER_STYLE
    INPUT_SEPARATOR = DIVIDER_STYLE
    LABEL_ANCIENT = f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};"
    CARD_SHADOW = Shadows.CARD
    CARD_SHADOW_HOVER = Shadows.CARD_HOVER
    NAVBAR_SHADOW = Shadows.NAVBAR
    SIDEBAR = NAV_SIDEBAR
    SIDEBAR_BUTTON = NAV_SIDEBAR_BUTTON
    FAMILY_CN = Fonts.BODY
    FAMILY_KAI = Fonts.TITLE
    FAMILY_SONG = Fonts.TITLE
    FAMILY_SERIF = Fonts.TITLE
    FAMILY_EN = Fonts.MONO
    SIZE_TITLE = Fonts.SZ_TITLE
    SIZE_SECTION = Fonts.SZ_SECTION
    SIZE_KEY = '24px'
    SIZE_BODY = Fonts.SZ_BODY
    SIZE_SMALL = Fonts.SZ_SMALL
    SIZE_MICRO = Fonts.SZ_MICRO
    WEIGHT_NORMAL = Fonts.W_NORMAL
    WEIGHT_BOLD = Fonts.W_BOLD


# 模块加载时填充 Font Scale QSS（委托 typography 单一真相源，避免双源漂移）
_build_font_scale_qss()