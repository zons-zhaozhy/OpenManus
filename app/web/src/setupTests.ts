// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(), // deprecated
        removeListener: jest.fn(), // deprecated
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Mock IntersectionObserver
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null
});
window.IntersectionObserver = mockIntersectionObserver;

// Mock Vite's import.meta.env
const env = {
    VITE_API_BASE_URL: 'http://localhost:8000',
    VITE_WS_BASE_URL: 'ws://localhost:8000',
    MODE: 'test'
};

// @ts-ignore
if (typeof window !== 'undefined') {
    // @ts-ignore
    window.env = env;
}

// @ts-ignore
if (typeof global !== 'undefined') {
    // @ts-ignore
    global.env = env;
}

// Mock import.meta
// @ts-ignore
global.import = {
    meta: {
        env
    }
};
