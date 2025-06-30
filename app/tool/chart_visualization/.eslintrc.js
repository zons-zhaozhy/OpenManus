module.exports = {
    root: true,
    parser: '@typescript-eslint/parser',
    plugins: [
        '@typescript-eslint',
        'jest'
    ],
    extends: [
        'eslint:recommended',
        'plugin:@typescript-eslint/recommended',
        'plugin:jest/recommended',
        'prettier'
    ],
    env: {
        browser: true,
        es2021: true,
        node: true,
        jest: true
    },
    rules: {
        // TypeScript specific rules
        '@typescript-eslint/explicit-function-return-type': 'error',
        '@typescript-eslint/no-explicit-any': 'error',
        '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
        '@typescript-eslint/no-non-null-assertion': 'error',
        '@typescript-eslint/no-empty-interface': 'error',
        '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
        '@typescript-eslint/prefer-interface': 'off',
        '@typescript-eslint/no-namespace': 'error',
        '@typescript-eslint/ban-types': 'error',

        // Jest specific rules
        'jest/no-disabled-tests': 'warn',
        'jest/no-focused-tests': 'error',
        'jest/no-identical-title': 'error',
        'jest/prefer-to-have-length': 'warn',
        'jest/valid-expect': 'error',

        // General rules
        'no-console': ['warn', { allow: ['warn', 'error'] }],
        'no-debugger': 'error',
        'no-alert': 'error',
        'no-var': 'error',
        'prefer-const': 'error',
        'prefer-template': 'error',
        'prefer-rest-params': 'error',
        'prefer-spread': 'error',
        'prefer-arrow-callback': 'error',
        'arrow-body-style': ['error', 'as-needed'],
        'no-duplicate-imports': 'error',
        'sort-imports': ['error', {
            ignoreCase: true,
            ignoreDeclarationSort: true,
            ignoreMemberSort: false,
            memberSyntaxSortOrder: ['none', 'all', 'multiple', 'single']
        }],
        'object-shorthand': ['error', 'always'],
        'eqeqeq': ['error', 'always'],
        'no-eval': 'error',
        'no-implied-eval': 'error',
        'no-new-func': 'error',
        'no-param-reassign': 'error',
        'no-return-assign': ['error', 'always'],
        'no-sequences': 'error',
        'no-throw-literal': 'error',
        'no-unused-expressions': 'error',
        'no-useless-call': 'error',
        'no-useless-concat': 'error',
        'no-useless-return': 'error',
        'prefer-promise-reject-errors': 'error',
        'radix': 'error',
        'wrap-iife': ['error', 'outside'],
        'yoda': 'error'
    },
    settings: {
        'import/resolver': {
            typescript: {}
        }
    },
    overrides: [
        {
            files: ['*.test.ts', '*.spec.ts'],
            rules: {
                '@typescript-eslint/no-explicit-any': 'off',
                'no-unused-expressions': 'off'
            }
        }
    ]
};
