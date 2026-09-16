# 🌐 Multi-Platform Handbook: Linux, Termux (Android), macOS, & Windows

`aeo-graph-engine` is engineered with **zero external runtime dependencies** using Python's standard library. It runs seamlessly on:
- 🐧 **Linux** (Debian, Ubuntu, Fedora, Arch, Alpine, CentOS, WSL2)
- 📱 **Termux on Android** (Pure mobile terminal execution, local HTTP server, mobile AI MCP tools)
- 🍏 **macOS** (Apple Silicon M-Series & Intel x86_64)
- 🪟 **Windows** (Windows 10/11, PowerShell, CMD, Windows Terminal)

---

## 🔍 Platform Health Check Command

Inspect your platform environment and runtime encodings at any time:

```bash
aeo platform
# or
aeo --platform
# or
python3 -m aeo_graph_engine.cli --platform
```

**Example Output:**
```text
============================================================
🌐 AEO GRAPH ENGINE — PLATFORM COMPATIBILITY INFO
============================================================
  • Environment:           LINUX (or TERMUX / WINDOWS / MACOS)
  • Operating System:      Linux (posix) / Windows (nt) / Darwin
  • OS Release:            7.0.13+parrot7-amd64
  • Python Version:        3.13.5 (CPython)
  • Default Encoding:      utf-8
  • Filesystem Encoding:   utf-8
  • Termux Android:        No (or Yes)
  • Windows Subsystem/WSL: No (or Yes)
============================================================
```

---

## 📱 1. Termux on Android

Run autonomous AEO audits, start the Google-styled AEO Studio web workbench, and serve MCP tools directly from your Android phone or tablet.

### Step 1: Install Python & Git in Termux
```bash
pkg update && pkg upgrade -y
pkg install -y python git libexpat
```

### Step 2: Clone & Install `aeo-graph-engine`
```bash
git clone https://github.com/1nc0gn30/aeo-graph-engine.git
cd aeo-graph-engine
pip install -e .
```

### Step 3: Run AEO Studio & Open in Android Browser
```bash
# Launch server (default port 8080/8090)
aeo serve --port 8080

# Or auto-launch into your default Android browser using termux-open-url
aeo serve --port 8080 --open
```

Visit `http://localhost:8080` in Chrome, Firefox, or Brave on your phone.

### Step 4: Grant Storage Access (Optional)
If you want to audit files in your phone's Shared Storage (`/sdcard/` or `~/storage/shared`):
```bash
termux-setup-storage
aeo --validate ~/storage/shared/my-web-project/dist/
```

---

## 🍏 2. macOS (Apple Silicon & Intel)

### Step 1: Install & Verify Python 3
```bash
# macOS includes python3 or install via Homebrew
brew install python

# Clone & Install
git clone https://github.com/1nc0gn30/aeo-graph-engine.git
cd aeo-graph-engine
pip install -e .
```

### Step 2: Connect Claude Desktop on macOS
Claude Desktop configuration file location on macOS:  
`~/Library/Application Support/Claude/claude_desktop_config.json`

Generate your exact config:
```bash
aeo mcp --config claude_desktop
```

Add the block to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": ["-m", "aeo_graph_engine.mcp_server"]
    }
  }
}
```

### Step 3: Connect Cursor on macOS
Cursor project MCP config: `.cursor/mcp.json` or Global Settings:
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": ["-m", "aeo_graph_engine.mcp_server"]
    }
  }
}
```

---

## 🪟 3. Windows (10 / 11 / Server / WSL2)

`aeo-graph-engine` includes native UTF-8 console stream wrappers to prevent `UnicodeEncodeError` on legacy Command Prompt (`cp1252` / `cp437`) and Windows PowerShell.

### Step 1: Install on Windows
Open **PowerShell** or **Windows Terminal**:
```powershell
# Clone repo
git clone https://github.com/1nc0gn30/aeo-graph-engine.git
cd aeo-graph-engine

# Install
python -m pip install -e .
```

### Step 2: Connect Claude Desktop on Windows
Claude Desktop configuration file location on Windows:  
`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python",
      "args": ["-m", "aeo_graph_engine.mcp_server"]
    }
  }
}
```

### Step 3: Connect Cursor on Windows
In your project directory, create `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python",
      "args": ["-m", "aeo_graph_engine.mcp_server"]
    }
  }
}
```

### Step 4: Run AEO Studio on Windows
```powershell
aeo serve --port 8080 --open
```

---

## 🐧 4. Linux & WSL2 (Debian, Ubuntu, Fedora, Arch)

### Quick Install:
```bash
# Debian / Ubuntu / Parrot OS
sudo apt update && sudo apt install -y python3 python3-pip git

# Fedora / RHEL
sudo dnf install -y python3 python3-pip git

# Arch Linux
sudo pacman -S python python-pip git

# Clone and install
git clone https://github.com/1nc0gn30/aeo-graph-engine.git
cd aeo-graph-engine
pip install -e .
```

---

## 🧪 5. Multi-Platform Verification Matrix

| Platform | Terminal / Shell | Native Encoding | Studio Web UI | MCP Server over Stdio | Zero Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Linux** | Bash / Zsh / Fish | UTF-8 | ✅ Supported | ✅ Supported | ✅ 100% Standard Library |
| **Termux (Android)** | Bash / Zsh | UTF-8 / C | ✅ Supported | ✅ Supported | ✅ 100% Standard Library |
| **macOS** | Zsh / Bash | UTF-8 | ✅ Supported | ✅ Supported | ✅ 100% Standard Library |
| **Windows Native** | PowerShell / CMD | UTF-8 auto-wrap | ✅ Supported | ✅ Supported | ✅ 100% Standard Library |
| **Windows WSL2** | Bash | UTF-8 | ✅ Supported | ✅ Supported | ✅ 100% Standard Library |

---

## 🔄 6. GitHub Actions Multi-OS Matrix & Automated Releases

The repository is configured with two automated GitHub Actions workflows:

1. **`.github/workflows/ci.yml`**:
   - Runs test matrix across **Ubuntu, macOS, and Windows** on Python versions `3.9`, `3.10`, `3.11`, `3.12`, and `3.13`.
   - Executes all 86 unit tests and end-to-end CLI tests on every push and pull request.

2. **`.github/workflows/release.yml`**:
   - Triggers automatically whenever commits are pushed to the `main` branch or when a tag like `v1.0.0` is published.
   - Builds `.whl` and `.tar.gz` distribution packages.
   - Computes SHA-256 checksums (`SHA256SUMS.txt`).
   - Generates release notes and publishes a new GitHub Release with attached binaries.
