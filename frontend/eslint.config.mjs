import eslint from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import eslintConfigPrettier from "eslint-config-prettier";
import globals from "globals";
import tseslint from "typescript-eslint";
import vueTsEslintConfig from "@vue/eslint-config-typescript";

export default tseslint.config(
  {
    ignores: ["dist", "coverage", "../backend/app/static"],
  },
  eslint.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  ...vueTsEslintConfig(),
  {
    files: ["**/*.{ts,mts,tsx,vue}"],
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
    rules: {
      "@typescript-eslint/consistent-type-imports": "error",
      "vue/multi-word-component-names": "off",
    },
  },
  eslintConfigPrettier,
);
