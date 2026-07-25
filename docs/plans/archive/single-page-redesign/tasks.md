# Tasks - 单界面集成应用重构

## 任务列表

- [x] Task 1: 重构主窗口布局 - 实现垂直三段式布局结构
  - [x] SubTask 1.1: 重写 `ui/main_window.py` 布局代码
  - [x] SubTask 1.2: 调整样式表适配新布局
  - [x] SubTask 1.3: 调整窗口尺寸策略

- [x] Task 2: 重构输入面板 - 实现横向表单布局
  - [x] SubTask 2.1: 重写 `ui/components/input_panel.py` 布局代码
  - [x] SubTask 2.2: 将表单元素改为水平排列
  - [x] SubTask 2.3: 调整提交按钮位置和样式
  - [x] SubTask 2.4: 添加输入验证反馈样式

- [x] Task 3: 重构结果面板 - 实现卡片网格布局
  - [x] SubTask 3.1: 重写 `ui/components/result_panel.py` 布局代码
  - [x] SubTask 3.2: 实现四张卡片的垂直堆叠布局
  - [x] SubTask 3.3: 为每张卡片添加折叠/展开功能
  - [x] SubTask 3.4: 添加单卡片复制按钮
  - [x] SubTask 3.5: 实现响应式网格（多列/单列切换）

- [x] Task 4: 验证和测试
  - [x] SubTask 4.1: 编译检查所有修改的文件
  - [x] SubTask 4.2: 测试完整排盘流程
  - [x] SubTask 4.3: 测试导出功能
  - [x] SubTask 4.4: 测试窗口缩放响应

## 任务依赖关系

```
Task 1 (主窗口重构)
    │
    ├── Task 2 (输入面板重构) 依赖于 Task 1 的布局基础
    │
    └── Task 3 (结果面板重构) 依赖于 Task 1 的布局基础
            │
            └── Task 4 (验证测试) 在 Task 2 和 Task 3 完成后执行
```

## 预期产出

1. 新的 `ui/main_window.py` - 垂直三段式布局
2. 新的 `ui/components/input_panel.py` - 横向表单布局
3. 新的 `ui/components/result_panel.py` - 卡片网格布局
