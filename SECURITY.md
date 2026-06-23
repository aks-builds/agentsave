# Security Policy

## Supported Versions

The following versions of AgentSave are currently receiving security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Yes             |

Older versions are not supported. Please upgrade to the latest release.

## Reporting a Vulnerability

**Do not file a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability in AgentSave, please report it
privately by emailing **its.aks@outlook.com**.

Include in your report:
- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Any proof-of-concept code or screenshots (if applicable)
- The AgentSave version(s) affected

**Response timeline:**
- You will receive an acknowledgement within **48 hours**
- We will investigate and provide a status update within **7 business days**
- We will work with you to coordinate disclosure after a fix is available

We follow responsible disclosure: we ask that you give us reasonable time to
patch the issue before making it public.

## Security Considerations

### API Token Storage

AgentSave SDK tokens are stored in `~/.agentsave/config.json` on disk.
Ensure this file has appropriate permissions (`chmod 600`). Do not commit
tokens to version control or expose them in environment variables that are
logged.

### Telemetry Opt-In

AgentSave telemetry is **opt-in only**. By default, no data leaves your machine.
Telemetry is enabled only when you explicitly run `agentsave login` and connect
a dashboard. Even when enabled, only the following fields are transmitted:

- `run_id` (random UUID, not linked to any personal identity)
- `framework` (e.g., `langchain`, `autogen`)
- `model` (e.g., `gpt-4o`)
- `tokens_before`, `tokens_after` (integer counts)
- `success` (boolean)

### No PII Collected

AgentSave does not collect, transmit, or store any personally identifiable
information (PII). Agent prompts, tool outputs, and conversation content are
never sent to AgentSave servers. The supervisor operates entirely in-process.
