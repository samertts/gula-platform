module.exports = {
  preset: 'jest-expo',
  testMatch: ['**/__tests__/**/*.test.ts'],
  clearMocks: true,
  restoreMocks: true,
  moduleNameMapper: {
    '^expo-modules-core(|/.*)$': '<rootDir>/node_modules/expo-modules-core$1',
  },
};
