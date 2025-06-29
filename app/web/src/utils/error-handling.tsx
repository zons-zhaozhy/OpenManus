import React from 'react';
import { toast } from 'react-toastify';

// 错误类型定义
export enum ErrorType {
    // 网络错误
    NETWORK_ERROR = 'NETWORK_ERROR',
    // API错误
    API_ERROR = 'API_ERROR',
    // 验证错误
    VALIDATION_ERROR = 'VALIDATION_ERROR',
    // 超时错误
    TIMEOUT_ERROR = 'TIMEOUT_ERROR',
    // 未知错误
    UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

// 错误配置
const ERROR_CONFIG = {
    [ErrorType.NETWORK_ERROR]: {
        title: '网络错误',
        message: '请检查您的网络连接',
        icon: '🌐',
        type: 'error' as const
    },
    [ErrorType.API_ERROR]: {
        title: 'API错误',
        message: '服务器响应异常',
        icon: '🔧',
        type: 'error' as const
    },
    [ErrorType.VALIDATION_ERROR]: {
        title: '输入错误',
        message: '请检查您的输入',
        icon: '⚠️',
        type: 'warning' as const
    },
    [ErrorType.TIMEOUT_ERROR]: {
        title: '请求超时',
        message: '服务器响应超时',
        icon: '⏳',
        type: 'error' as const
    },
    [ErrorType.UNKNOWN_ERROR]: {
        title: '未知错误',
        message: '发生未知错误',
        icon: '❌',
        type: 'error' as const
    }
};

// 错误处理函数
export function handleError(error: any, type: ErrorType = ErrorType.UNKNOWN_ERROR) {
    const config = ERROR_CONFIG[type];

    // 记录错误
    console.error(`${config.icon} ${config.title}:`, error);

    // 显示错误提示
    toast[config.type](`${config.icon} ${config.title}: ${config.message}`, {
        position: 'top-right',
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true
    });

    // 返回错误信息
    return {
        type,
        title: config.title,
        message: config.message,
        error
    };
}

// API错误处理
export async function handleApiError(response: Response) {
    try {
        const data = await response.json();
        return handleError(data, ErrorType.API_ERROR);
    } catch (error) {
        return handleError(error, ErrorType.UNKNOWN_ERROR);
    }
}

// 网络错误处理
export function handleNetworkError(error: Error) {
    return handleError(error, ErrorType.NETWORK_ERROR);
}

// 验证错误处理
export function handleValidationError(error: any) {
    return handleError(error, ErrorType.VALIDATION_ERROR);
}

// 超时错误处理
export function handleTimeoutError(error: Error) {
    return handleError(error, ErrorType.TIMEOUT_ERROR);
}

// 错误边界组件
export class ErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { hasError: boolean; error: Error | null }
> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        handleError(error, ErrorType.UNKNOWN_ERROR);
        console.error('Error boundary caught error:', errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center space-x-2 text-red-700 mb-2">
                        <span className="text-xl">❌</span>
                        <h3 className="font-medium">出错了</h3>
                    </div>
                    <p className="text-sm text-red-600">
                        {this.state.error?.message || '发生未知错误'}
                    </p>
                    <button
                        onClick={() => this.setState({ hasError: false, error: null })}
                        className="mt-2 px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                    >
                        重试
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

// 错误提示组件
export function ErrorAlert({ error }: { error: any }) {
    const config = ERROR_CONFIG[error.type as ErrorType] || ERROR_CONFIG[ErrorType.UNKNOWN_ERROR];

    return (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg animate-fadeIn">
            <div className="flex items-center space-x-2 text-red-700 mb-2">
                <span className="text-xl">{config.icon}</span>
                <h3 className="font-medium">{config.title}</h3>
            </div>
            <p className="text-sm text-red-600">{error.message || config.message}</p>
        </div>
    );
}

// 加载状态组件
export function LoadingSpinner({ message = '加载中...' }: { message?: string }) {
    return (
        <div className="flex items-center justify-center space-x-2 p-4">
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
            <span className="text-sm text-gray-600">{message}</span>
        </div>
    );
}

// 空状态组件
export function EmptyState({ message = '暂无数据' }: { message?: string }) {
    return (
        <div className="text-center py-8">
            <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                    />
                </svg>
            </div>
            <p className="text-gray-500">{message}</p>
        </div>
    );
}
