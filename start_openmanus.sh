#!/bin/bash

# OpenManus AI软件公司一键启动脚本
echo "🚀 启动 OpenManus AI软件公司..."

# 检查并杀死占用端口的进程
echo "🔍 检查端口占用情况..."

# 检查后端端口 8000
if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  端口 8000 被占用，正在停止相关进程..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# 检查前端端口 5173-5180 (Vite会自动寻找可用端口)
for port in {5173..5180}; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "⚠️  端口 $port 被占用，正在停止相关进程..."
        lsof -ti :$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
done

# 启动后端服务
echo "🔥 启动后端服务 (端口: 8000)..."
nohup python run_web_server.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 检查后端服务是否成功启动
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo "✅ 后端服务启动成功 (http://localhost:8000)"
else
    echo "❌ 后端服务启动失败，请检查 backend.log"
    echo "📄 显示后端日志最后10行："
    tail -10 backend.log
    exit 1
fi

# 启动前端服务
echo "🎨 启动前端服务..."
cd app/web
nohup npm run dev > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"
cd ../..

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 8

# 检查前端服务启动情况（检查多个可能的端口）
FRONTEND_URL=""
for port in {5173..5180}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port | grep -q "200"; then
        FRONTEND_URL="http://localhost:$port"
        break
    fi
done

if [ -n "$FRONTEND_URL" ]; then
    echo "✅ 前端服务启动成功 ($FRONTEND_URL)"
else
    echo "❌ 前端服务启动失败，请检查 frontend.log"
    echo "📄 显示前端日志最后10行："
    tail -10 frontend.log
    exit 1
fi

echo ""
echo "🎉 OpenManus AI软件公司启动完成！"
echo ""
echo "📋 服务信息："
echo "   后端服务: http://localhost:8000"
echo "   前端界面: $FRONTEND_URL"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "📝 日志文件："
echo "   后端日志: backend.log"
echo "   前端日志: frontend.log"
echo ""
echo "⚡ 快速访问："
echo "   在浏览器中打开: $FRONTEND_URL"
echo ""
echo "🛑 停止服务："
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 保存进程ID到文件
echo "BACKEND_PID=$BACKEND_PID" > .openmanus_pids
echo "FRONTEND_PID=$FRONTEND_PID" >> .openmanus_pids

echo "✨ 服务进程ID已保存到 .openmanus_pids 文件"
