import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
    CogIcon,
    CircleStackIcon as DatabaseIcon,
    CodeBracketIcon,
    KeyIcon,
    CloudIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon,
    PlusIcon,
    TrashIcon,
    PencilIcon,
    DocumentTextIcon,
    FolderOpenIcon
} from '@heroicons/react/24/outline';

interface LLMConfig {
    model: string;
    base_url: string;
    api_key: string;
    max_tokens: number;
    temperature: number;
    api_type: string;
}

interface KnowledgeBase {
    id: string;
    name: string;
    description: string;
    type: string;
    status: 'active' | 'inactive';
}

interface Codebase {
    id: string;
    name: string;
    description: string;
    local_path: string;
    main_language: string;
    last_analyzed_at?: string;
}

export function SettingsPage() {
    const [activeTab, setActiveTab] = useState('llm');
    const [showApiKeyForm, setShowApiKeyForm] = useState(false);
    const [llmConfig, setLlmConfig] = useState<LLMConfig>({
        model: 'deepseek/deepseek-v3-0324',
        base_url: 'https://api.ppinfra.com/v3/openai',
        api_key: '',
        max_tokens: 16000,
        temperature: 0.0,
        api_type: 'ppio'
    });

    // Mock data - 在实际项目中应该从API获取
    const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([
        {
            id: '1',
            name: '软件需求分析知识库',
            description: '包含软件工程需求分析的最佳实践和模板',
            type: 'requirements_templates',
            status: 'active'
        },
        {
            id: '2',
            name: '技术架构模式库',
            description: '常见的软件架构模式和设计模式',
            type: 'architecture_patterns',
            status: 'active'
        }
    ]);

    const [codebases, setCodebases] = useState<Codebase[]>([
        {
            id: '1',
            name: 'OpenManus',
            description: 'AI驱动的软件公司平台',
            local_path: '/Users/stan/code/ai/github/fock/OpenManus',
            main_language: 'Python',
            last_analyzed_at: '2025-06-23T19:25:04.723554'
        }
    ]);

    const tabs = [
        {
            id: 'llm',
            name: 'LLM配置',
            icon: CloudIcon,
            description: '配置大语言模型API'
        },
        {
            id: 'knowledge',
            name: '知识库',
            icon: DatabaseIcon,
            description: '管理知识库资源'
        },
        {
            id: 'codebase',
            name: '代码库',
            icon: CodeBracketIcon,
            description: '管理项目代码库'
        }
    ];

    const handleSaveLLMConfig = async () => {
        // TODO: 实现保存LLM配置的API调用
        console.log('保存LLM配置:', llmConfig);
    };

    const testLLMConnection = async () => {
        // TODO: 实现测试LLM连接的API调用
        console.log('测试LLM连接');
    };

    const renderLLMSettings = () => (
        <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-xl font-semibold text-white">DeepSeek配置</h3>
                        <p className="text-gray-400 mt-1">配置DeepSeek AI模型的连接参数</p>
                    </div>
                    <div className="flex items-center space-x-2">
                        {llmConfig.api_key ? (
                            <CheckCircleIcon className="h-5 w-5 text-green-500" />
                        ) : (
                            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
                        )}
                        <span className="text-sm text-gray-300">
                            {llmConfig.api_key ? '已配置' : '未配置'}
                        </span>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            模型名称
                        </label>
                        <input
                            type="text"
                            value={llmConfig.model}
                            onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
                            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            API类型
                        </label>
                        <select
                            value={llmConfig.api_type}
                            onChange={(e) => setLlmConfig({ ...llmConfig, api_type: e.target.value })}
                            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                        >
                            <option value="ppio">PPIO</option>
                            <option value="openai">OpenAI</option>
                            <option value="azure">Azure OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            API端点
                        </label>
                        <input
                            type="text"
                            value={llmConfig.base_url}
                            onChange={(e) => setLlmConfig({ ...llmConfig, base_url: e.target.value })}
                            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            最大Token数
                        </label>
                        <input
                            type="number"
                            value={llmConfig.max_tokens}
                            onChange={(e) => setLlmConfig({ ...llmConfig, max_tokens: parseInt(e.target.value) })}
                            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                        />
                    </div>

                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            API密钥
                        </label>
                        <div className="flex space-x-2">
                            <input
                                type={showApiKeyForm ? "text" : "password"}
                                value={llmConfig.api_key}
                                onChange={(e) => setLlmConfig({ ...llmConfig, api_key: e.target.value })}
                                placeholder="请输入API密钥"
                                className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                            />
                            <button
                                onClick={() => setShowApiKeyForm(!showApiKeyForm)}
                                className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500"
                            >
                                <KeyIcon className="h-4 w-4" />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="flex space-x-3 mt-6">
                    <button
                        onClick={handleSaveLLMConfig}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
                    >
                        保存配置
                    </button>
                    <button
                        onClick={testLLMConnection}
                        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
                    >
                        测试连接
                    </button>
                </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">并行处理优化</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-700 rounded-lg p-4">
                        <h4 className="font-medium text-white mb-2">智能体并行协作</h4>
                        <p className="text-sm text-gray-300">启用多智能体并行处理，减少用户等待时间</p>
                        <div className="mt-3">
                            <label className="flex items-center">
                                <input type="checkbox" className="mr-2" defaultChecked />
                                <span className="text-sm text-gray-300">启用并行处理</span>
                            </label>
                        </div>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4">
                        <h4 className="font-medium text-white mb-2">请求优化</h4>
                        <p className="text-sm text-gray-300">优化LLM请求策略，提升响应速度</p>
                        <div className="mt-3">
                            <label className="flex items-center">
                                <input type="checkbox" className="mr-2" defaultChecked />
                                <span className="text-sm text-gray-300">启用流式响应</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderKnowledgeBaseSettings = () => (
        <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-xl font-semibold text-white">知识库管理</h3>
                        <p className="text-gray-400 mt-1">管理项目知识库和模板资源</p>
                    </div>
                    <div className="flex space-x-3">
                        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2">
                            <PlusIcon className="h-4 w-4" />
                            <span>添加知识库</span>
                        </button>
                        <label className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2 cursor-pointer">
                            <DocumentTextIcon className="h-4 w-4" />
                            <span>上传文档</span>
                            <input
                                type="file"
                                multiple
                                accept=".pdf,.doc,.docx,.txt,.md,.json,.xml,.yaml,.yml"
                                className="hidden"
                                onChange={(e) => {
                                    // TODO: 处理文档上传
                                    console.log('上传的文件:', e.target.files);
                                }}
                            />
                        </label>
                    </div>
                </div>

                <div className="space-y-4">
                    {knowledgeBases.map((kb) => (
                        <div key={kb.id} className="bg-gray-700 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center space-x-3">
                                        <DatabaseIcon className="h-5 w-5 text-blue-400" />
                                        <div>
                                            <h4 className="font-medium text-white">{kb.name}</h4>
                                            <p className="text-sm text-gray-300">{kb.description}</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${kb.status === 'active'
                                        ? 'bg-green-600 text-green-100'
                                        : 'bg-gray-600 text-gray-300'
                                        }`}>
                                        {kb.status === 'active' ? '启用' : '禁用'}
                                    </span>
                                    <button className="text-gray-400 hover:text-white">
                                        <PencilIcon className="h-4 w-4" />
                                    </button>
                                    <button className="text-gray-400 hover:text-red-400">
                                        <TrashIcon className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderCodebaseSettings = () => (
        <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-xl font-semibold text-white">代码库管理</h3>
                        <p className="text-gray-400 mt-1">管理项目代码库和分析配置</p>
                    </div>
                    <div className="flex space-x-3">
                        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2">
                            <PlusIcon className="h-4 w-4" />
                            <span>添加代码库</span>
                        </button>
                        <label className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2 cursor-pointer">
                            <FolderOpenIcon className="h-4 w-4" />
                            <span>选择目录</span>
                            <input
                                type="file"
                                {...({ webkitdirectory: "" } as any)}
                                className="hidden"
                                onChange={(e) => {
                                    // TODO: 处理目录选择和自动分析
                                    console.log('选择的目录:', e.target.files);
                                }}
                            />
                        </label>
                    </div>
                </div>

                <div className="space-y-4">
                    {codebases.map((codebase) => (
                        <div key={codebase.id} className="bg-gray-700 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center space-x-3">
                                        <CodeBracketIcon className="h-5 w-5 text-green-400" />
                                        <div>
                                            <h4 className="font-medium text-white">{codebase.name}</h4>
                                            <p className="text-sm text-gray-300">{codebase.description}</p>
                                            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
                                                <span>语言: {codebase.main_language}</span>
                                                <span>路径: {codebase.local_path}</span>
                                                {codebase.last_analyzed_at && (
                                                    <span>最后分析: {new Date(codebase.last_analyzed_at).toLocaleDateString()}</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                                        重新分析
                                    </button>
                                    <button className="text-gray-400 hover:text-white">
                                        <PencilIcon className="h-4 w-4" />
                                    </button>
                                    <button className="text-gray-400 hover:text-red-400">
                                        <TrashIcon className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    return (
        <div className="h-full bg-gray-900 text-white flex">
            {/* 左侧导航 */}
            <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
                <div className="p-6 border-b border-gray-700">
                    <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                        <CogIcon className="h-6 w-6" />
                        <span>系统设置</span>
                    </h2>
                </div>

                <nav className="flex-1 p-4">
                    <div className="space-y-2">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${activeTab === tab.id
                                    ? 'bg-blue-600 text-white'
                                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                                    }`}
                            >
                                <div className="flex items-center space-x-3">
                                    <tab.icon className="h-5 w-5" />
                                    <div>
                                        <div className="font-medium">{tab.name}</div>
                                        <div className="text-xs opacity-75">{tab.description}</div>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </nav>
            </div>

            {/* 右侧内容区域 */}
            <div className="flex-1 overflow-y-auto">
                <div className="p-6">
                    {activeTab === 'llm' && renderLLMSettings()}
                    {activeTab === 'knowledge' && renderKnowledgeBaseSettings()}
                    {activeTab === 'codebase' && renderCodebaseSettings()}
                </div>
            </div>
        </div>
    );
}
