export interface Project {
    id: string;
    name: string;
    description: string;
    createdAt: string;
    updatedAt: string;
}

export const getProjects = async (): Promise<Project[]> => {
    console.log('Mocking getProjects');
    return [];
};

export const createProject = async (project: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>): Promise<Project> => {
    console.log('Mocking createProject', project);
    return { id: 'mock-id', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), ...project };
};

export const updateProject = async (id: string, project: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>): Promise<Project> => {
    console.log('Mocking updateProject', id, project);
    return { id, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), ...project };
};

export const deleteProject = async (id: string): Promise<boolean> => {
    console.log('Mocking deleteProject', id);
    return true;
};
