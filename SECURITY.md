# Security Policy

## Supported versions

Security fixes are applied to the latest release on the default branch. Older tags may remain available for
reproducibility but are not guaranteed to receive fixes.

## Reporting a vulnerability

Prefer GitHub private vulnerability reporting from the repository's **Security** tab when it is available. Include:

- the affected commit or tag;
- a minimal reproduction;
- impact and preconditions;
- suggested mitigation, if known.

Do not include real birth records, personal identifiers, credentials, tokens, or third-party confidential data. If
private reporting is unavailable, open a minimal issue that asks the maintainer to establish a private channel; do
not publish exploit details or sensitive data in that issue.

## Security properties and boundaries

The core engine is designed to run offline with the Python standard library. It does not require credentials,
network access, telemetry, or persistent storage. Input is untrusted JSON and is validated against a strict schema.

The following are outside the core engine's security boundary:

- the privacy and retention behavior of chat, terminal, CI, or hosting platforms;
- calendar conversion or chart-generation services added by downstream users;
- third-party wrappers, forks, plugins, or MCP servers;
- social or professional harm caused by treating metaphysical output as factual assessment.

Report security issues separately from disagreements about the traditional model. Safety or privacy weaknesses that
could enable high-impact screening, disclosure of personal data, or misleading claims are welcome as security-adjacent
reports.
