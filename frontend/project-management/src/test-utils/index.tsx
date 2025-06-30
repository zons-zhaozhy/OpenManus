import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { ConfigProvider } from 'antd';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
    route?: string;
    initialEntries?: string[];
}

const renderWithRouter = (
    ui: ReactElement,
    { route = '/', initialEntries = [route], ...options }: CustomRenderOptions = {}
) => {
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
        <ConfigProvider>
            <MemoryRouter initialEntries={initialEntries}>
                <Routes>
                    <Route path={route} element={children} />
                </Routes>
            </MemoryRouter>
        </ConfigProvider>
    );

    return {
        ...render(ui, { wrapper: Wrapper, ...options }),
        user: userEvent.setup(),
    };
};

const createMockFn = <T extends (...args: any[]) => any>(
    implementation?: T
): jest.MockedFn<T> => {
    const mockFn = jest.fn() as jest.MockedFn<T>;
    if (implementation) mockFn.mockImplementation(implementation);
    return mockFn;
};

const waitForPromises = () => new Promise(resolve => setImmediate(resolve));

const submitForm = async (form: HTMLFormElement) => {
    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
    form.dispatchEvent(submitEvent);
    await waitForPromises();
};

export { renderWithRouter as render, createMockFn, waitForPromises, submitForm };
