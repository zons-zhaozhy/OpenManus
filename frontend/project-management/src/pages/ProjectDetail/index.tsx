import React from 'react';
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const ProjectDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    // 实际项目中这里会根据id从后端获取项目详细信息
    const project = {
        id: id,
        name: `项目 ${id} 名称`,
        description: `这是项目 ${id} 的详细描述信息。`,
        status: '进行中',
        createdAt: '2025-06-01',
        lastUpdated: '2025-06-29',
    };

    const handleBack = () => {
        navigate('/');
    };

    return (
        <Card
            title={
                <>
                    <Button
                        type="text"
                        icon={<ArrowLeftOutlined />}
                        onClick={handleBack}
                        style={{ marginRight: 8 }}
                    />
                    项目详情: {project.name}
                </>
            }
            style={{ marginBottom: 24 }}
        >
            <Descriptions bordered column={1}>
                <Descriptions.Item label="项目ID">{project.id}</Descriptions.Item>
                <Descriptions.Item label="项目名称">{project.name}</Descriptions.Item>
                <Descriptions.Item label="描述">{project.description}</Descriptions.Item>
                <Descriptions.Item label="状态">{project.status}</Descriptions.Item>
                <Descriptions.Item label="创建日期">{project.createdAt}</Descriptions.Item>
                <Descriptions.Item label="最后更新">{project.lastUpdated}</Descriptions.Item>
            </Descriptions>
        </Card>
    );
};

export default ProjectDetail;
