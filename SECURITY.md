# Security policy

## Reporting a vulnerability

Report vulnerabilities privately to **security@aidoo.ai**. Do not open a public issue.

Include the affected version, the steps to reproduce, and the impact you observed. You
will get an acknowledgement within three business days, and a fix or a mitigation plan
within thirty days for confirmed issues.

## Scope

This repository contains the stdio bridge only. It holds no Odoo credentials and stores
nothing on disk. Reports about the hosted Aidoo platform are equally welcome at the same
address.

## Handling your API key

- The key is read from `AIDOO_API_KEY` or `--api-key`, sent as a bearer token over HTTPS,
  and masked in every log line the bridge writes.
- Prefer the environment over the command line: process arguments are visible to other
  local processes.
- Use one key per person, and revoke it from the Aidoo dashboard as soon as it leaks.
- Grant each key the narrowest set of permissions that still does the job.
