// Mock API module
export const requirementsApi = {
    sendMessage: jest.fn(),
    getMessages: jest.fn(),
    getClarificationQuestions: jest.fn(),
    answerClarificationQuestion: jest.fn(),
    getRequirementsSummary: jest.fn(),
    getRequirementsDocument: jest.fn(),
    getRequirementsStatus: jest.fn(),
    clearRequirements: jest.fn(),
};
