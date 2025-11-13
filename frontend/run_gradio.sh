#!/bin/bash

# Cool Papers - Gradio Frontend Launcher
# 启动 Gradio 版本的前端应用

echo "🚀 Starting Cool Papers Gradio Frontend..."
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# 检查是否安装了依赖
if ! python3 -c "import gradio" 2>/dev/null; then
    echo "⚠️  Gradio not found. Installing dependencies..."
    pip install -r requirements-gradio.txt
else
    echo "✓ Gradio is installed"
fi

# 检查后端 API 是否运行
echo ""
echo "🔍 Checking backend API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend API is running at http://localhost:8000"
else
    echo "⚠️  Backend API is not running!"
    echo "   Please start the backend first:"
    echo "   cd ../backend && python main.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 启动 Gradio 应用
echo ""
echo "🎉 Launching Gradio app..."
echo "📱 Frontend will be available at: http://localhost:7860"
echo "📚 Press Ctrl+C to stop"
echo ""

python3 gradio_app.py
