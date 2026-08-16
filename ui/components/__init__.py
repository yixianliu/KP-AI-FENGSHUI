"""
可复用界面组件包。

集中存放主窗口各标签页拼装所需的 Qt 控件，按职责分为四类：

  - 输入面板：input_panel（八字）、meihua_input（梅花易数）、liuren_input（大六壬）
  - 结果面板：result_panel、meihua_result_panel、liuren_result_panel
  - 通用构件：collapsible_card（结果显示卡片，含 AI 章节头与重点提示）
  - 对话框与后台任务：settings_dialog、about_dialog、export_dialog、ai_analysis_worker

组件只做界面渲染与信号发射，具体计算一律交由 core 层完成，便于单独测试与替换。
"""
