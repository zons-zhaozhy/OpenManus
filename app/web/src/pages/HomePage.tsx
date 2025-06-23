import React from 'react';
import { Link } from 'react-router-dom';
import {
    SparklesIcon,
    UserGroupIcon,
    DocumentTextIcon,
    RocketLaunchIcon,
    CheckCircleIcon,
    ArrowRightIcon,
    BoltIcon,
    CpuChipIcon,
    ChartBarIcon,
    CodeBracketIcon,
    CogIcon,
    ShieldCheckIcon,
    CloudArrowUpIcon
} from '@heroicons/react/24/outline';

export function HomePage() {
    const services = [
        {
            icon: DocumentTextIcon,
            title: '需求分析',
            description: '智能需求澄清与规格生成',
            color: 'blue',
            status: '已上线'
        },
        {
            icon: CogIcon,
            title: '架构设计',
            description: '系统架构智能设计与优化',
            color: 'green',
            status: '开发中'
        },
        {
            icon: CodeBracketIcon,
            title: '编码实现',
            description: 'AI驱动的代码生成与开发',
            color: 'purple',
            status: '规划中'
        },
        {
            icon: ShieldCheckIcon,
            title: '测试部署',
            description: '自动化测试与智能部署',
            color: 'orange',
            status: '规划中'
        }
    ];

    const agents = [
        { name: '需求澄清师', icon: '🔍', desc: '理解和澄清用户需求' },
        { name: '业务分析师', icon: '📊', desc: '分析业务逻辑和流程' },
        { name: '系统架构师', icon: '🏗️', desc: '设计系统架构方案' },
        { name: '技术文档师', icon: '📝', desc: '编写技术文档规格' },
        { name: '后端开发师', icon: '⚙️', desc: '实现后端业务逻辑' },
        { name: '前端开发师', icon: '🎨', desc: '构建用户界面体验' },
        { name: '测试工程师', icon: '🧪', desc: '保障代码质量安全' },
        { name: '运维工程师', icon: '☁️', desc: '部署和运维管理' }
    ];

    const stats = [
        { label: 'AI智能体', value: '8+', icon: UserGroupIcon },
        { label: '服务模块', value: '4个', icon: CpuChipIcon },
        { label: '自动化率', value: '95%', icon: BoltIcon }
    ];

    return (
        <div className="h-full bg-gray-900 text-white overflow-hidden">
            {/* 背景装饰 */}
            <div className="absolute inset-0">
                <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl"></div>
            </div>

            <div className="relative h-full flex flex-col">
                {/* 主要内容区域 */}
                <div className="flex-1 px-6 py-8">
                    <div className="mx-auto max-w-7xl h-full flex flex-col">
                        {/* 顶部区域：Logo + 标题 + 愿景 */}
                        <div className="flex-none mb-8">
                            <div className="text-center mb-6">
                                {/* Logo和标题 */}
                                <div className="mb-4 flex items-center justify-center space-x-3">
                                    <img
                                        src="/assets/logo.jpg"
                                        alt="OpenManus"
                                        className="h-12 w-12 rounded-lg shadow-lg"
                                    />
                                    <div className="text-left">
                                        <h1 className="text-3xl font-bold text-white">OpenManus</h1>
                                        <p className="text-sm text-blue-400 font-medium">AI驱动的软件公司</p>
                                    </div>
                                </div>

                                {/* 主标语 */}
                                <h2 className="text-xl font-bold text-gray-200 mb-3">
                                    真正的AI软件公司，让智能体接管传统软件开发
                                </h2>

                                <p className="mx-auto max-w-3xl text-base text-gray-300 leading-relaxed mb-4">
                                    从需求分析到系统部署，通过多智能体协作实现软件开发全流程自动化。
                                    当前专注需求分析阶段，未来将覆盖完整软件开发生命周期。
                                </p>

                                {/* CTA按钮 */}
                                <div className="flex flex-col sm:flex-row gap-3 justify-center items-center mb-6">
                                    <Link
                                        to="/requirements"
                                        className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 group"
                                    >
                                        <DocumentTextIcon className="h-4 w-4 mr-2" />
                                        体验需求分析
                                        <ArrowRightIcon className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                                    </Link>
                                    <button className="inline-flex items-center px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white font-semibold rounded-lg transition-all duration-200 border border-gray-600 hover:border-gray-500">
                                        了解愿景
                                    </button>
                                </div>
                            </div>

                            {/* 统计数据 */}
                            <div className="grid grid-cols-3 gap-4">
                                {stats.map((stat, index) => (
                                    <div key={index} className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
                                        <div className="flex items-center justify-center mb-2">
                                            <stat.icon className="h-6 w-6 text-blue-400" />
                                        </div>
                                        <div className="text-2xl font-bold text-white mb-1 text-center">{stat.value}</div>
                                        <div className="text-xs text-gray-300 text-center">{stat.label}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* 核心内容区域 */}
                        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* 左侧：AI软件公司服务 */}
                            <div className="flex flex-col">
                                <div className="mb-4">
                                    <h3 className="text-xl font-bold text-white mb-2">AI软件公司服务</h3>
                                    <p className="text-gray-400 text-sm">完整的软件开发生命周期智能化</p>
                                </div>

                                <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {services.map((service, index) => (
                                        <div
                                            key={index}
                                            className="group bg-gray-800 rounded-lg p-5 border border-gray-700 hover:border-gray-600 transition-all duration-300 hover:transform hover:-translate-y-1 hover:shadow-lg"
                                        >
                                            <div className="flex items-center space-x-3 mb-3">
                                                <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg bg-${service.color}-600/20 group-hover:scale-110 transition-transform duration-300`}>
                                                    <service.icon className={`h-5 w-5 text-${service.color}-400`} />
                                                </div>
                                                <div className="flex-1">
                                                    <h4 className="text-base font-bold text-white">{service.title}</h4>
                                                    <span className={`text-xs px-2 py-1 rounded-full ${service.status === '已上线'
                                                        ? 'bg-green-600/20 text-green-400'
                                                        : service.status === '开发中'
                                                            ? 'bg-yellow-600/20 text-yellow-400'
                                                            : 'bg-gray-600/20 text-gray-400'
                                                        }`}>
                                                        {service.status}
                                                    </span>
                                                </div>
                                            </div>
                                            <p className="text-gray-300 text-sm leading-relaxed">
                                                {service.description}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* 右侧：智能体团队 */}
                            <div className="flex flex-col">
                                <div className="mb-4">
                                    <h3 className="text-xl font-bold text-white mb-2">智能体团队</h3>
                                    <p className="text-gray-400 text-sm">专业AI智能体协作完成软件开发</p>
                                </div>

                                <div className="flex-1">
                                    <div className="grid grid-cols-2 gap-3">
                                        {agents.map((agent, index) => (
                                            <div
                                                key={index}
                                                className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-all duration-200 hover:bg-gray-750"
                                            >
                                                <div className="flex items-center space-x-3">
                                                    <span className="text-2xl">{agent.icon}</span>
                                                    <div>
                                                        <div className="text-sm font-semibold text-white">{agent.name}</div>
                                                        <div className="text-xs text-gray-400">{agent.desc}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 底部行动区域 */}
                        <div className="flex-none mt-8">
                            <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                                    <div>
                                        <h3 className="text-lg font-bold text-white mb-2">开启AI软件公司之旅</h3>
                                        <p className="text-gray-400 text-sm mb-4">
                                            当前第一期专注需求分析，体验智能体协作的强大能力
                                        </p>
                                        <div className="flex space-x-3">
                                            <Link
                                                to="/requirements"
                                                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 group text-sm"
                                            >
                                                <SparklesIcon className="h-4 w-4 mr-2" />
                                                开始需求分析
                                                <ArrowRightIcon className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                                            </Link>
                                        </div>
                                    </div>

                                    <div className="text-right text-sm text-gray-400">
                                        <div className="space-y-1">
                                            <div>✅ 第一期：需求分析智能体 (当前)</div>
                                            <div>🚧 第二期：系统架构设计智能体</div>
                                            <div>📋 第三期：编码实现智能体</div>
                                            <div>🔮 终极期：完整AI软件公司生态</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
