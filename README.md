# d_Pygen ⚡

## Universal AI-Powered Project Generator CLI

d_Pygen is a powerful, extensible, and intelligent command-line tool
that generates complete, production-ready project structures using AI,
templates, and plugins.

It supports multiple languages, dependency managers, plugin
marketplaces, and AI providers --- allowing developers to bootstrap
projects instantly with correct structure, dependencies, and
configurations.

---

# 📚 Table of Contents

- Overview
- Installation
- Quick Start
- Features
- Command Reference
- Core Commands
- Config Commands
- Plugin Commands
- Template Commands
- Cache Commands
- Telemetry Commands
- CLI Options
- Example Workflows
- Configuration
- Supported Providers
- Supported Platforms
- Security
- License
- Author

---

# 🚀 Overview

d_Pygen is an intelligent CLI that generates complete project structures
using:

- AI providers (OpenAI, OpenRouter, Gemini, Ollama, Groq, Together)
- Built-in templates
- Plugin system
- Dependency detection and installation
- Automatic environment and toolchain validation
- Template variants and plugin extensions

It eliminates manual setup and generates production-ready projects
instantly.

---

# 🚀 Installation

## Install from PyPI (Recommended)

```bash
pip install d_pygen
```

## Install from Source

```bash
git clone https://github.com/dangerSayan/d_pygen.git
cd d_pygen
pip install -e .
```

---

# ⚡ Quick Start

Initialize configuration:

```bash
d_Pygen init
```

Create your first project:

```bash
d_Pygen create "FastAPI backend with JWT"
```

Interactive mode:

```bash
d_Pygen create
```

Show help:

```bash
d_Pygen help
```

Show version:

```bash
d_Pygen version
```

---

# ✨ Features

- AI-powered project generation
- Template-based generation
- Plugin marketplace and plugin system
- Automatic dependency installation
- Toolchain and environment validation
- Interactive mode
- Template variants
- Cross-platform support
- Telemetry control
- Cache system
- Multiple AI provider support

---

# 📖 Command Reference

## 🧠 Core Commands

```bash
d_Pygen create "project description"
d_Pygen create --template fastapi --variant minimal
d_Pygen create "FastAPI backend" --install local
d_Pygen init
d_Pygen doctor
d_Pygen update
d_Pygen version
d_Pygen help
```

---

## ⚙️ Config Commands

```bash
d_Pygen config show
d_Pygen config set api_provider openrouter
d_Pygen config set api_key YOUR_KEY
d_Pygen config set api_model gpt-4o
d_Pygen config reset
d_Pygen config edit
d_Pygen config wizard
```

---

## 🔌 Plugin Commands

```bash
d_Pygen plugins install fastapi
d_Pygen plugins uninstall fastapi
d_Pygen plugins list
d_Pygen plugins search
d_Pygen plugins info fastapi
d_Pygen plugins marketplace
d_Pygen plugins update fastapi
d_Pygen plugins update-all
d_Pygen plugins upgrade
d_Pygen plugins outdated
d_Pygen plugins validate fastapi
d_Pygen plugins publish
d_Pygen plugins registry update
d_Pygen plugins cache clear
d_Pygen plugins cache info
```

---

## 📁 Template Commands

```bash
d_Pygen templates list
```

---

## 🧹 Cache Commands

```bash
d_Pygen cache list
d_Pygen cache clear
d_Pygen cache info
```

---

## 📊 Telemetry Commands

```bash
d_Pygen telemetry status
d_Pygen telemetry enable
d_Pygen telemetry disable
d_Pygen telemetry clear
```

Telemetry is anonymous and optional.

---

# ⚙️ CLI Options

| Option       | Description             |
| ------------ | ----------------------- |
| `--provider` | Select AI provider      |
| `--template` | Use template            |
| `--variant`  | Template variant        |
| `--install`  | Dependency install mode |
| `--output`   | Output directory        |
| `--name`     | Override project name   |
| `--dry-run`  | Preview only            |
| `--force`    | Overwrite existing      |
| `--verbose`  | Enable verbose logging  |
| `--no-cache` | Disable cache           |

---

# 🧠 Example Workflows

```bash
d_Pygen init
d_Pygen create "FastAPI backend"
d_Pygen plugins install fastapi
d_Pygen doctor
d_Pygen update
```

---

# 📁 Configuration

Configuration directory:

    ~/.d_pygen/

Contains:

    config.json
    plugins/
    templates/
    cache/
    logs/
    registry.json

---

# 🤖 Supported AI Providers

- OpenAI
- OpenRouter
- Gemini
- Groq
- Together
- Ollama

---

# 🖥 Supported Platforms

- Windows
- Linux
- macOS
- WSL

---

# 🔒 Security

- Plugin validation
- Safe file generation
- Plan validation
- No arbitrary code execution

---

# 📜 License

MIT License

---

# 👤 Author

Sayan Bose

GitHub: https://github.com/dangerSayan/d_pygen

---

# ⭐ Support

If you like this project, please star the repository.
