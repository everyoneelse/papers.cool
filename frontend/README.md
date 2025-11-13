# Cool Papers - Streamlit Frontend

🎉 **沉浸式刷论文！Immersive Paper Discovery**

基于 Streamlit 的 Cool Papers 前端实现，纯 Python 开发，无需懂前端技术。

## ✨ 功能特性

### 📚 核心功能
- ✅ **首页导航** - 分类选择、会议浏览、搜索入口
- ✅ **arXiv 浏览** - 按分类浏览最新论文
- ✅ **全文搜索** - 支持关键词搜索、过滤
- ✅ **会议论文** - 浏览顶会论文集
- ✅ **论文详情** - 标题、作者、摘要、分类
- ✅ **PDF 查看** - 在线预览 PDF
- ✅ **Kimi 摘要** - AI 生成论文摘要（需配置 API）
- ✅ **星标管理** - 收藏感兴趣的论文
- ✅ **导出功能** - 导出星标论文列表
- ✅ **RSS 订阅** - 订阅分类和会议
- ✅ **页面筛选** - 在列表中快速筛选

### 🎨 界面特点
- 现代化设计，响应式布局
- 绿色主题（与 papers.cool 一致）
- 清晰的导航结构
- 流畅的交互体验

## 🚀 快速开始

### 前置条件

1. **Python 3.8+**
2. **后端 API 运行中**（默认 `http://localhost:8000`）

### 安装步骤

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API 地址（可选）
# 编辑 .streamlit/secrets.toml 文件
# API_BASE_URL = "http://your-api-server:8000"

# 4. 启动应用
streamlit run streamlit_app.py

# 5. 浏览器自动打开，或访问：
# http://localhost:8501
```

## 📖 使用指南

### 1️⃣ 首页
- 选择感兴趣的 arXiv 分类（cs.AI, cs.CL, cs.CV 等）
- 点击 "View Selected Categories" 查看论文
- 点击会议名称浏览会议论文
- 使用搜索框进行全文搜索

### 2️⃣ arXiv 论文浏览
- 查看选中分类的最新论文
- 按日期、热度、星标数排序
- 使用页面内筛选功能
- 查看 RSS 订阅链接

### 3️⃣ 论文操作
- **📄 PDF** - 在线查看 PDF（嵌入式查看器）
- **🤖 Kimi** - 生成 AI 摘要（需配置 API Key）
- **🔗 Link** - 跳转到原始页面
- **⭐ Star** - 收藏论文到星标列表
- **📄 Abstract** - 展开查看详细摘要

### 4️⃣ 搜索功能
- 输入关键词搜索所有论文
- 按会议、分类过滤结果
- 设置最大返回数量

### 5️⃣ 星标管理
- 点击侧边栏 "⭐ Starred" 查看收藏
- 导出星标论文为 JSON 文件
- 便于跨设备同步或分享

## ⚙️ 配置说明

### API 地址配置

编辑 `.streamlit/secrets.toml`：

```toml
API_BASE_URL = "http://localhost:8000"
```

### 主题配置

编辑 `.streamlit/config.toml`：

```toml
[theme]
primaryColor = "#32a852"      # 绿色主题
backgroundColor = "#FFFFFF"    # 白色背景
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### Kimi API 配置（可选）

在 `.streamlit/secrets.toml` 中添加：

```toml
KIMI_API_KEY = "your_api_key_here"
```

然后在代码中集成 Kimi API 调用。

## 📁 项目结构

```
frontend/
├── streamlit_app.py          # 主应用文件
├── requirements.txt          # Python 依赖
├── README.md                 # 本文档
├── .streamlit/
│   ├── config.toml          # Streamlit 配置
│   └── secrets.toml         # API 密钥配置
└── .gitignore               # Git 忽略文件
```

## 🎯 页面结构

```
streamlit_app.py
├── page_home()              # 首页 - 分类选择
├── page_arxiv()             # arXiv 论文列表
├── page_search()            # 搜索页面
├── page_venue()             # 会议论文页面
├── page_starred()           # 星标论文页面
└── render_paper_card()      # 论文卡片组件
```

## 🔌 API 接口使用

本应用调用以下后端 API：

```python
# 获取 arXiv 论文
GET /papers/arxiv/combined?include=cs.AI,cs.LG&date=2024-01-15

# 搜索论文
GET /search/?query=transformer&max_results=100

# 获取会议论文
GET /papers/venue/NeurIPS

# 获取单篇论文
GET /papers/arxiv/2401.12345

# RSS 订阅
GET /feeds/arxiv/cs.AI
GET /feeds/venue/ICLR
```

## 🎨 自定义样式

在 `streamlit_app.py` 中，你可以修改自定义 CSS：

```python
st.markdown("""
<style>
/* 你的自定义样式 */
.stButton>button {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)
```

## 🚢 部署

### 本地部署
```bash
streamlit run streamlit_app.py
```

### Streamlit Cloud 部署
1. 推送代码到 GitHub
2. 访问 [streamlit.io/cloud](https://streamlit.io/cloud)
3. 连接仓库并部署
4. 在设置中配置 `API_BASE_URL`

### Docker 部署
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```

## 🔧 故障排查

### 问题 1: API 连接失败
**症状**: 显示 "API 错误" 或 "Failed to load papers"

**解决方案**:
1. 确认后端 API 正在运行：`curl http://localhost:8000/health`
2. 检查 `.streamlit/secrets.toml` 中的 `API_BASE_URL` 配置
3. 查看后端日志是否有错误

### 问题 2: 论文列表为空
**症状**: "No papers found"

**解决方案**:
1. 检查后端数据库是否有数据
2. 运行后端更新脚本：`python backend/scripts/update_papers.py`
3. 尝试选择不同的日期或分类

### 问题 3: PDF 无法显示
**症状**: PDF iframe 显示空白

**解决方案**:
1. 某些 PDF 服务器不允许 iframe 嵌入
2. 改用 "Link" 按钮在新标签页打开
3. 或使用 PDF.js 等替代方案

### 问题 4: 样式异常
**症状**: 界面显示混乱

**解决方案**:
1. 清除浏览器缓存
2. 更新 Streamlit：`pip install --upgrade streamlit`
3. 检查 `.streamlit/config.toml` 配置

## 💡 开发提示

### 添加新功能

1. **添加新页面**:
```python
def page_my_feature():
    st.title("My Feature")
    # 你的代码

# 在 main() 中添加路由
if current_page == "my_feature":
    page_my_feature()
```

2. **添加新组件**:
```python
def render_my_component(data):
    with st.container():
        st.markdown(f"**{data['title']}**")
        # 更多组件
```

3. **添加 API 调用**:
```python
def api_post(endpoint, data):
    with httpx.Client() as client:
        response = client.post(f"{API_BASE_URL}{endpoint}", json=data)
        return response.json()
```

### 性能优化

1. **使用缓存**:
```python
@st.cache_data(ttl=3600)
def get_papers(category):
    return api_get(f"/papers/arxiv/list/{category}")
```

2. **分页加载**:
```python
# 使用 st.pagination() 或手动实现
papers_per_page = 20
page = st.number_input("Page", min_value=1)
start = (page - 1) * papers_per_page
end = start + papers_per_page
display_papers = papers[start:end]
```

3. **延迟加载**:
```python
# 使用 st.expander() 包裹大内容
with st.expander("Show Details", expanded=False):
    render_large_content()
```

## 📊 与原版对比

| 功能 | 原版 papers.cool | Streamlit 版 | 说明 |
|------|-----------------|--------------|------|
| arXiv 浏览 | ✅ | ✅ | 完全实现 |
| 会议论文 | ✅ | ✅ | 完全实现 |
| 全文搜索 | ✅ | ✅ | 完全实现 |
| PDF 查看 | ✅ | ✅ | iframe 嵌入 |
| Kimi 摘要 | ✅ | 🔌 | 需配置 API |
| 星标收藏 | ✅ | ✅ | 完全实现 |
| RSS 订阅 | ✅ | ✅ | 链接形式 |
| 延迟加载 | ✅ | ⚠️ | 可优化 |
| 响应式设计 | ✅ | ✅ | Streamlit 原生 |
| 离线使用 | ❌ | ❌ | 需网络连接 |

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 许可证

MIT License

## 🙏 致谢

- [Cool Papers](https://papers.cool) - 原版项目
- [Streamlit](https://streamlit.io) - 快速构建应用
- [科学空间](https://kexue.fm) - 项目灵感来源

---

**Enjoy immersive paper reading!** 📚✨
