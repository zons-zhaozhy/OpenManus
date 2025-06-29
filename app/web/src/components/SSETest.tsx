import React, { useState, useRef } from 'react';

const SSETest: React.FC = () => {
    const [messages, setMessages] = useState<string[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);

    const startSSE = () => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        setMessages(['开始连接...']);
        setIsConnected(false);

        // 尝试使用完整URL而不是相对路径
        const url = `${window.location.protocol}//${window.location.host}/api/requirements/analyze/stream?content=${encodeURIComponent('test library system')}`;
        console.log('Attempting SSE connection to:', url);
        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            console.log('SSE connection opened');
            setIsConnected(true);
            setMessages(prev => [...prev, '✅ SSE连接已建立']);
        };

        eventSource.onmessage = (event) => {
            console.log('Raw SSE data:', event.data);
            try {
                const data = JSON.parse(event.data);
                console.log('Parsed SSE data:', data);
                setMessages(prev => [...prev, `${data.type}: ${data.message || JSON.stringify(data)}`]);
            } catch (e) {
                console.error('JSON parse error:', e);
                setMessages(prev => [...prev, `解析错误: ${event.data}`]);
            }
        };

        eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            console.error('EventSource readyState:', eventSource.readyState);
            console.error('EventSource url:', eventSource.url);

            let errorMessage = '❌ SSE连接错误';
            if (eventSource.readyState === EventSource.CONNECTING) {
                errorMessage += ' - 正在重连...';
            } else if (eventSource.readyState === EventSource.CLOSED) {
                errorMessage += ' - 连接已关闭';
            }

            setMessages(prev => [...prev, errorMessage]);
            setIsConnected(false);

            // 如果连接失败，尝试重连
            setTimeout(() => {
                if (eventSource.readyState === EventSource.CLOSED) {
                    setMessages(prev => [...prev, '🔄 尝试重新连接...']);
                    // 这里可以添加重连逻辑
                }
            }, 2000);
        };
    };

    const stopSSE = () => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
            setIsConnected(false);
            setMessages(prev => [...prev, '🛑 连接已关闭']);
        }
    };

    return (
        <div className="p-4 bg-gray-800 text-white rounded-lg">
            <h3 className="text-lg font-bold mb-4">SSE 连接测试</h3>

            <div className="flex space-x-2 mb-4">
                <button
                    onClick={startSSE}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
                >
                    开始测试
                </button>
                <button
                    onClick={stopSSE}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-white"
                >
                    停止测试
                </button>
                <div className={`px-3 py-2 rounded text-sm ${isConnected ? 'bg-green-600' : 'bg-gray-600'}`}>
                    {isConnected ? '已连接' : '未连接'}
                </div>
            </div>

            <div className="bg-gray-900 p-3 rounded max-h-96 overflow-y-auto">
                <h4 className="text-sm font-semibold mb-2">消息日志:</h4>
                {messages.map((message, index) => (
                    <div key={index} className="text-sm py-1 border-b border-gray-700">
                        {message}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SSETest;
