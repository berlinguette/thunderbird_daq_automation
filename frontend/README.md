# Thunderbird Data Analyzer Frontend

This is the frontend interface for the Thunderbird automatic data analyzer.
It gives users visibility into the conversion/processing status of all experiments stored on the QMI data drive,
as well as allowing them to easily run conversion/processing scripts. The frontend is meant to interface with the backend API server which manages the inventory of experiments.


## Installation

To install dependencies, run `npm install`. The program needs a `.env` file in the root directory - use the provided `.env_example` as a template.

## Usage

To start the dev server, run `npm run dev`.

To build for production, run `npm run build` and use `npm run preview` to preview the production build.

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type aware lint rules:

- Configure the top-level `parserOptions` property like this:

```js
export default {
  // other rules...
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: ['./tsconfig.json', './tsconfig.node.json'],
    tsconfigRootDir: __dirname,
  },
}
```

- Replace `plugin:@typescript-eslint/recommended` to `plugin:@typescript-eslint/recommended-type-checked` or `plugin:@typescript-eslint/strict-type-checked`
- Optionally add `plugin:@typescript-eslint/stylistic-type-checked`
- Install [eslint-plugin-react](https://github.com/jsx-eslint/eslint-plugin-react) and add `plugin:react/recommended` & `plugin:react/jsx-runtime` to the `extends` list
