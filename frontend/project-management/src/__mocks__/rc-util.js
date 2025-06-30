module.exports = {
    __esModule: true,
    // 模拟 getScrollBarSize 的默认导出
    default: jest.fn(() => 0),
    getScrollBarSize: jest.fn(() => 0),
    getTargetScrollBarSize: jest.fn(() => ({
        width: 0,
        height: 0,
        overflow: false,
    })),
    // 明确模拟 canUseDom，使其始终返回 true
    canUseDom: jest.fn(() => true),
};
