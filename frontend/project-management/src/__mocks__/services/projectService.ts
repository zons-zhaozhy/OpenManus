export const getProjects = jest.fn().mockResolvedValue([
    {
        id: '1',
        name: 'OpenManus Core',
        description: '核心系统开发',
        createdAt: '2023-01-01T10:00:00Z',
        updatedAt: '2023-01-01T10:00:00Z'
    }
]);

export const getProject = jest.fn().mockResolvedValue({
    id: '1',
    name: '项目 1 名称',
    description: '这是项目 1 的详细描述信息。',
    status: '进行中',
    createdAt: '2025-06-01',
    updatedAt: '2025-06-29'
});

export const createProject = jest.fn().mockImplementation(async (project) => ({
    id: 'mock-id-new',
    ...project,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
}));

export const updateProject = jest.fn().mockImplementation(async (id, project) => ({
    id,
    ...project,
    updatedAt: new Date().toISOString()
}));

export const deleteProject = jest.fn().mockResolvedValue(true);
