module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'subject-case': [
      2,
      'always',
      ['lower-case', 'sentence-case', 'start-case'],
    ],
    'type-enum': [
      2,
      'always',
      [
        'fix',
        'feat',
        'BREAKING CHANGE',
        'build',
        'chore',
        'ci',
        'docs',
        'style',
        'refactor',
        'revert',
        'test',
        'optimization',
      ],
    ],
  },
};
