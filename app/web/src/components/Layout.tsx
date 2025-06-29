import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    ChatBubbleLeftRightIcon,
    HomeIcon,
    Cog6ToothIcon,
    CubeIcon
} from '@heroicons/react/24/outline';

interface LayoutProps {
    children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
    const location = useLocation();

    return (
        <div className="h-screen bg-gray-900 text-white flex flex-col">
            {/* 顶部导航栏 - 更像OpenHands的设计 */}
            <header className="bg-gray-800 border-b border-gray-600 px-6 py-4 flex items-center justify-between shadow-sm">
                <div className="flex items-center space-x-4">
                    <img
                        src="/assets/logo.jpg"
                        alt="OpenManus"
                        className="h-10 w-10 rounded-lg shadow-sm"
                    />
                    <div>
                        <h1 className="text-xl font-bold text-white">OpenManus</h1>
                        <p className="text-xs text-gray-400">AI需求分析助手</p>
                    </div>
                </div>

                <div className="flex items-center space-x-6">
                    <nav className="flex space-x-2">
                        <Link
                            to="/"
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${location.pathname === '/'
                                ? 'bg-blue-600 text-white shadow-md'
                                : 'text-gray-300 hover:text-white hover:bg-gray-700'
                                }`}
                        >
                            <HomeIcon className="h-4 w-4" />
                            <span>首页</span>
                        </Link>
                        <Link
                            to="/requirements"
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${location.pathname === '/requirements'
                                ? 'bg-blue-600 text-white shadow-md'
                                : 'text-gray-300 hover:text-white hover:bg-gray-700'
                                }`}
                        >
                            <ChatBubbleLeftRightIcon className="h-4 w-4" />
                            <span>需求分析</span>
                        </Link>
                        <Link
                            to="/architecture"
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${location.pathname === '/architecture'
                                ? 'bg-blue-600 text-white shadow-md'
                                : 'text-gray-300 hover:text-white hover:bg-gray-700'
                                }`}
                        >
                            <CubeIcon className="h-4 w-4" />
                            <span>架构设计</span>
                        </Link>
                    </nav>

                    <button className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-md transition-colors">
                        <Cog6ToothIcon className="h-5 w-5" />
                    </button>
                </div>
            </header>

            {/* 主要内容区域 */}
            <main className="flex-1 overflow-hidden">
                {children}
            </main>

            {/* 底部状态栏 - 更现代化的设计 */}
            <footer className="bg-gray-800 border-t border-gray-600 px-6 py-3 flex items-center justify-between text-sm">
                <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-2">
                        <span className="text-gray-300 font-medium">OpenManus</span>
                        <span className="text-gray-500">v2.0.0</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-gray-400">系统运行正常</span>
                    </div>
                </div>

                <div className="flex items-center space-x-4 text-gray-500">
                    <span>© 2024 OpenManus AI</span>
                </div>
            </footer>
        </div>
    );
}
