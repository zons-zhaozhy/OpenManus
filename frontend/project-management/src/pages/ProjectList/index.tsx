import React, { useState } from 'react';
import { Button, Table, Modal, Form, Input, Popconfirm, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

interface Project {
    id: string;
    name: string;
    description: string;
}

const ProjectList: React.FC = () => {
    const [projects, setProjects] = useState<Project[]>([{
        id: '1',
        name: 'OpenManus Core',
        description: '核心系统开发',
    }]);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [editingProject, setEditingProject] = useState<Project | null>(null);
    const [form] = Form.useForm();
    const navigate = useNavigate();

    const handleAddProject = () => {
        setEditingProject(null);
        form.resetFields();
        setIsModalVisible(true);
    };

    const handleEditProject = (project: Project) => {
        setEditingProject(project);
        form.setFieldsValue(project);
        setIsModalVisible(true);
    };

    const handleDeleteProject = (id: string) => {
        setProjects(projects.filter(project => project.id !== id));
        message.success('项目删除成功');
    };

    const handleSaveProject = () => {
        form.validateFields().then(values => {
            if (editingProject) {
                setProjects(projects.map(project =>
                    project.id === editingProject.id ? { ...project, ...values } : project
                ));
                message.success('项目更新成功');
            } else {
                setProjects([
                    ...projects,
                    { id: (projects.length + 1).toString(), ...values }
                ]);
                message.success('项目添加成功');
            }
            setIsModalVisible(false);
        }).catch(info => {
            console.log('Validate Failed:', info);
        });
    };

    const handleViewProject = (id: string) => {
        navigate(`/projects/${id}`);
    };

    const columns = [
        {
            title: '项目名称',
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: '描述',
            dataIndex: 'description',
            key: 'description',
        },
        {
            title: '操作',
            key: 'action',
            render: (_: any, record: Project) => (
                <>
                    <Button
                        icon={<EyeOutlined />}
                        onClick={() => handleViewProject(record.id)}
                        style={{ marginRight: 8 }}
                        data-testid={`view-project-${record.id}`}
                    >
                        查看
                    </Button>
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => handleEditProject(record)}
                        style={{ marginRight: 8 }}
                        data-testid={`edit-project-${record.id}`}
                    >
                        编辑
                    </Button>
                    <Popconfirm
                        title="确定删除此项目吗？"
                        onConfirm={() => handleDeleteProject(record.id)}
                        okText="是"
                        cancelText="否"
                    >
                        <Button
                            icon={<DeleteOutlined />}
                            danger
                            data-testid={`delete-project-${record.id}`}
                        >
                            删除
                        </Button>
                    </Popconfirm>
                </>
            ),
        },
    ];

    return (
        <div>
            <div style={{ marginBottom: 16, textAlign: 'right' }}>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleAddProject}
                    data-testid="add-project"
                >
                    添加项目
                </Button>
            </div>
            <Table columns={columns} dataSource={projects} rowKey="id" />

            <Modal
                title={editingProject ? '编辑项目' : '添加项目'}
                open={isModalVisible}
                onOk={handleSaveProject}
                onCancel={() => setIsModalVisible(false)}
                destroyOnHidden
            >
                <Form form={form} layout="vertical" name="project_form">
                    <Form.Item
                        name="name"
                        label="项目名称"
                        rules={[{ required: true, message: '请输入项目名称！' }]}
                    >
                        <Input />
                    </Form.Item>
                    <Form.Item
                        name="description"
                        label="描述"
                    >
                        <Input.TextArea rows={4} />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default ProjectList;
