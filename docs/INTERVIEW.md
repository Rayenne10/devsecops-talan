# Interview preparation

## Explain it in 45 seconds

“I worked on a Kubernetes DevSecOps workflow combining deterministic scanners with AI-assisted review. Jenkins runs kube-linter and kube-score in parallel; Python combines the findings and requests structured OpenAI output. Proposed fixes go to a draft GitLab merge request for a human to review. Flux then reconciles approved changes from the watched branch. Elasticsearch records audit history. In the refined public version, an independent baseline policy prevents the AI from downgrading serious security violations.”

Only describe integrations you personally implemented and can demonstrate. Distinguish the original internship from later improvements to this public snapshot.

## Why use both scanners?

They provide complementary static checks. Neither proves that a workload works at runtime. Retain both raw reports and avoid claiming their findings are unique vulnerabilities; they may overlap.

## Why parallel Jenkins stages?

Independent scans run concurrently, reducing the scan portion toward the slower tool’s runtime rather than their sum. Actual benefit depends on agent CPU, filesystem contention and total AI/network latency. The reported 31-second internship run requires its original receipt; the public demo is not that benchmark.

## What does AI add?

It turns findings into explanations and proposed minimal fixes. Scanners and policy make deterministic judgments; AI assists interpretation. Its failure modes include hallucinations, unsafe edits, truncation and prompt injection in manifest text.

## What prevents an unsafe AI fix?

Schema validation, scanned-path allowlisting, identity preservation, YAML parsing and baseline policy checks. Humans still review semantics, rerun tools and validate against the cluster. Do not claim these controls replace admission policies or tests.

## Why a draft MR instead of directly applying YAML?

The proposal stays isolated on a branch pinned to the audited commit. Review and required CI checks happen before merge. The workflow does not invoke kubectl or automatically merge.

## What if OpenAI is unavailable?

Transient errors have bounded retries and a timeout. Invalid/refused results block the stage. Offline mode is a separate policy demo, not a silent substitute for a successful live AI result.

## Does a failed Jenkins build stop Flux?

No. Flux independently watches Git. Protect the target branch and require checks/approval so failed or unreviewed changes never enter the source Flux reconciles.

## What belongs in Elasticsearch and Prometheus?

Elasticsearch stores build audit history; Prometheus stores numeric time-series from exporters. Grafana visualizes them. The public lab provisions datasources and Prometheus self-monitoring; it does not reproduce the historical infrastructure dashboards.

## What would you improve next?

Add Kubernetes schema/server-side validation to candidate MRs, policy-as-code admission checks, prompt-evaluation fixtures, idempotent MR lookup/recovery, authenticated observability and traceable benchmark receipts.

## How did you measure 15+ / 23 / 31 seconds?

Use original Jenkins receipts, exact commits, scanner versions, manifest counts and the timing boundaries. Without those records, say these are reported internship results and do not represent the two-file public demo as proof.
