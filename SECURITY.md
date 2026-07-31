# Security policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability.

Use GitHub's **Report a vulnerability** feature in the repository Security tab.
Include:

- the affected component and version or commit;
- reproduction steps;
- potential impact;
- suggested mitigation, if known.

If private vulnerability reporting has not yet been enabled, contact the repository
owner through a private channel and ask them to enable it before sharing details.

## Supported versions

Security fixes are applied to the latest revision of the default branch. Tagged
releases are supported only when explicitly stated in their release notes.

## Scope

Reports involving authentication, authorization, prompt injection, data leakage,
unsafe document ingestion, dependency compromise, container escape, or Terraform
misconfiguration are welcome.

Microsoft Azure platform vulnerabilities should also be reported through the
[Microsoft Security Response Center](https://www.microsoft.com/msrc).

Never include real access tokens, customer documents, or production identifiers in
a report.
