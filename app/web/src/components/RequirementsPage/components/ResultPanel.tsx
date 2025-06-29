import React from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import { useRequirementsContext } from '../RequirementsPageContext';

export function ResultPanel() {
    const {
        completionRate
    } = useRequirementsContext();

    return (
        <div className="bg-gray-900">
            {/* 状态栏 */}
            <div className="border-t border-gray-700 bg-gray-800 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-6">
                        <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-sm text-gray-300">系统运行正常</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <DocumentTextIcon className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-300">
                                分析进度: {completionRate}%
                            </span>
                        </div>
                    </div>
                    <div className="text-sm text-gray-400">
                        <span className="text-xs opacity-60">
                            快捷键: Ctrl+Shift+D 切换调试模式
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
