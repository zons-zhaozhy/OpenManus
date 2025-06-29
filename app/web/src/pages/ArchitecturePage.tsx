import React, { useState, useEffect } from 'react';

interface ProjectConstraints {
    budget?: string;
    timeline?: string;
    team_size?: string;
    technology_constraints?: string;
    deployment_environment?: string;
}

interface RequirementsSession {
    session_id: string;
    created_at: string;
    status: string;
    quality_score?: number;
}

export const ArchitecturePage: React.FC = () => {
    const [requirements, setRequirements] = useState('');
    const [sessionId, setSessionId] = useState('');
    const [importSessionId, setImportSessionId] = useState('');
    const [projectConstraints, setProjectConstraints] = useState<ProjectConstraints>({});
    const [result, setResult] = useState('');
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'manual' | 'import'>('import');
    const [availableSessions, setAvailableSessions] = useState<RequirementsSession[]>([]);
    const [showConstraints, setShowConstraints] = useState(false);

    // 组件挂载时获取可用的需求分析会话
    useEffect(() => {
        fetchAvailableRequirementsSessions();
    }, []);

    const fetchAvailableRequirementsSessions = async () => {
        try {
            // 这里应该调用第一期的API获取可用会话
            // 暂时使用模拟数据
            const mockSessions: RequirementsSession[] = [
                {
                    session_id: 'req-001',
                    created_at: '2024-12-16 10:00:00',
                    status: 'completed',
                    quality_score: 0.85
                },
                {
                    session_id: 'req-002',
                    created_at: '2024-12-16 11:30:00',
                    status: 'completed',
                    quality_score: 0.78
                },
                {
                    session_id: 'req-003',
                    created_at: '2024-12-16 14:15:00',
                    status: 'completed',
                    quality_score: 0.92
                }
            ];
            setAvailableSessions(mockSessions);
        } catch (error) {
            console.error('获取需求分析会话失败:', error);
        }
    };

    const handleImportFromRequirements = async () => {
        if (!importSessionId) {
            alert('请选择需求分析会话');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/api/architecture/import-from-requirements', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    requirements_session_id: importSessionId,
                    project_constraints: Object.keys(projectConstraints).length > 0 ? projectConstraints : null
                }),
            });

            const data = await response.json();

            if (data.status === 'completed') {
                setSessionId(data.session_id);
                setResult(data.result);
                setProgress(data.progress);
                alert('🎉 架构设计完成！已从需求分析成功导入并完成设计。');
            } else if (data.status === 'error') {
                alert(`❌ 导入失败: ${data.error}`);
            }
        } catch (error) {
            console.error('导入需求失败:', error);
            alert('❌ 导入需求失败，请检查网络连接');
        } finally {
            setLoading(false);
        }
    };

    const handleManualDesign = async () => {
        if (!requirements.trim()) {
            alert('请输入需求文档');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/api/architecture/design', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    requirements_doc: requirements,
                    project_constraints: Object.keys(projectConstraints).length > 0 ? projectConstraints : null
                }),
            });

            const data = await response.json();

            if (data.status === 'completed') {
                setSessionId(data.session_id);
                setResult(data.result);
                setProgress(data.progress);
                alert('🎉 架构设计完成！');
            } else if (data.status === 'error') {
                alert(`❌ 设计失败: ${data.error}`);
            }
        } catch (error) {
            console.error('架构设计失败:', error);
            alert('❌ 架构设计失败，请检查网络连接');
        } finally {
            setLoading(false);
        }
    };

    const renderConstraintsForm = () => (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-blue-800">📋 项目约束条件 (可选)</h4>
                <button
                    onClick={() => setShowConstraints(!showConstraints)}
                    className="text-blue-600 text-sm hover:text-blue-800"
                >
                    {showConstraints ? '收起' : '展开'}
                </button>
            </div>

            {showConstraints && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">预算限制</label>
                        <input
                            type="text"
                            value={projectConstraints.budget || ''}
                            onChange={(e) => setProjectConstraints({ ...projectConstraints, budget: e.target.value })}
                            placeholder="如：100万元"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">时间限制</label>
                        <input
                            type="text"
                            value={projectConstraints.timeline || ''}
                            onChange={(e) => setProjectConstraints({ ...projectConstraints, timeline: e.target.value })}
                            placeholder="如：6个月"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">团队规模</label>
                        <input
                            type="text"
                            value={projectConstraints.team_size || ''}
                            onChange={(e) => setProjectConstraints({ ...projectConstraints, team_size: e.target.value })}
                            placeholder="如：5-8人"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">部署环境</label>
                        <input
                            type="text"
                            value={projectConstraints.deployment_environment || ''}
                            onChange={(e) => setProjectConstraints({ ...projectConstraints, deployment_environment: e.target.value })}
                            placeholder="如：阿里云、私有云"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                    </div>

                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">技术约束</label>
                        <textarea
                            value={projectConstraints.technology_constraints || ''}
                            onChange={(e) => setProjectConstraints({ ...projectConstraints, technology_constraints: e.target.value })}
                            placeholder="如：必须使用Java、不能使用某些开源组件等"
                            rows={2}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                    </div>
                </div>
            )}
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto p-6">
            <div className="bg-white rounded-lg shadow-lg">
                {/* 头部 */}
                <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-lg">
                    <h1 className="text-2xl font-bold flex items-center">
                        🏗️ 系统架构设计助手
                    </h1>
                    <p className="text-purple-100 mt-2">智能化系统架构设计，支持从需求分析直接导入</p>
                </div>

                <div className="p-6">
                    {/* 标签页切换 */}
                    <div className="border-b border-gray-200 mb-6">
                        <nav className="-mb-px flex space-x-8">
                            <button
                                onClick={() => setActiveTab('import')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'import'
                                        ? 'border-purple-500 text-purple-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                📥 从需求分析导入
                            </button>
                            <button
                                onClick={() => setActiveTab('manual')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'manual'
                                        ? 'border-purple-500 text-purple-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                ✏️ 手动输入需求
                            </button>
                        </nav>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* 左侧：输入区域 */}
                        <div className="lg:col-span-1 space-y-4">
                            {activeTab === 'import' ? (
                                <>
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-800 mb-3">
                                            📋 选择需求分析会话
                                        </h3>

                                        {/* 会话选择 */}
                                        <div className="space-y-2">
                                            {availableSessions.length > 0 ? (
                                                availableSessions.map((session) => (
                                                    <div
                                                        key={session.session_id}
                                                        className={`p-3 border rounded-lg cursor-pointer transition-all ${importSessionId === session.session_id
                                                                ? 'border-purple-500 bg-purple-50'
                                                                : 'border-gray-200 hover:border-gray-300'
                                                            }`}
                                                        onClick={() => setImportSessionId(session.session_id)}
                                                    >
                                                        <div className="flex items-center justify-between">
                                                            <div>
                                                                <div className="font-medium text-sm text-gray-800">
                                                                    {session.session_id}
                                                                </div>
                                                                <div className="text-xs text-gray-500">
                                                                    {session.created_at}
                                                                </div>
                                                            </div>
                                                            <div className="text-right">
                                                                <div className={`text-xs px-2 py-1 rounded-full ${session.quality_score && session.quality_score >= 0.8
                                                                        ? 'bg-green-100 text-green-800'
                                                                        : 'bg-yellow-100 text-yellow-800'
                                                                    }`}>
                                                                    {session.quality_score ? `${(session.quality_score * 100).toFixed(0)}%` : 'N/A'}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="text-center py-8 text-gray-500">
                                                    <p>暂无可用的需求分析会话</p>
                                                    <p className="text-sm mt-1">请先完成需求分析</p>
                                                </div>
                                            )}
                                        </div>

                                        {/* 刷新按钮 */}
                                        <button
                                            onClick={fetchAvailableRequirementsSessions}
                                            className="w-full mt-3 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm"
                                        >
                                            🔄 刷新会话列表
                                        </button>
                                    </div>

                                    {/* 项目约束 */}
                                    {renderConstraintsForm()}

                                    {/* 导入按钮 */}
                                    <button
                                        onClick={handleImportFromRequirements}
                                        disabled={loading || !importSessionId}
                                        className={`w-full py-3 px-4 rounded-md font-medium ${loading || !importSessionId
                                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                                : 'bg-purple-600 text-white hover:bg-purple-700'
                                            } transition-colors`}
                                    >
                                        {loading ? '🔄 导入并设计中...' : '🚀 导入并开始设计'}
                                    </button>
                                </>
                            ) : (
                                <>
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-800 mb-3">
                                            📝 输入需求文档
                                        </h3>
                                        <textarea
                                            value={requirements}
                                            onChange={(e) => setRequirements(e.target.value)}
                                            placeholder="请输入完整的需求文档..."
                                            rows={12}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                        />
                                    </div>

                                    {/* 项目约束 */}
                                    {renderConstraintsForm()}

                                    {/* 设计按钮 */}
                                    <button
                                        onClick={handleManualDesign}
                                        disabled={loading || !requirements.trim()}
                                        className={`w-full py-3 px-4 rounded-md font-medium ${loading || !requirements.trim()
                                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                                : 'bg-purple-600 text-white hover:bg-purple-700'
                                            } transition-colors`}
                                    >
                                        {loading ? '🔄 设计中...' : '🚀 开始架构设计'}
                                    </button>
                                </>
                            )}
                        </div>

                        {/* 中间：进度显示 */}
                        <div className="lg:col-span-1">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4">⚡ 设计进度</h3>

                            {loading ? (
                                <div className="space-y-4">
                                    <div className="bg-blue-50 p-4 rounded-lg">
                                        <div className="flex items-center space-x-3">
                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                            <span className="text-blue-800 font-medium">正在执行架构设计...</span>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        {['技术选型分析', '系统架构设计', '数据库设计', '架构质量评审'].map((step, index) => (
                                            <div key={step} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                                                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${index === 0 ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
                                                    }`}>
                                                    {index + 1}
                                                </div>
                                                <span className={index === 0 ? 'text-blue-800 font-medium' : 'text-gray-600'}>
                                                    {step}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : progress ? (
                                <div className="space-y-4">
                                    <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center">
                                                <span className="text-white text-xs">✓</span>
                                            </div>
                                            <span className="text-green-800 font-medium">架构设计已完成</span>
                                        </div>
                                    </div>

                                    {sessionId && (
                                        <div className="text-sm text-gray-600">
                                            <p><strong>会话ID:</strong> {sessionId}</p>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-gray-500">
                                    <p>请选择输入方式并开始设计</p>
                                    <p className="text-sm mt-1">系统将自动显示进度</p>
                                </div>
                            )}
                        </div>

                        {/* 右侧：结果展示 */}
                        <div className="lg:col-span-1">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4">📊 设计结果</h3>

                            {result ? (
                                <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                                    <pre className="text-sm text-gray-800 whitespace-pre-wrap">{result}</pre>
                                </div>
                            ) : (
                                <div className="bg-gray-50 p-8 rounded-lg text-center text-gray-500">
                                    <p>架构设计结果将在这里显示</p>
                                    <p className="text-sm mt-1">包括技术选型、系统架构、数据库设计等</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 底部操作区 */}
                    {result && (
                        <div className="mt-6 pt-6 border-t border-gray-200">
                            <div className="flex justify-between items-center">
                                <div className="text-sm text-gray-600">
                                    <p>✅ 架构设计完成，可以进行下一步开发</p>
                                </div>
                                <div className="space-x-3">
                                    <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                                        📄 导出设计文档
                                    </button>
                                    <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
                                        🚀 开始开发阶段
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
