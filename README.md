# d_Pygen ⚡

**Universal AI-Powered Project Generator CLI**

d_Pygen is a powerful, extensible, and intelligent command-line tool that automatically generates complete, production-ready project structures using AI, templates, and plugins.

It supports multiple programming languages, dependency managers, plugin marketplaces, and AI providers, allowing developers to bootstrap projects instantly with correct structure, dependencies, and configurations.

---

# 🚀 Installation

## From Source

```bash
git clone https://github.com/dangerSayan/d_pygen.git

cd d_pygen

pip install -e .
```

## Quick Start

d_Pygen init
d_Pygen create "FastAPI backend"

# ✨ Features

## 🤖 AI-Powered Project Generation

- Generate complete projects using natural language prompts
- Example:

  ```bash
  d_Pygen create "FastAPI backend with JWT authentication"
  ```

- Automatically creates:
  - folder structure
  - source files
  - configs
  - dependency files

Supports multiple AI providers:

- OpenAI
- OpenRouter
- Groq
- Together AI
- Ollama (local AI)

---

## 📦 Multi-Language Support

Supports automatic project detection and dependency installation for:

- Python (pip, poetry)
- Node.js (npm, yarn, pnpm)
- Rust (cargo)
- Go (go modules)

---

## 🔌 Plugin Marketplace System

Install plugins to extend functionality.

Plugins can add:

- new templates
- new generators
- new project types

Example:

```bash
d_Pygen plugins install fastapi
```

---

## 📁 Template Engine with Variants

Use predefined templates:

```bash
d_Pygen create --template fastapi
```

Templates support variants:

```bash
d_Pygen create --template fastapi --variant full
```

---

## ⚙️ Automatic Dependency Installation

Automatically installs dependencies after project generation.

Supports:

- pip
- poetry
- npm
- yarn
- pnpm
- cargo
- go mod

---

## 🧠 Toolchain Detection (Doctor System)

Check system readiness:

```bash
d_Pygen doctor
```

Detects:

- installed runtimes
- dependency managers
- missing tools
- environment issues

---

## 🧩 Plugin Marketplace

View available plugins:

```bash
d_Pygen plugins marketplace
```

Search plugins:

```bash
d_Pygen plugins search
```

Install plugin:

```bash
d_Pygen plugins install plugin_name
```

Update plugin:

```bash
d_Pygen plugins update plugin_name
```

Update all plugins:

```bash
d_Pygen plugins upgrade
```

Uninstall plugin:

```bash
d_Pygen plugins uninstall plugin_name
```

---

## 🧰 Dependency Management

Scan project dependencies:

```bash
d_Pygen doctor
```

---

## ⚡ Interactive Project Creation

Interactive wizard:

```bash
d_Pygen create
```

Prompts you step-by-step.

---

## 🧾 Template Management

List templates:

```bash
d_Pygen templates list
```

List template variants:

```bash
d_Pygen templates variants template_name
```

---

## ⚙️ Configuration Management

View config:

```bash
d_Pygen config show
```

Set config value:

```bash
d_Pygen config set api_provider openrouter
```

Reset config:

```bash
d_Pygen config reset
```

Interactive config wizard:

```bash
d_Pygen config wizard
```

---

## 🧠 AI Provider Configuration

Supports priority fallback system:

Example priority:

```
OpenRouter → Ollama
```

Automatically switches if one fails.

---

## 📊 Telemetry System (Optional)

Anonymous usage tracking helps improve the tool.

Disable telemetry:

```bash
d_Pygen telemetry disable
```

Enable telemetry:

```bash
d_Pygen telemetry enable
```

Clear telemetry:

```bash
d_Pygen telemetry clear
```

---

## 🧹 Cache Management

Clear cache:

```bash
d_Pygen cache clear
```

Clear plugin cache:

```bash
d_Pygen plugins cache clear
```

---

## After publishing to PyPI

```bash
pip install d_pygen
```

---

# 🧑‍💻 Usage Examples

## Generate FastAPI backend

```bash
d_Pygen create "FastAPI backend with JWT auth"
```

---

## Generate MERN stack project

```bash
d_Pygen create "MERN stack with authentication"
```

---

## Use template

```bash
d_Pygen create --template fastapi
```

---

## Use template variant

```bash
d_Pygen create --template fastapi --variant full
```

---

## Interactive mode

```bash
d_Pygen create
```

---

---

# 🧠 How It Works

Workflow:

```
User Prompt
   ↓
AI Provider generates project plan
   ↓
Template engine creates files
   ↓
Dependency manager installs dependencies
   ↓
Project ready
```

---

# 🔌 Plugin System

Plugins can extend:

- templates
- generators
- features

Plugin structure:

```
plugin/
├── plugin.json
└── templates/
```

---

# 🧠 Supported AI Providers

| Provider   | Supported |
| ---------- | --------- |
| OpenAI     | ✅        |
| OpenRouter | ✅        |
| Groq       | ✅        |
| Together   | ✅        |
| Ollama     | ✅        |

---

# 🖥 Supported Platforms

- Windows
- Linux
- macOS
- WSL
- Docker

---

# 🔒 Security

- Basic validation checks are performed before file generation and plugin installation.

---

# 📈 Roadmap

Future plans:

- GUI interface
- More templates
- More plugins
- More AI providers
- Project update support

---

# 🤝 Contributing

Contributions welcome.

Steps:

```
Fork repo
Create branch
Make changes
Submit PR
```

---

# 📜 License

MIT License

---

# 👤 Author

Sayan Bose

GitHub: https://github.com/dangerSayan

---

# ⭐ Support

If you like this project, please star the repository.
