# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅        |

## Reporting a vulnerability

Please report security vulnerabilities privately, not in a public GitHub issue.

Email: **raktimchandra26@gmail.com**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested remediation

You should receive an acknowledgement within 48 hours. If accepted, we will work on a fix and coordinate disclosure.

## Known considerations

NeuroSentry Clinical Console is a visualization dashboard for a research-grade seizure-prediction model and is **not intended for clinical use**. Do not rely on its predictions for patient care decisions. The server accepts arbitrary EEG-window payloads for inference; it performs input shape and bounds checking but does not authenticate requests. Use behind an authentication proxy if exposed to the public internet with sensitive data.

The included Docker image pins CPU-only PyTorch and all dependencies to current stable versions. Dependabot is enabled on the repository to flag upstream CVEs automatically.
