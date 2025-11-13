#!/bin/bash

# Cool Papers Streamlit Frontend 启动脚本

echo "🚀 Starting Cool Papers Frontend..."

# 检查是否安装了 streamlit
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install -r requirements.txt
fi

# 检查后端是否运行
echo "🔍 Checking backend API..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API is running"
else
    echo "⚠️  Warning: Backend API not responding at http://localhost:8000"
    echo "   Please make sure to start the backend first:"
    echo "   cd ../backend && python main.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 启动 Streamlit
echo "📚 Launching Cool Papers..."
streamlit run streamlit_app.py --server.port=8501
