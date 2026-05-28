import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";
import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({
  baseDirectory: import.meta.dirname,
});

const eslintConfig = [...nextCoreWebVitals, ...nextTypescript, ...compat.config({
  extends: ["prettier"],
  plugins: ["unused-imports"],

  rules: {
    "@typescript-eslint/no-empty-object-type": "off",
    "@typescript-eslint/no-unused-vars": "off",
    "unused-imports/no-unused-imports": "error",
    "unused-imports/no-unused-vars": [
      "warn",
      { "argsIgnorePattern": "^_" }
    ],
    "@typescript-eslint/no-explicit-any": "error",
  }
}), {
  ignores: ["components/ui/*", "tailwind.config.js", "watcher.js", "postcss.config.js"]
}];

export default eslintConfig;
