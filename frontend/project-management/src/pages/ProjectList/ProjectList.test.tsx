import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProjectList from './index';

describe('ProjectList', () => {
    it('should render initial project', async () => {
        render(<ProjectList />);

        await waitFor(() => {
            expect(screen.getByText('OpenManus Core')).toBeInTheDocument();
            expect(screen.getByText('核心系统开发')).toBeInTheDocument();
        });
    });

    it('should show add project modal when click add button', async () => {
        render(<ProjectList />);

        const addButton = screen.getByTestId('add-project');
        await userEvent.click(addButton);

        expect(screen.getByText('添加项目')).toBeInTheDocument();
        expect(screen.getByLabelText('项目名称')).toBeInTheDocument();
        expect(screen.getByLabelText('描述')).toBeInTheDocument();
    });

    it('should show edit project modal when click edit button', async () => {
        render(<ProjectList />);

        await waitFor(() => {
            expect(screen.getByText('OpenManus Core')).toBeInTheDocument();
        });

        const editButton = screen.getByTestId('edit-project-1');
        await userEvent.click(editButton);

        expect(screen.getByText('编辑项目')).toBeInTheDocument();
        expect(screen.getByDisplayValue('OpenManus Core')).toBeInTheDocument();
        expect(screen.getByDisplayValue('核心系统开发')).toBeInTheDocument();
    });
});
