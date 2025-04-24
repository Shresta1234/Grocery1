module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.js'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': '<rootDir>/tests/frontend/__mocks__/styleMock.js',
  },
  testMatch: [
    '<rootDir>/tests/frontend/**/*.test.js'
  ],
  collectCoverageFrom: [
    'static/js/**/*.js'
  ]
}; 