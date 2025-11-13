# Cool Papers - 简化版Gradio界面

这是一个极简的单页面论文浏览和搜索应用。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements-gradio.txt
```

### 2. 准备数据

在 `papers_data` 目录下放置按日期命名的JSON文件：

```
papers_data/
├── papers_2025-11-13.json
├── papers_2025-11-12.json
└── papers_2025-11-11.json
```

每个JSON文件格式：

```json
[
  {
    "id": "2311.12345",
    "title": "论文标题",
    "authors": ["作者1", "作者2", "作者3"],
    "abstract": "论文摘要...",
    "categories": ["cs.AI", "cs.LG"],
    "published_date": "2025-11-13",
    "url": "https://arxiv.org/abs/2311.12345",
    "pdf_url": "https://arxiv.org/pdf/2311.12345.pdf"
  }
]
```

### 3. 运行应用

```bash
python gradio_app.py
```

访问：http://localhost:7860

## 功能特点

### ✅ 单页面设计
- 无需在多个标签页间切换
- 所有功能一目了然

### ✅ 论文浏览
1. 输入日期（YYYY-MM-DD格式）
2. 从下拉框选择分类（可多选）
3. 论文自动加载并显示在表格中

### ✅ 论文搜索
1. 保持日期和分类选择
2. 输入关键词
3. 点击"搜索"按钮
4. 查看搜索结果（仅在当前日期范围内）

### ✅ 论文信息
- **标题**：可点击链接直接访问
- **作者**：最多显示5位作者
- **摘要**：自动截断长文本
- **分类**：显示所有arxiv分类

## 配置

通过环境变量配置：

```bash
export DATA_DIR="./papers_data"           # 数据目录
export SEARCH_INDEX_PATH="./search_index" # 搜索索引目录（可选）
```

## 支持的ArXiv分类

- cs.AI - Artificial Intelligence
- cs.CL - Computation and Language
- cs.CV - Computer Vision
- cs.LG - Machine Learning
- cs.NE - Neural and Evolutionary Computing
- cs.CC - Computational Complexity
- stat.ML - Statistics - Machine Learning

## 搜索功能

当前使用简单的字符串匹配搜索标题和摘要。

### 升级到Tantivy（可选）

安装tantivy：
```bash
pip install tantivy
```

然后修改 `search_papers_with_tantivy` 函数实现真正的全文搜索。

## 示例数据

项目包含了示例数据文件：
- `papers_data/papers_2025-11-13.json` - 8篇示例论文

您可以直接使用这些数据测试应用。

## 界面截图说明

1. **顶部**：日期输入框
2. **第二行**：分类多选下拉框
3. **状态行**：显示加载状态和论文数量
4. **论文表格**：显示所有匹配的论文
5. **分隔线下方**：搜索功能区
6. **搜索结果表格**：显示搜索结果

## 常见问题

### Q: 为什么看不到论文？
A: 请确保：
- 日期格式正确（YYYY-MM-DD）
- 对应日期的JSON文件存在
- JSON文件格式正确

### Q: 搜索没有结果？
A: 搜索仅在当前选定日期的论文中进行，请：
- 确认日期已选择
- 确认该日期有论文数据
- 尝试更通用的关键词

### Q: 如何添加更多分类？
A: 编辑 `gradio_app.py` 中的 `ARXIV_CATEGORIES` 字典。

## 技术栈

- **Gradio**: 4.0+
- **Pandas**: 数据展示
- **Python**: 3.8+

## 未来改进

- [ ] 集成真正的Tantivy全文搜索
- [ ] 数据缓存机制
- [ ] 自动从arXiv API获取数据
- [ ] 导出功能
- [ ] 论文收藏功能
- [ ] 高级搜索（正则、布尔表达式）

---

**提示**：这是一个极简版本，专注于核心功能。如需更多功能，请参考完整版本。
