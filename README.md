# SysAdmin AI — Local Linux/Windows Troubleshooting Agent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/AI-Ollama-000000)](https://ollama.com/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-FF6600)](https://www.trychroma.com/)

An AI-powered sysadmin assistant that runs entirely locally. Diagnose Linux and Windows issues, execute safe commands, and get intelligent troubleshooting guidance without sending data to the cloud.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage Guide](#usage-guide)
- [Safety System](#safety-system)
- [Knowledge Base](#knowledge-base)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [License](#license)

---

## Overview

**SysAdmin AI** is a local-first troubleshooting agent for system administrators. It combines:

- **RAG (Retrieval Augmented Generation)** — Searches a curated knowledge base before answering
- **Safe Command Execution** — Runs diagnostics with built-in safety guards
- **Local LLM Integration** — Uses Ollama models (qwen2.5, kimi, etc.) without cloud dependency
- **Persistent Logging** — All actions and results are logged for audit trails

Perfect for:
- Linux server troubleshooting (Red Hat, Ubuntu, CentOS)
- Windows system administration
- Network diagnostics
- Security audits
- Performance analysis

---

## Features

### Core Capabilities
| Feature | Description |
|---------|-------------|
| **AI Troubleshooting** | Ask natural language questions; get step-by-step solutions |
| **Safe Command Execution** | Run diagnostics with read-only and whitelisted commands |
| **RAG Knowledge Base** | Semantic search over sysadmin documentation |
| **Multi-OS Support** | Linux (RHEL, Ubuntu) and Windows troubleshooting |
| **Persistent Logs** | JSONL logs for every action with timestamps |
| **Vector Search** | ChromaDB-powered document retrieval |
| **Safety Filters** | Prevents destructive commands (rm -rf, format, etc.) |

### Diagnostic Modules
| Module | Description |
|--------|-------------|
| **System Info** | CPU, memory, disk, and process analysis |
| **Network Diagnostics** | Ping, traceroute, port scanning, DNS checks |
| **Log Analysis** | Parse and summarize system logs |
| **Security Audit** | Check permissions, services, and vulnerabilities |
| **Performance** | Identify bottlenecks and resource hogs |
| **Package Management** | Query installed packages and updates |

### Supported Platforms
| Platform | Status |
|----------|--------|
| Red Hat Enterprise Linux 9/10 | ✅ Full support |
| Ubuntu 22.04+ | ✅ Full support |
| CentOS Stream | ✅ Full support |
| Windows 10/11 | ✅ Full support |
| WSL (Windows Subsystem for Linux) | ✅ Tested |

---

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   User Query           │────│   RAG Pipeline       │───│   Knowledge Base     │
│   ("Why is my disk      │     │   - Embed query        │     │   - Linux docs         │
│    full?")              │     │   - Vector search      │     │   - Windows docs       │
└─────────────────────┘     │   - Retrieve context   │     │   - Security guides    │
                                                  └─────────────────────┘
┌─────────────────────┐     │
│   Safety Check          │◀───┼
│   - Block dangerous     │     │
│   - Allow read-only     │     │
└─────────────────────┘     │
                                  │
┌─────────────────────┐     │
│   Command Execution     │◀───┴
│   - Run diagnostics     │
│   - Collect output      │
└─────────────────────┘
┌─────────────────────┐
│   AI Analysis (Ollama)  │
│   - Summarize results   │
│   - Recommend fixes     │
└─────────────────────┘
```

### Data Flow
1. **Query** → User asks a troubleshooting question
2. **RAG** → System embeds query and searches ChromaDB knowledge base
3. **Safety** → Any proposed commands are validated against safety rules
4. **Execution** → Safe commands are executed; output captured
5. **Analysis** → Ollama LLM synthesizes context + results into actionable guidance
6. **Logging** → Full interaction is written to JSONL logs

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + Uvicorn |
| **Language** | Python 3.10+ |
| **AI/LLM** | Ollama (local) + LangChain |
| **Embeddings** | sentence-transformers / nomic-embed-text |
| **Vector DB** | ChromaDB |
| **Safety** | Custom command whitelist/blacklist |
| **Process Monitoring** | psutil |
| **Config** | python-dotenv |
| **Data Validation** | Pydantic v2 |

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- [Ollama](https://ollama.com/) installed and running
- At least one model pulled (recommended: `qwen2.5:7b`)

### Installation

```bash
# Clone the repo
git clone https://github.com/Venuvgp19/sysadmin-ai.git
cd sysadmin-ai

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize knowledge base (one-time)
python -c "from agent.knowledge_manager import KnowledgeManager; km = KnowledgeManager(); km._init_db()"

# Start the agent
python agent/main.py
```

### Quick Scripts

Windows PowerShell:
```powershell
# Setup
.\scripts\setup.ps1

# Run
.\scripts\run.bat
```

Linux/macOS:
```bash
# Run
./scripts/run.sh
```

### Ollama Setup

```bash
# Pull recommended model
ollama pull qwen2.5:7b

# For best results (larger context)
ollama pull qwen2.5:14b

# Ensure Ollama is running
ollama serve
```

---

## Usage Guide

### Interactive Mode
```bash
python agent/main.py
```

Example interaction:
```
╔═══════════════════════════════════════════════════════╗
║  SysAdmin AI Agent v1.0                               ║
║  Model: qwen2.5:7b | OS: Windows                     ║
╚═══════════════════════════════════════════════════════╝

[OK] Connected to Ollama at http://localhost:11434 (model: qwen2.5:7b)

├── Commands ─────────────────────────────────────────────────────────┼
│  ask <question>   Ask a troubleshooting question          │
│  diag              Run system diagnostics                    │
│  logs              View recent logs                          │
│  status            Show agent status                         │
│  help              Show this help                            │
│  quit              Exit the agent                            │
└──────────────────────────────────────────────────────────────────────────┘

> ask Why is my disk full?
[SEARCHING] Querying knowledge base...
[EXEC] Running: wmic logicaldisk get size,freespace,caption
[AI] Your C: drive has only 2.3GB free out of 512GB. Here's what I found:

1. Large directories to investigate:
   - C:\Windows\Temp\ (1.2GB)
   - C:\Users\praneeth\.openclaw\ (4.1GB)
   - C:\Users\praneeth\AppData\Local\ (12GB)

2. Safe cleanup actions:
   - Run Disk Cleanup (cleanmgr)
   - Clear browser caches
   - Empty Recycle Bin

3. Commands to identify large files:
   Get-ChildItem -Path C:\ -Recurse | Sort-Object Length -Descending | Select-Object -First 20
```

### Common Queries
- `"My server is slow — what's consuming resources?"`
- `"How do I check for failed SSH login attempts?"`
- `"Why is my service failing to start?"`
- `"Show me how to configure a firewall on RHEL 9"`
- `"What updates are available for my system?"`

---

## Safety System

### Command Categories
| Category | Examples | Action |
|----------|----------|--------|
| **Read-Only** | `df`, `ps`, `netstat`, `systemctl status` | ✅ Allowed |
| **Safe Write** | `systemctl restart nginx` | ⚠️ Confirm first |
| **Destructive** | `rm -rf /`, `format`, `mkfs` | ❌ Blocked |
| **Unknown** | Custom scripts | ⚠️ Confirm first |

### Safety Configuration
Edit `agent/settings.py` to customize:
- Whitelisted commands
- Blacklisted patterns
- Confirmation requirements
- Dry-run mode

---

## Knowledge Base

### Included Documents
| Document | Description |
|----------|-------------|
| `linux-troubleshooting.txt` | Common Linux issues and fixes |
| `linux_audit_commands.txt` | Security audit command reference |
| `linux_system_admin_handbook.txt` | System admin best practices |
| `linuxcommand_learning_shell.txt` | Shell scripting guide |
| `rhel_9_to_10_upgrade_docs.txt` | RHEL upgrade procedures |
| `windows-troubleshooting.txt` | Windows-specific troubleshooting |

### Adding Custom Knowledge
Place `.txt` files in the `knowledge/` directory and run:
```python
from agent.knowledge_manager import KnowledgeManager
km = KnowledgeManager()
km.ingest_documents("knowledge/")
```

---

## Project Structure

```
sysadmin-ai/
│
├── agent/                       # Core agent logic
│   ├── __init__.py
│   ├── main.py                   # Main agent class & CLI
│   ├── knowledge_manager.py      # RAG / vector DB management
│   ├── safety.py                  # Command safety validator
│   └── settings.py                # Configuration & constants
│
├── knowledge/                    # Knowledge base documents
│   ├── linux-troubleshooting.txt
│   ├── linux_audit_commands.txt
│   ├── linux_system_admin_handbook.txt
│   ├── linuxcommand_learning_shell.txt
│   ├── rhel_9_to_10_upgrade_docs.txt
│   └── windows-troubleshooting.txt
│
├── logs/                         # Action logs (JSONL format)
│   └── agent-2026-05-22.jsonl
│
├── vector_db/                     # ChromaDB persistent storage
│   └── chroma.sqlite3
│
├── scripts/                       # Runner scripts
│   ├── run.bat
│   ├── run.sh
│   └── setup.ps1
│
├── requirements.txt               # Python dependencies
├── DEPLOYMENT.md                  # Deployment guide
└── README.md                      # This file
```

---

## API Reference

### FastAPI Endpoints (if deployed as service)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ask` | POST | Ask a troubleshooting question |
| `/diag` | POST | Run system diagnostics |
| `/logs` | GET | Retrieve recent logs |
| `/knowledge/search` | POST | Search knowledge base |
| `/knowledge/ingest` | POST | Ingest new documents |

### Example API Call
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Why is my disk full?"}'
```

---

## Deployment

### Local Development
```bash
python agent/main.py
```

### FastAPI Server Mode
```bash
uvicorn agent.main:app --host 0.0.0.0 --port 8000
```

### Docker (Future)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "agent/main.py"]
```

---

## Environment Variables

Create `.env`:

```env
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Agent Settings
AGENT_LOG_LEVEL=INFO
AGENT_MAX_RETRIES=3
AGENT_TIMEOUT=30

# Safety
SAFETY_CONFIRM_DESTRUCTIVE=true
SAFETY_DRY_RUN=false
```

---

## Future Enhancements

- [ ] Web UI (React + FastAPI)
- [ ] Slack/Discord bot integration
- [ ] Multi-agent collaboration
- [ ] Ansible/Terraform playbook generation
- [ ] Scheduled health checks
- [ ] Alerting integration (Email, PagerDuty)
- [ ] Kubernetes troubleshooting module
- [ ] Windows Event Log analysis

---

## License

MIT © Venuvgp19

---

> Built with Python + Ollama + LangChain. Your data never leaves your machine.
