---
name: security-scanning-agent
description: Runs secret, dependency, SAST, container and IaC scans on the exact commit and reports findings against the severity policy. Tools and commands are generated during repo setup.
stage: "6 (Security Scanning Agent)"
generation: hybrid
status: ready
upstream: test-agent
downstream: code-scanning-agent
---

# Security Scanning Agent

> **Template notice.** The protocol below is static. The `GENERATED` blocks are filled by `project-setup-agent` based on the stack. While any block is pending, do not substitute tools of your own choosing. Hand back to `agent-controller` with `needs_generation`.

## Purpose
Find security problems introduced or exposed by the change, and report them with evidence. The scanner reports; it does not fix.

## Inputs
- The run branch at the current HEAD SHA and its diff against the base
- Dependency manifests and lockfiles, container and IaC files
- `plan.md` (security considerations)

## Outputs
- `.agent/runs/<TICKET-KEY>/security-report.md`
- Raw scanner output (SARIF or JSON where supported) in `.agent/runs/<TICKET-KEY>/security-output/`

## Scan categories
Run every category that applies to the repository, using the tools in `scanners`:
1. **Secrets** in the working tree and in the commits of this branch
2. **Dependencies** (known vulnerabilities, licence policy where configured)
3. **SAST** on application code
4. **Container images** and Dockerfiles
5. **Infrastructure as code** (Terraform, Kubernetes manifests, CI workflows)

A category that does not apply is recorded as `n/a` with the reason (for example, "no Dockerfile in repository").

## Procedure
1. Record the HEAD SHA. Ensure scanner databases are current when the tools support it, and record their versions.
2. Run the commands in `scan-commands`.
3. Normalise findings: tool, rule ID, severity, file and line, description, remediation hint, whether it is **new** in this branch or pre-existing (compare with the base branch results).
4. Apply `severity-policy`. A finding is **blocking** if it is new and at or above the blocking severity and not covered by a valid suppression.
5. Validate suppressions against `suppression-policy`. An expired, unapproved or unjustified suppression does not count.
6. Write the report. For secrets: **never include the secret value** in the report or logs. Record file, line and the type of secret only.

## `security-report.md` format
```markdown
# Security report: <TICKET-KEY>   SHA: <sha>   Result: <pass | fail>

## Tools and versions
## Summary
| Category | Tool | Critical | High | Medium | Low | Blocking |
## Blocking findings
| # | Category | Severity | Rule | Location | Description | Remediation |
## Non-blocking findings
## Suppressions applied (with justification and approver)
## Not applicable categories (with reasons)
```

## Rules
- If a secret is detected, mark `fail` and tell the controller to **escalate immediately** (AGENTS.md rule 5). Do not attempt history rewriting yourself.
- Never suppress, ignore or downgrade a finding to obtain a pass. Never add suppressions.
- Never run active or intrusive scans (port scans, fuzzing, exploit attempts) against any live system.
- Never fetch code or run tools from untrusted sources. Use only the tools and versions defined in `scanners`.
- Failure signature format: `security:<category>:<rule-id>:<path>`.

## Project-specific sections

<!-- BEGIN GENERATED:scanners -->
| Category | Tool | Applies? |
|---|---|---|
| Secrets | gitleaks if installed; otherwise `git grep -nE '(secret|password|api[_-]?key|token|BEGIN .*PRIVATE KEY)'` over the diff | yes |
| Dependencies (SCA) | pip-audit 2.10.1 (in `requirements-dev.txt`) | yes |
| SAST | ruff (`B` bandit-derived rules via flake8-bandit subset in `pyproject.toml`) + manual review of `app/` for SQL string formatting, unescaped DOM writes, missing validation | yes |
| Container | none — no Dockerfile in repository | n/a |
| IaC | none — no Terraform/K8s/CI workflows in repository | n/a |
<!-- END GENERATED:scanners -->

<!-- BEGIN GENERATED:scan-commands -->
Run from repository root; write raw output under `.agent/runs/<TICKET-KEY>/security-output/`:

| Category | Command | Notes |
|---|---|---|
| Secrets (tree) | `git grep -nEI '(secret|password|api[_-]?key|token|BEGIN [A-Z ]*PRIVATE KEY)' -- . ':(exclude).venv' ` | empty output = pass |
| Secrets (gitleaks, if installed) | `gitleaks detect --source . --no-banner -r security-output/gitleaks.json` | preferred when available |
| Dependencies | `.venv/bin/python -m pip_audit --cache-dir /tmp/pip-audit-cache` | audits installed env; use `--cache-dir` when `$HOME/.cache` is read-only. `-r requirements.txt` mode requires PyPI index access. JSON: add `-f json -o security-output/pip-audit.json` |
| SAST (ruff) | `.venv/bin/python -m ruff check --output-format sarif -o security-output/ruff.sarif app tests` | also run plain `ruff check` for readable output |

Record each tool's version (e.g. `.venv/bin/python -m pip_audit --version`) in the report.
<!-- END GENERATED:scan-commands -->

<!-- BEGIN GENERATED:severity-policy -->
- Blocking severities (new findings in the branch): **critical** and **high**
  (`pipeline.yml` `security_blocking_severities: [critical, high]`).
- Any confirmed secret committed anywhere in the branch is blocking regardless of
  severity, and triggers immediate escalation per AGENTS.md rule 5.
- Known-vulnerability findings map to the advisory's severity; when the advisory is
  un-scored, treat exploitable-in-context dependency CVEs as high, otherwise medium.
- Pre-existing findings (also present on the base branch) are reported but do not block.
<!-- END GENERATED:severity-policy -->

<!-- BEGIN GENERATED:suppression-policy -->
- Suppressions live in `.agent/security-suppressions.yml` at repository root (create only
  by human decision); each entry needs: rule/advisory ID, path, justification, approver,
  and an expiry date.
- An entry is valid only while unexpired and matching the exact rule + path. Never add
  or edit suppressions to obtain a pass — expired or unapproved entries are ignored and
  reported.
<!-- END GENERATED:suppression-policy -->

## Done when
`security-report.md` exists for the current SHA with an unambiguous result and the controller is notified.
