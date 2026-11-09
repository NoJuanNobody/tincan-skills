---
name: tincan-agent-hitl
description: >-
  Run interactive or single-shot AI queries against TinCan's pooled OpenRouter gateway
  (tincan chat, tincan ask), audit live OpenRouter credits and per-model cost rates
  (tincan credits, tincan cost), start the TinCan stdio MCP server (tincan mcp), and
  govern incoming remote actions via the Human-In-The-Loop Accessibility Gate
  (tincan actions, tincan trigger, tincan dismiss). Use when querying TinCan AI models,
  checking OpenRouter spend, wiring TinCan MCP, or approving/rejecting queued peer actions.
---

# TinCan Pooled AI Agent, Cost Telemetry & HITL Accessibility Gate (`tincan-agent-hitl`)

Query pooled OpenRouter frontier models from the terminal, track real-time credit burn, expose TinCan as a standard Model Context Protocol (MCP) server, and enforce strict Human-In-The-Loop (HITL) execution gating.

## 1. Interactive & Single-Shot Pooled AI Queries (`chat`, `ask`)

```bash
# Launch interactive REPL with the default pooled model (gemini-brain)
tincan chat

# Single-shot query with a specific model alias
tincan ask "Summarize the unread architectural decisions in our shared vault" --model claude-sonnet

# Quick one-liner via chat
tincan chat "Write a pytest fixture for the X25519 sealed envelope" --model gemini-brain
```

## 2. Live OpenRouter Credits & Cost Telemetry (`credits`, `cost`)

Inspect pooled API balances, session spend, and per-model prompt/completion token rates:

```bash
# Display formatted credit and cost table
tincan credits

# Emit machine-readable JSON for budget guardrails
tincan cost --json
```

## 3. Human-In-The-Loop (HITL) Accessibility Gate (`actions`, `trigger`, `dismiss`)

When a remote peer or autonomous agent dispatches an executable action (`run_script`, `git_sync`, `deploy`, `open_url`), TinCan holds it inside the local **Accessibility Gate** until explicitly approved by the human operator:

```bash
# 1. Inspect all pending actions in the Accessibility Gate
tincan actions --json

# 2. Approve and execute queued action #1
tincan trigger 1 --json

# 3. Dismiss/reject queued action #2 without executing
tincan dismiss 2
```

## 4. Model Context Protocol (MCP) Stdio Server (`mcp`)

Expose TinCan's identity, sealed messaging, contacts, presence, and Accessibility Gate tools to Claude Code, Cursor, or Antigravity via stdio MCP:

```bash
tincan mcp
```

Example MCP client configuration (`mcp_config.json`):
```json
{
  "mcpServers": {
    "tincan": {
      "command": "tincan",
      "args": ["mcp"],
      "env": {
        "TINCAN_RELAY": "https://iot-federated-agent-memory-production.up.railway.app"
      }
    }
  }
}
```
