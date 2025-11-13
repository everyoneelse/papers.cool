# Streamlit 应用重构 - 去除侧边栏和多页面

**日期**: 2025-11-13 09:34:13

## 任务概述

重构 Streamlit 应用，简化界面结构：
1. 去掉 starred 页面
2. 去掉 home 页面
3. 将 arXiv 和 search 合并到一个页面
4. 去掉侧边栏
5. 将 arXiv 分类移到主页面上

## 主要改动

### 1. 页面结构简化

**之前**:
- 多页面架构（Home、arXiv、Search、Starred）
- 使用侧边栏导航
- 侧边栏包含分类选择和统计信息

**之后**:
- 单页面架构
- arXiv 分类直接显示在页面顶部
- 使用两个 tab 标签页：
  - 📅 Browse by Date (按日期浏览)
  - 🔍 Search Papers (搜索论文)

### 2. 分类选择位置变更

将 arXiv 分类选择从侧边栏移到主页面顶部，使用 4 列布局展示所有分类：
- Artificial Intelligence (cs.AI)
- Computation and Language (cs.CL)
- Computer Vision (cs.CV)
- Machine Learning (cs.LG)
- Neural and Evolutionary Computing (cs.NE)
- Computational Complexity (cs.CC)
- Statistics - Machine Learning (stat.ML)

### 3. 侧边栏完全隐藏

- 设置 `initial_sidebar_state="collapsed"`
- 通过 CSS 隐藏侧边栏切换按钮
- 移除所有侧边栏相关的导航逻辑

### 4. 删除的功能

- Home 页面（不再需要独立的首页）
- Starred 页面（星标功能保留，但不显示星标列表页面）
- 页面间导航逻辑
- 侧边栏导航菜单

### 5. 保留的功能

- 论文卡片渲染
- 星标功能（可以标记论文，统计显示在页面顶部）
- 浏览记录统计
- PDF 查看器
- Kimi 摘要（占位功能）
- 按日期浏览 arXiv 论文
- 关键词搜索论文
- 分类过滤

## 代码变更

### 主要函数变更

1. **删除的函数**:
   - `page_home()` - 首页
   - `page_starred()` - 星标页面
   - `page_arxiv()` - 单独的 arXiv 页面
   - `page_search()` - 单独的搜索页面

2. **保留的函数**:
   - `api_get()` - API 调用
   - `render_paper_card()` - 论文卡片渲染

3. **重写的函数**:
   - `main()` - 主应用逻辑，改为单页面设计

### 新的布局结构

```
主页面
├── 标题: "📚 Immersive Paper Discovery（沉浸式刷论文！）"
├── arXiv 分类选择区域 (4列布局)
├── 统计信息 (3列: Starred, Viewed, Categories)
├── Tabs 标签页
│   ├── 📅 Browse by Date
│   │   ├── 日期选择
│   │   ├── 结果数量设置
│   │   ├── View Papers 按钮
│   │   └── 论文列表展示
│   └── 🔍 Search Papers
│       ├── 搜索框
│       ├── 结果数量设置
│       ├── 分类过滤选项
│       └── 搜索结果展示
└── 页脚 (链接到 GitHub, Blog, API Docs)
```

## 用户体验改进

1. **更简洁的界面**: 所有功能集中在一个页面，无需切换
2. **更直观的操作**: 分类选择和功能入口都在主视图中
3. **更快的访问**: 无需通过侧边栏导航即可使用所有功能
4. **更清晰的功能分区**: 使用 Tab 标签页区分浏览和搜索两种主要使用场景

## 技术细节

- 页面配置修改为隐藏侧边栏
- 使用 `st.tabs()` 创建标签页界面
- 使用 `st.columns()` 创建多列布局
- 保留所有原有的 session state 管理
- 保留所有 API 调用逻辑

## 文件变更

- 修改文件: `/workspace/frontend/streamlit_app.py`
- 代码行数: 从 514 行减少到约 330 行
- 删除代码: 约 200 行（删除多个页面函数和侧边栏逻辑）
- 新增代码: 约 16 行（新的单页面布局）

## 测试建议

1. 验证分类选择功能是否正常工作
2. 测试按日期浏览功能
3. 测试搜索功能
4. 验证星标功能仍然可用
5. 检查论文卡片渲染是否正常
6. 确认 PDF 和 Kimi 按钮功能

## 后续优化建议

1. 可以考虑添加星标论文的快速查看功能（例如在一个 expander 中）
2. 可以添加最近浏览历史功能
3. 可以优化搜索结果的排序选项
4. 可以添加论文导出功能
