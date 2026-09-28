# 设计令牌系统

本文档详细说明了 KP-AI-FENGSHUI 项目的设计令牌系统，包括颜色、阴影、字体、间距和动效等全局可复用的设计变量。

所有令牌均定义在 `ui/styles.py` 和 `ui/animation.py` 中，作为项目的「单一真相源」。

## 色彩体系

### 主色调（项目规范）
| 令牌 | 值 | 说明 |
|------|-----|------|
| `Colors.INK` | `#1a1a2e` | 深靛蓝（主色） |
| `Colors.GOLD` | `#c9a227` | 古金（强调/高亮） |
| `Colors.ZHONGYI` | `#8b0000` | 朱红（主操作/点缀） |

### 语义化权威命名（v6.1 单一真相源，新代码首选）
| 令牌 | 值 | 说明 |
|------|-----|------|
| `Colors.BRAND` | `#c9a227` | 品牌金：导航 / 选中 / 强调 / 图表主色 |
| `Colors.BRAND_LIGHT` | `#e8d08a` | - |
| `Colors.BRAND_DARK` | `#8f751c` | - |
| `Colors.BRAND_GLOW` | `rgba(201, 162, 39, 0.22)` | - |
| `Colors.ACCENT` | `#8b0000` | 主操作朱红：主按钮 / 主操作 / 警报 |
| `Colors.ACCENT_LIGHT` | `#C97A6A` | - |
| `Colors.ACCENT_DARK` | `#5E0000` | - |
| `Colors.ACCENT_GLOW` | `rgba(139, 0, 0, 0.25)` | - |
| `Colors.SEMANTIC_SUCCESS` | `#5DAF74` | 成功 / 吉 |
| `Colors.SEMANTIC_WARNING` | `#D8A94E` | 警告 / 需留意 |
| `Colors.SEMANTIC_DANGER` | `#C45545` | 危险 / 凶 |
| `Colors.DANGER_DARK` | `#A03E32` | 危险按钮专用深底（M7：浅字对比度 5.76:1） |
| `Colors.SEMANTIC_INFO` | `#7FB3C8` | 信息 / 中性 |

### 底色系 - 深靛蓝水墨
| 令牌 | 值 |
|------|-----|
| `Colors.BG` | `#1a1a2e` |
| `Colors.BG_DARK` | `#12121f` |
| `Colors.CARD` | `#21213a` |
| `Colors.HOVER` | `#262640` |
| `Colors.CARD_HOVER` | `#28284a` |
| `Colors.CARD_SELECTED` | `#2c2c4e` |

### 三色点缀 - 国风主题（保留，已等价于语义色）
| 令牌 | 等价于 |
|------|--------|
| `Colors.ZHUSHA` | `Colors.ACCENT` |
| `Colors.QINGHUA` | `Colors.BRAND` |
| `Colors.LIUJIN` | `Colors.BRAND` |

### 文字色彩（深底配浅色字）
| 令牌 | 值 |
|------|-----|
| `Colors.TEXT` | `#F5F1E8` |
| `Colors.TEXT2` | `#D8D3C8` |
| `Colors.TEXT3` | `#9C97A8` |
| `Colors.TEXT4` | `#918C9E` |
| `Colors.TEXT_INV` | `#12121f` |
| `Colors.WHITE` | `#FFFFFF` |

### 边框与分割
| 令牌 | 值 |
|------|-----|
| `Colors.BORDER` | `#33335A` |
| `Colors.BORDER2` | `#45456E` |
| `Colors.DIVIDER` | `#2E2E4C` |
| `Colors.DIVIDER_LIGHT` | `#262640` |

### 状态色彩（深色底优化对比度）
| 令牌 | 值 | 等价于 |
|------|-----|--------|
| `Colors.SUCCESS` | `#5DAF74` | `Colors.SEMANTIC_SUCCESS` |
| `Colors.SUCCESS_LIGHT` | `#2A4A38` | - |
| `Colors.WARNING` | `#D8A94E` | `Colors.SEMANTIC_WARNING` |
| `Colors.WARNING_LIGHT` | `#4A3E20` | - |
| `Colors.DANGER` | `#C45545` | `Colors.SEMANTIC_DANGER` |
| `Colors.DANGER_LIGHT` | `#4A2626` | - |
| `Colors.INFO` | `#7FB3C8` | `Colors.SEMANTIC_INFO` |
| `Colors.INFO_LIGHT` | `#1E3A4A` | - |

### 渐变（深色水墨）
| 令牌 | 值 |
|------|-----|
| `Colors.GRADIENT_WARM` | `#1a1a2e` |
| `Colors.GRADIENT_COOL` | `#141428` |
| `Colors.GRADIENT_NAV_START` | `#1a1a2e` |
| `Colors.GRADIENT_NAV_END` | `#12121f` |

### 水墨纹理（低透明度，深底微纹理）
| 令牌 | 值 |
|------|-----|
| `Colors.WATERMARK` | `rgba(201, 162, 39, 0.03)` |

### 五行色彩（深色底提亮以保可读性）
| 令牌 | 值 |
|------|-----|
| `Colors.WOOD` | `#7CB48E` |
| `Colors.WOOD_LIGHT` | `#A8D8B8` |
| `Colors.WOOD_DARK` | `#4A8A5E` |
| `Colors.FIRE` | `#E88870` |
| `Colors.FIRE_LIGHT` | `#F0B8A0` |
| `Colors.FIRE_DARK` | `#C45545` |
| `Colors.EARTH` | `#C0A878` |
| `Colors.EARTH_LIGHT` | `#D8C8A0` |
| `Colors.EARTH_DARK` | `#8B7355` |
| `Colors.METAL` | `#B8B0A0` |
| `Colors.METAL_LIGHT` | `#D8D0C0` |
| `Colors.METAL_DARK` | `#8A8278` |
| `Colors.WATER` | `#8AC8E8` |
| `Colors.WATER_LIGHT` | `#B0D8F0` |
| `Colors.WATER_DARK` | `#5B8FA8` |

### 新中式扩展色彩（视觉层次补充）
| 令牌 | 值 |
|------|-----|
| `Colors.XUANZHI` | `#F5F0E6` |
| `Colors.XUANZHI_LIGHT` | `#FAF7F0` |
| `Colors.XUANZHI_DARK` | `#E8E0CC` |
| `Colors.MO` | `#2C2C3A` |
| `Colors.MO_LIGHT` | `#3A3A50` |
| `Colors.MO_DARK` | `#1E1E2E` |

### 领域专用色（面板局部，不与品牌色冲突）
| 令牌 | 值 |
|------|-----|
| `Colors.INDIGO_DEEP` | `#4A5A8A` |
| `Colors.CANVAS_DARK` | `#0F0F1A` |

### 卡纸高亮渐变（关键柱/标题专用，暖宣纸色）
| 令牌 | 值 |
|------|-----|
| `Colors.HIGHLIGHT_WARM_STRONG` | `#FFFBF0` |
| `Colors.HIGHLIGHT_WARM` | `#FFF5E0` |
| `Colors.HIGHLIGHT_WARM_SOFT` | `#FFF9E8` |

### 浅色国风主题（导出对话框专用，语义化令牌）
| 令牌 | 值 |
|------|-----|
| `Colors.PAPER` | `#FFF8E7` |
| `Colors.PAPER_LIGHT` | `#FFF3D6` |
| `Colors.PAPER_HOVER` | `#FBF3DD` |
| `Colors.PAPER_BORDER` | `#E5D9B8` |
| `Colors.PAPER_ACTIVE` | `#F3E9CF` |
| `Colors.INK_PAPER` | `#5D4037` |
| `Colors.INK_PAPER_HOVER` | `#6B4423` |
| `Colors.INK_PAPER_BORDER` | `#4A3428` |
| `Colors.INK_PAPER_DARK` | `#3D2A20` |
| `Colors.INK_PAPER_DARKEST` | `#2D1F18` |
| `Colors.GOLD_PAPER` | `#D4AF37` |
| `Colors.GOLD_PAPER_DARK` | `#B08D3C` |
| `Colors.TEXT_PAPER` | `#333333` |
| `Colors.TEXT_PAPER_DIM` | `#8A8278` |

### PDF 导出专用调色板（打印介质）
| 令牌 | 值 |
|------|-----|
| `Colors.PDF_ZHUSHA` | `#C45545` |
| `Colors.PDF_QINGHUA` | `#4A7A90` |
| `Colors.PDF_LIUJIN` | `#B88A30` |
| `Colors.PDF_BG` | `#F7F4EE` |
| `Colors.PDF_CARD` | `#FFFFFF` |
| `Colors.PDF_TEXT` | `#333333` |
| `Colors.PDF_LINE` | `#D9CDB8` |
| `Colors.PDF_MUTED` | `#8A7F6B` |

### 其他语义色
| 令牌 | 值 | 等价于 |
|------|-----|--------|
| `Colors.YU` | `#5DAF74` | `Colors.SEMANTIC_SUCCESS` |
| `Colors.YU_LIGHT` | `#2A4A38` | `Colors.SUCCESS_LIGHT` |
| `Colors.SHANHU` | `#D8A94E` | `Colors.SEMANTIC_WARNING` |
| `Colors.SHANHU_LIGHT` | `#4A3E20` | `Colors.WARNING_LIGHT` |
| `Colors.DIANQING` | `#7FB3C8` | `Colors.SEMANTIC_INFO` |
| `Colors.DIANQING_LIGHT` | `#1E3A4A` | `Colors.INFO_LIGHT` |

### 水墨纹理透明度（用于背景装饰）
| 令牌 | 值 |
|------|-----|
| `Colors.INK_WASH_LOW` | `rgba(201, 162, 39, 0.04)` |
| `Colors.INK_WASH_MID` | `rgba(201, 162, 39, 0.08)` |

### 旧版兼容别名
> 以下别名值与对应的新令牌保持一致，仅为向后兼容保留，新代码请优先使用语义化权威命名。
| 令牌 | 等价于 |
|------|--------|
| `Colors.BACKGROUND` | `Colors.BG` |
| `Colors.PRIMARY` | `Colors.QINGHUA` (即 `Colors.BRAND`) |
| `Colors.PRIMARY_LIGHT` | `Colors.QINGHUA_LIGHT` |
| `Colors.PRIMARY_DARK` | `Colors.QINGHUA_DARK` |
| `Colors.ACCENT` | `Colors.ZHUSHA` (即 `Colors.ACCENT`) |
| `Colors.ACCENT_LIGHT` | `Colors.ZHUSHA_LIGHT` |
| `Colors.ACCENT_DARK` | `Colors.ZHUSHA_DARK` |
| `Colors.HIGHLIGHT` | `Colors.LIUJIN` (即 `Colors.BRAND`) |
| `Colors.HIGHLIGHT_LIGHT` | `Colors.LIUJIN_LIGHT` |
| `Colors.HIGHLIGHT_DARK` | `Colors.LIUJIN_DARK` |
| `Colors.HIGHLIGHT_GLOW` | `Colors.LIUJIN_GLOW` |
| `Colors.TEXT_PRIMARY` | `Colors.TEXT` |
| `Colors.TEXT_SECONDARY` | `Colors.TEXT2` |
| `Colors.TEXT_TERTIARY` | `Colors.TEXT3` |
| `Colors.TEXT_INVERSE` | `Colors.TEXT_INV` |
| `Colors.TEXT_SUB` | `Colors.TEXT2` |
| `Colors.BORDER_LIGHT` | `Colors.DIVIDER` |
| `Colors.HOVER_BG` | `Colors.HOVER` |
| `Colors.INPUT_BG` | `Colors.CARD` |
| `Colors.PARCHMENT` | `Colors.BG` |
| `Colors.PARCHMENT_LIGHT` | `Colors.BG` |
| `Colors.PARCHMENT_DARK` | `#12121f` |
| `Colors.BRONZE` | `#8A7A5A` |
| `Colors.BRONZE_LIGHT` | `#B0A070` |
| `Colors.BRONZE_DARK` | `#5A5A40` |

## 阴影体系

| 令牌 | 参数 | 说明 |
|------|------|------|
| `Shadows.CARD` | `{hex: '#000000', alpha: 0.35, offset: (0, 4), radius: 12}` | 卡片基础阴影 |
| `Shadows.CARD_HOVER` | `{hex: '#C9A227', alpha: 0.25, offset: (0, 6), radius: 16}` | 卡片悬浮阴影（金色发光） |
| `Shadows.ROW` | `{hex: '#000000', alpha: 18/255, offset: (0, 2), radius: 10}` | 概率统计行阴影（prob-row） |
| `Shadows.ROW_HOVER` | `{hex: '#000000', alpha: 32/255, offset: (0, 4), radius: 18}` | 概率统计行悬浮阴影 |
| `Shadows.NAVBAR` | `{hex: '#000000', alpha: 0.5, offset: (0, 2), radius: 4}` | 导航栏阴影 |

> 阴影效果通过 `apply_shadow(spec, eff)` 或 `make_shadow(spec)` 应用于 `QGraphicsDropShadowEffect` 实例。

## 字体体系

### 字体族
| 令牌 | 值 |
|------|-----|
| `Fonts.TITLE` | `"KaiTi", "SimSun", "STKaiti", "Noto Serif CJK SC", "Source Han Serif SC", serif` |
| `Fonts.BODY` | `"Microsoft YaHei", "微软雅黑", "PingFang SC", "Noto Sans CJK SC", sans-serif` |
| `Fonts.MONO` | `"Cascadia Code", "Consolas", "SF Mono", Monaco, monospace` |

### Font Scale（v6.1 7 级，px 逻辑像素）
| 令牌 | 值 (px) | 说明 |
|------|---------|------|
| `Fonts.FS_HERO` | 28 | 首页大标题（Hero 场景） |
| `Fonts.FS_H1` | 20 | 主标题 |
| `Fonts.FS_H2` | 17 | 页内标题 |
| `Fonts.FS_H3` | 15 | 小标题 / 卡片标题 |
| `Fonts.FS_BODY` | 13 | 正文 |
| `Fonts.FS_CAPTION` | 12 | 辅助说明 |
| `Fonts.FS_MICRO` | 11 | 极小字（时间戳、单位） |

### 兼容旧别名（值不变）
| 令牌 | 值 |
|------|-----|
| `Fonts.SZ_HERO` | `'20px'` |
| `Fonts.SZ_TITLE` | `'17px'` |
| `Fonts.SZ_SECTION` | `'15px'` |
| `Fonts.SZ_BODY` | `'13px'` |
| `Fonts.SZ_SMALL` | `'12px'` |
| `Fonts.SZ_MICRO` | `'11px'` |

### 字重（旧版字符串别名，值不变）
| 令牌 | 值 |
|------|-----|
| `Fonts.W_LIGHT` | `'300'` |
| `Fonts.W_NORMAL` | `'Normal'` |
| `Fonts.W_MEDIUM` | `'500'` |
| `Fonts.W_BOLD` | `'600'` |

### 字重（v6.1 数字字重，新代码首选）
| 令牌 | 值 |
|------|-----|
| `Fonts.W_REGULAR` | 400 |
| `Fonts.W_MEDIUM_NUM` | 500 |
| `Fonts.W_SEMIBOLD_NUM` | 600 |
| `Fonts.W_BOLD_NUM` | 700 |
| `Fonts.W_SEMIBOLD` | 600 |

### 旧版兼容
| 令牌 | 值 |
|------|-----|
| `Fonts.FAMILY_CN` | `Fonts.BODY` |
| `Fonts.FAMILY_KAI` | `Fonts.TITLE` |
| `Fonts.FAMILY_SONG` | `Fonts.TITLE` |
| `Fonts.FAMILY_SERIF` | `Fonts.TITLE` |
| `Fonts.FAMILY_EN` | `Fonts.MONO` |
| `Fonts.SIZE_TITLE` | `Fonts.SZ_TITLE` |
| `Fonts.SIZE_SECTION` | `Fonts.SZ_SECTION` |
| `Fonts.SIZE_KEY` | `'24px'` |
| `Fonts.SIZE_BODY` | `Fonts.SZ_BODY` |
| `Fonts.SIZE_SMALL` | `Fonts.SZ_SMALL` |
| `Fonts.SIZE_MICRO` | `Fonts.SZ_MICRO` |
| `Fonts.WEIGHT_NORMAL` | `Fonts.W_NORMAL` |
| `Fonts.WEIGHT_BOLD` | `Fonts.W_BOLD` |

## 间距与圆角体系

### 8-4 基准体系（v6.1 整数像素，新代码首选）
| 令牌 | 值 (px) | 说明 |
|------|---------|------|
| `Spacing.S0` | 0 | - |
| `Spacing.S1` | 4 | 图标-文字 |
| `Spacing.S2` | 8 | 内边距紧 |
| `Spacing.S3` | 12 | 控件间距 |
| `Spacing.S4` | 16 | 常规间距 |
| `Spacing.S5` | 20 | 卡片内边距 |
| `Spacing.S6` | 24 | 面板内边距 |
| `Spacing.S7` | 32 | 板块间距 |
| `Spacing.S8` | 48 | 大分区 |

### 圆角（整数，4 的倍数，触控友好）
| 令牌 | 值 (px) | 说明 |
|------|---------|------|
| `Spacing.RADIUS_XS` | 4 | - |
| `Spacing.RADIUS_SM_INT` | 6 | - |
| `Spacing.RADIUS_INT` | 10 | - |
| `Spacing.RADIUS_LG_INT` | 14 | - |
| `Spacing.RADIUS_XL_INT` | 18 | - |
| `Spacing.RADIUS_PILL` | 999 | 胶囊形圆角 |

### 行高 / 字距
| 令牌 | 值 |
|------|-----|
| `Spacing.LINE_HEIGHT_TIGHT` | 1.2 |
| `Spacing.LINE_HEIGHT` | 1.6 |
| `Spacing.LINE_HEIGHT_LOOSE` | 1.75 |
| `Spacing.LETTER_SPACING` | 0.5 px |

### 控件最小尺寸（整数像素）
| 令牌 | 值 (px) |
|------|---------|
| `Spacing.CONTROL_H_SM` | 28 |
| `Spacing.CONTROL_H` | 36 |
| `Spacing.CONTROL_H_LG` | 44 |
| `Spacing.BUTTON_H` | 40 |
| `Spacing.BUTTON_W_MIN` | 100 |

### 旧版别名（字符串值，全项目 QSS 依赖，值不变）
| 令牌 | 值 |
|------|-----|
| `Spacing.RADIUS` | `'10px'` |
| `Spacing.RADIUS_SM` | `'6px'` |
| `Spacing.RADIUS_LG` | `'14px'` |
| `Spacing.RADIUS_XL` | `'18px'` |
| `Spacing.PAD` | `'20px'` |
| `Spacing.PAD_LG` | `'28px'` |
| `Spacing.GAP` | `'14px'` |
| `Spacing.GAP_SM` | `'8px'` |

### 旧版兼容
| 令牌 | 值 |
|------|-----|
| `Spacing.CARD_RADIUS` | `Spacing.RADIUS` |
| `Spacing.CONTROL_RADIUS` | `Spacing.RADIUS_SM` |
| `Spacing.CARD_PADDING` | `Spacing.PAD` |
| `Spacing.MODULE_GAP` | `Spacing.GAP` |
| `Spacing.LINE_HEIGHT_STR` | `'1.6'` |
| `Spacing.LETTER_SPACING_STR` | `'0.5px'` |
| `Spacing.CONTROL_VERTICAL_GAP` | `'12px'` |
| `Spacing.BUTTON_MIN_HEIGHT` | `'40px'` |
| `Spacing.BUTTON_MIN_WIDTH` | `'100px'` |

## 动效令牌

### 缓动曲线（统一）
| 令牌 | 值 | 说明 |
|------|-----|------|
| `animation.EASING_STANDARD` | `QEasingCurve.InOutCubic` | 默认过渡（进出对称） |
| `animation.EASING_IN` | `QEasingCurve.InCubic` | 消失 / 离场 |
| `animation.EASING_OUT` | `QEasingCurve.OutCubic` | 出现 / 入场 |
| `animation.EASING_LINEAR` | `QEasingCurve.Linear` | 线性（hover 背景/即时反馈） |
| `animation.EASING_OVERSHOOT` | `QEasingCurve.OutBack` | 弹性回弹（数值弹跳等点缀） |

### 时长常量（毫秒，统一）
| 令牌 | 值 (ms) | 说明 |
|------|---------|------|
| `animation.DURATION_INSTANT` | 100 | 键盘反馈 / 即时响应 |
| `animation.DURATION_FAST` | 200 | hover 切换 |
| `animation.DURATION_NORMAL` | 300 | 默认动画（卡片折叠、板块切换） |
| `animation.DURATION_SLOW` | 500 | 卡片折叠（长内容） |
| `animation.DURATION_SLOWER` | 800 | 页面切换 / 大区块过渡 |

### 应用映射（组件 → 属性/时长/缓动）
| 动效名称 | 属性 | 时长 (ms) | 缓动 | 说明 |
|----------|------|-----------|------|------|
| `collapsible_height` | `maximumHeight` | 300 | InOutCubic | 卡片折叠高度动画 |
| `list_item_bg` | `background` | 100 | Linear | 列表项背景颜色过渡 |
| `card_shadow_hover` | `color` | 200 | InCubic | 卡片悬浮阴影颜色过渡 |
| `ai_stream_append` | `opacity` | 100 | Linear | AI 流式输出追加透明度 |
| `section_switch` | `opacity` | 300 | InOutCubic | 板块切换透明度过渡 |
| `timeline_hover` | `scale` | 200 | OutCubic | 时间轴悬浮缩放动画 |

> 应用映射定义在 `ui/animation.py` 的 `ANIMATION_MAP` 中，供审计脚本与组件文档引用。

## 使用规范

1. **首选语义化命名**：新代码中请优先使用 `Colors.BRAND`、`Colors.ACCENT` 等语义化权威命名，而非旧有命名（如 `Colors.QINGHUA`）。
2. **禁止裸色值**：业务文件不得写死硬编码色值，必须使用设计令牌。
3. **动效统一**：所有动效参数必须引用 `ui/animation.py` 中的令牌，禁止各自硬编码时长/缓动。
4. **间距与圆角**：新代码请使用 `Spacing.S*` 整数像素令牌，旧版字符串别名仅保留向后兼容。
5. **字体与字重**：新代码请使用 `Fonts.FS_*` 和 `Fonts.W_*` 数字令牌。

> 详细使用示例请参考 `docs/component-guide.md` 及各组件源码。