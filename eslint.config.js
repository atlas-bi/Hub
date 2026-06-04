const { defineConfig, globalIgnores } = require("eslint/config");
const js = require("@eslint/js");
const globals = require("globals");

module.exports = defineConfig([
  globalIgnores([
    "node_modules/**",
    ".mypy_cache/**",
    ".pytest_cache/**",
    ".tox/**",
    "web/static/**/*.min.*",
    "web/static/lib/**",
    "web/static/fonts/**",
    "web/static/css/**",
  ]),
  {
    files: ["web/**/*.js"],
    extends: [js.configs.recommended],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: "script",
      globals: {
        ...globals.browser,
        CodeMirror: "readonly",
        flatpickr: "readonly",
      },
    },
  },
]);
