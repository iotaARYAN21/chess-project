# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.


# Node js

## Install Node Version specified in `.nvmrc`

```bash
    nvm install
```
(this will look for `.nvmrc` and that particular version gets downloaded from internet and installed in your pc)

## Ensure `.nvmrc` node version is in use

```bash
    node -v
```
if match continue 
otherwise run
```bash
    nvm use
```
(checks for `.nvmrc` if found uses that version)

## Install the necessary packages via npm

```bash
    npm install
```
(looks for `package.json` and `package-lock.json` and downloads and installs the packages from npm's default registry)

## Run the frontend

```bash
    npm run dev
``` 
(look at scripts field in `package.json`)

## Prettify the frontend folder
```bash
    npm run format
```
(format the files in the parent directory)