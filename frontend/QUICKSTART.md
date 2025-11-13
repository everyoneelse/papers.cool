# 🚀 Cool Papers Frontend - 快速启动指南

## 5 分钟上手

### 步骤 1: 启动后端 API

```bash
# 在第一个终端窗口
cd backend
pip install -r requirements.txt
python main.py
```

等待看到：
```
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 步骤 2: 启动前端

```bash
# 在第二个终端窗口
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

或者使用启动脚本：
```bash
cd frontend
./run.sh
```

### 步骤 3: 访问应用

浏览器自动打开，或访问：
- **前端**: http://localhost:8501
- **后端 API 文档**: http://localhost:8000/docs

---

## 📖 使用示例

### 1. 浏览 arXiv 论文

1. 在首页选择分类（如 cs.AI, cs.LG）
2. 点击 "📖 View Selected Categories"
3. 浏览最新论文列表
4. 点击 "📄 PDF" 查看论文
5. 点击 "⭐" 收藏感兴趣的论文

### 2. 搜索论文

1. 在首页搜索框输入关键词（如 "transformer attention"）
2. 点击 "Go" 按钮
3. 查看搜索结果
4. 可以按会议、分类过滤

### 3. 浏览会议论文

1. 在首页点击会议名称（如 "NeurIPS"）
2. 查看该会议的所有论文
3. 复制 RSS 订阅链接

### 4. 管理星标

1. 点击侧边栏 "⭐ Starred"
2. 查看所有收藏的论文
3. 点击 "📤 Export" 导出为 JSON

---

## ⚙️ 配置

### API 地址（可选）

如果后端不在本地，编辑 `.streamlit/secrets.toml`:

```toml
API_BASE_URL = "http://your-server:8000"
```

### 主题颜色（可选）

编辑 `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#32a852"  # 改成你喜欢的颜色
```

---

## 🎯 核心功能速览

| 功能 | 位置 | 说明 |
|------|------|------|
| **分类浏览** | 首页 → 选择分类 → View | 浏览 arXiv 各分类论文 |
| **会议论文** | 首页 → 点击会议名 | 浏览顶会论文 |
| **搜索** | 首页 → 搜索框 | 全文搜索所有论文 |
| **PDF 查看** | 论文卡片 → PDF 按钮 | 在线预览 PDF |
| **AI 摘要** | 论文卡片 → Kimi 按钮 | 生成论文摘要（需配置）|
| **收藏** | 论文卡片 → ⭐ 按钮 | 星标收藏论文 |
| **导出** | 星标页面 → Export | 导出星标列表 |
| **RSS 订阅** | 各列表页面 | 复制订阅链接 |
| **筛选** | 列表页面 → Filter | 页面内快速筛选 |

---

## 🐛 常见问题

### Q1: "API 错误" 或无法加载论文

**A**: 检查后端是否运行：
```bash
curl http://localhost:8000/health
```

如果返回 `{"status": "healthy"}` 说明正常。

### Q2: 论文列表为空

**A**: 后端数据库可能没有数据，运行更新脚本：
```bash
cd backend
python scripts/update_papers.py
```

### Q3: PDF 无法显示

**A**: 某些 PDF 不支持 iframe 嵌入，点击 "🔗 Link" 在新标签页打开。

### Q4: Kimi 摘要不工作

**A**: 需要配置 Kimi API Key：
1. 在 `.streamlit/secrets.toml` 添加：
   ```toml
   KIMI_API_KEY = "your_key"
   ```
2. 在代码中集成 API 调用（见开发文档）

---

## 🎨 界面预览

```
┌─────────────────────────────────────────┐
│  📚 Cool Papers                         │
├─────────────────────────────────────────┤
│                                         │
│  🔬 arXiv Categories                    │
│  ☑ cs.AI   ☑ cs.CL   ☐ cs.CV          │
│  ☑ cs.LG   ☐ cs.NE   ☐ stat.ML        │
│                                         │
│  📖 View Selected Categories            │
│                                         │
│─────────────────────────────────────────│
│                                         │
│  🎓 Conference Papers (Venue)           │
│  [AAAI] [ACL] [ICLR] [NeurIPS] ...     │
│                                         │
│─────────────────────────────────────────│
│                                         │
│  🔍 Search Papers                       │
│  [__________________] [Go]              │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📚 更多文档

- **完整文档**: 查看 `README.md`
- **API 文档**: http://localhost:8000/docs
- **后端文档**: `../backend/README.md`

---

## 🆘 获取帮助

遇到问题？

1. 查看日志输出
2. 检查后端 API 是否正常
3. 阅读 `README.md` 故障排查部分
4. 提交 Issue

---

**Happy Paper Reading!** 📚✨
