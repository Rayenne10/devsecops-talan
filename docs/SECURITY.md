# Trust boundaries

- Scanner failures and missing/malformed reports block analysis; findings are not silently converted into success.
- AI output is untrusted. Strict response structure, local validation and deterministic policy reduce risk, but do not establish semantic correctness.
- The baseline blocks privileged containers, privilege escalation, missing non-root enforcement, host namespace/filesystem access and added capabilities. It is not a complete Kubernetes admission policy.
- Draft MRs require manual diff review, rescans and cluster validation. Protect the Flux source branch; Jenkins has no automatic authority over independent Flux reconciliation.
- Secrets never belong in scanned manifests. Do not expose Jenkins or the local unauthenticated Elasticsearch endpoint publicly.
- CI uses no OpenAI/GitLab credentials. Production integration credentials must be stored in Jenkins, scoped and rotated.
- Audit exports include source/build, severity, file paths and mode, not prompts, tokens or full manifests. Export failure fails the stage rather than losing audit data silently.
- Retry is limited to transient OpenAI errors; GitLab writes are not blindly retried because duplicate remote branches/MRs may result.
