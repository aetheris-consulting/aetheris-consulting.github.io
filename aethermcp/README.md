# AEF-OS v7.0 "AetherMCP"

**AI Exploration Framework - Operating System**
**The Linux Kernel for AI Orchestration**

## Overview

AEF-OS is an **MCP (Model Context Protocol) execution environment** that enables AI agents to orchestrate multiple tools, models, and data sources to fulfill user intent. Rather than prescribing rigid workflows, it provides a **substrate** where AIs dynamically compose solutions using available MCP servers and proven templates.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTENT                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  MCP KERNEL                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ Orchestrator │ │ Tool Registry│ │ Protocol     │       │
│  │              │ │              │ │ Handler      │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
│  ┌──────────────┐ ┌──────────────────────────────┐        │
│  │ Provenance   │ │ Template Library             │        │
│  │ Engine       │ │                              │        │
│  └──────────────┘ └──────────────────────────────┘        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  MCP SERVERS                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │   LLM    │ │Simulation│ │   Data   │ │Validation│     │
│  │ Servers  │ │ Servers  │ │ Servers  │ │ Servers  │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Intent-Driven Orchestration**: Natural language → structured execution
- **MCP Protocol**: Standardized tool communication
- **Template Library**: Reusable workflow patterns
- **Provenance Tracking**: Immutable audit trail with cryptographic verification
- **Cost Management**: Real-time budget tracking and enforcement
- **Multi-AI Ensemble**: Orchestrate multiple LLMs for diverse perspectives
- **Security by Design**: Recursive protection, cognitive guardians, sentinels
- **Flexible Deployment**: Browser, Docker, SBC, Federated modes

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/aetheris-consulting/aethermcp
cd aethermcp

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your API keys
```

### Basic Usage

```python
from aethermcp import AetherMCP

# Initialize
aether = AetherMCP(config_path="config/config.yaml")

# Execute intent
result = aether.execute(
    intent="Design a secure sovereign AI handshake protocol",
    budget=100.0,
    constraints=["Must prevent replay attacks", "Must validate identity"]
)

# Review results
print(result.deliverables)
print(result.provenance)
print(f"Cost: ${result.cost:.2f}")
print(f"Confidence: {result.confidence:.2f}")
```

## Deployment Modes

### Browser Mode (Zero Install)
- Run entirely in browser with WebAssembly
- Air-gapped operation with local Llama
- No installation required

### Docker Mode (Production)
```bash
docker-compose up -d
```

### SBC Mode (Sovereign Edge)
- Deploy on Raspberry Pi or equivalent ARM SBC
- Offline operation with local models
- Solar powered for grid-down scenarios

### Federated Mode
- Multi-node collaboration
- Distributed processing
- Encrypted communication

## Documentation

- [Architecture Overview](docs/architecture.md)
- [MCP Protocol](docs/mcp-protocol.md)
- [Template Library](docs/templates.md)
- [Security Model](docs/security.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)

## Examples

See the `examples/` directory for:
- Simple query execution
- Multi-AI brainstorming
- Security validation workflows
- Budget-constrained execution
- Custom template creation

## License

Apache 2.0

## Version

v7.0 "AetherMCP Edition"
