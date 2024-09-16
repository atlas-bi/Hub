import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [{
    ignores: [
        "web/static/**/*.min.*",
        "node_modules/*",
        "**/.mypy_cache",
        "**/.pytest_cache",
        "**/.tox",
        "web/static/lib/*",
        "web/static/fonts/*",
        "web/static/css/*",
    ],
}, ...compat.extends("eslint:recommended"), {
    languageOptions: {
        globals: {
            ...globals.browser,
            CodeMirror: "readonly",
            flatpickr: "readonly",
        },

        ecmaVersion: 12,
        sourceType: "script",
    },

    rules: {},
}];
