import { test, expect } from '@playwright/test';

test.describe('Project List Page', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to the project list page
        await page.goto('http://localhost:3000'); // Assuming your React app runs on port 3000
    });

    test('should display project list', async ({ page }) => {
        // Expect a title "项目管理"
        await expect(page.locator('h1')).toHaveText('项目管理'); // Assuming the page has an h1 with this title

        // Expect existing projects to be visible
        await expect(page.getByText('OpenManus Core')).toBeVisible();
        await expect(page.getByText('核心系统开发')).toBeVisible();
        await expect(page.getByText('AI Agent')).toBeVisible();
        await expect(page.getByText('AI Agent 研发')).toBeVisible();
    });

    test('should add a new project', async ({ page }) => {
        // Click the "添加项目" button
        await page.getByTestId('add-project').click();

        // Fill the form
        await page.getByLabel('项目名称').fill('E2E Test Project');
        await page.getByLabel('描述').fill('This project was added via E2E test');

        // Click the "确定" button in the modal
        await page.getByRole('button', { name: '确定' }).click();

        // Expect the new project to be visible in the list
        await expect(page.getByText('E2E Test Project')).toBeVisible();
        await expect(page.getByText('This project was added via E2E test')).toBeVisible();
    });

    test('should edit an existing project', async ({ page }) => {
        // Expect existing project to be visible
        await expect(page.getByText('OpenManus Core')).toBeVisible();

        // Click the edit button for 'OpenManus Core'
        await page.getByTestId('edit-project-1').click();

        // Fill the form
        await page.getByLabel('项目名称').fill('OpenManus Core E2E Edited');
        await page.getByLabel('描述').fill('E2E Edited Description');

        // Click the "确定" button in the modal
        await page.getByRole('button', { name: '确定' }).click();

        // Expect the edited project name to be visible
        await expect(page.getByText('OpenManus Core E2E Edited')).toBeVisible();
        await expect(page.getByText('E2E Edited Description')).toBeVisible();
    });

    test('should delete a project', async ({ page }) => {
        // Expect existing project to be visible
        await expect(page.getByText('AI Agent')).toBeVisible();

        // Click the delete button for 'AI Agent'
        await page.getByTestId('delete-project-2').click();

        // Confirm deletion in the Popconfirm
        await page.getByRole('button', { name: '是' }).click();

        // Expect the project to be removed from the list
        await expect(page.getByText('AI Agent')).not.toBeVisible();
    });

    test('should navigate to project detail', async ({ page }) => {
        // Expect existing project to be visible
        await expect(page.getByText('OpenManus Core')).toBeVisible();

        // Click the view button for 'OpenManus Core'
        await page.getByTestId('view-project-1').click();

        // Expect to be on the project detail page
        await expect(page).toHaveURL('http://localhost:3000/projects/1');
    });
});
