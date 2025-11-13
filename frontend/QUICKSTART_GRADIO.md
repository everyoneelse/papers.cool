# Cool Papers - Gradio 版本快速启动指南

## 🚀 5 分钟快速上手

### 方法 1: 使用启动脚本（推荐）

```bash
# 1. 进入前端目录
cd frontend

# 2. 运行启动脚本
./run_gradio.sh
```

脚本会自动：
- ✅ 检查 Python 环境
- ✅ 安装必要依赖
- ✅ 验证后端 API
- ✅ 启动 Gradio 应用

访问：http://localhost:7860

---

### 方法 2: 手动启动

```bash
# 1. 安装依赖
pip install -r requirements-gradio.txt

# 2. 启动应用
python gradio_app.py
```

---

### 方法 3: Docker 启动

```bash
# 1. 构建镜像
docker build -t coolpapers-gradio -f Dockerfile.gradio .

# 2. 运行容器
docker run -p 7860:7860 \
  -e API_BASE_URL=http://host.docker.internal:8000 \
  coolpapers-gradio
```

---

### 方法 4: Docker Compose（完整部署）

```bash
# 启动前端和后端
docker-compose -f docker-compose-gradio.yml up -d

# 查看日志
docker-compose -f docker-compose-gradio.yml logs -f

# 停止服务
docker-compose -f docker-compose-gradio.yml down
```

---

## 📝 前置要求

### 必需
- Python 3.8 或更高版本
- 后端 API 运行在 http://localhost:8000

### 检查后端状态
```bash
curl http://localhost:8000/health
# 应返回: {"status":"healthy"}
```

### 启动后端（如果未运行）
```bash
# 在另一个终端
cd backend
pip install -r requirements.txt
python main.py
```

---

## 🎯 首次使用

### 1. 浏览 arXiv 论文
1. 点击 "📚 arXiv" 标签
2. 选择分类（默认已选 AI, CL, LG）
3. 选择日期（默认今天）
4. 点击 "🔄 Fetch Papers"

### 2. 搜索论文
1. 点击 "🔍 Search" 标签
2. 输入关键词（如 "transformer"）
3. 点击 "🔍 Search"

### 3. 管理星标
1. 浏览论文时点击星标
2. 切换到 "⭐ Starred" 标签
3. 点击 "📤 Export" 导出

---

## ⚙️ 配置

### 更改 API 地址
```bash
export API_BASE_URL="http://your-backend:8000"
python gradio_app.py
```

### 更改端口
编辑 `gradio_app.py` 第 382 行：
```python
app.launch(server_port=8080)  # 改为你想要的端口
```

---

## 🆚 Gradio vs Streamlit

选择 Gradio 版本，如果你：
- ✅ 喜欢 Material Design 风格
- ✅ 需要快速部署和分享
- ✅ 想要更好的并发性能
- ✅ 熟悉 Hugging Face 生态

选择 Streamlit 版本，如果你：
- ✅ 喜欢简约风格
- ✅ 需要更多自定义组件
- ✅ 想要更丰富的数据可视化
- ✅ 熟悉 Streamlit 生态

两个版本功能完全相同！

---

## 🔧 故障排查

### 问题：导入错误
```bash
# 重新安装依赖
pip install --upgrade -r requirements-gradio.txt
```

### 问题：API 连接失败
```bash
# 检查后端
curl http://localhost:8000/health

# 启动后端
cd backend && python main.py
```

### 问题：端口被占用
```bash
# 查找进程
lsof -i :7860

# 杀死进程
kill -9 <PID>
```

---

## 📚 下一步

- 📖 阅读完整文档: [README_GRADIO.md](README_GRADIO.md)
- 🔌 查看 API 文档: http://localhost:8000/docs
- 💡 自定义主题和样式
- 🚢 部署到 Hugging Face Spaces

---

## 🎉 开始使用！

```bash
cd frontend
./run_gradio.sh
```

然后访问 http://localhost:7860

**Happy paper reading!** 📚✨
