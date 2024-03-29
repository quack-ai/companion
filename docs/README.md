<h1 align="center">
 Quack documentation
</h1>

<p align="center">
  <a href="https://github.com/quack-ai/companion/actions?query=workflow%3Adocs">
    <img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/quack-ai/companion/docs.yml?branch=main&label=CI&logo=github&style=flat-square" />
  </a>
  <a href="https://mintlify.com/">
    <img src="https://img.shields.io/badge/Framework-Mintlify-0D9373?style=flat-square&logoColor=white" alt="Mintlify" />
  </a>
  <a href="https://github.com/quack-ai/companion/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/quack-ai/companion.svg?label=License&logoColor=fff&style=flat-square" alt="License" />
  </a>
</p>
<p align="center">
  <a href="https://discord.gg/E9rY3bVCWd">
    <img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat-square&logo=discord&logoColor=white" />
  </a>
  <a href="https://twitter.com/quack_ai">
    <img src="https://img.shields.io/badge/-@quack_ai-1D9BF0?style=flat-square&logo=twitter&logoColor=white" alt="Twitter" />
  </a>
</p>


# Mintlify Starter Kit

Click on `Use this template` to copy the Mintlify starter kit. The starter kit contains examples including

- Guide pages
- Navigation
- Customizations
- API Reference pages
- Use of popular components

### 👩‍💻 Development

Install the [Mintlify CLI](https://www.npmjs.com/package/mintlify) to preview the documentation changes locally. To install, use the following command

```
npm i -g mintlify
```

Run the following command at the root of your documentation (where mint.json is)

```
mintlify dev
```

### 😎 Publishing Changes

Changes will be deployed to production automatically after pushing to the default branch.

You can also preview changes using PRs, which generates a preview link of the docs.

#### Troubleshooting

- Mintlify dev isn't running - Run `mintlify install` it'll re-install dependencies.
- Page loads as a 404 - Make sure you are running in a folder with `mint.json`
