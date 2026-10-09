# Verification scope

Local validation on 9 October 2026: 19 Python tests passed, including unsafe workload checks, path traversal rejection, resource identity changes, malformed scanner results, a LOW AI result unable to bypass HIGH policy, draft MR request payloads pinned to an audited SHA, bounded transient retries and offline isolation.

GitHub CI executes the real kube-linter and kube-score binaries (checksum verified), creates offline JSON/HTML reports and asserts an expected blocked gate for the unsafe fixture. Its lab job validates Compose configuration and builds/runs the Jenkins image with its actual scanner and Python dependencies.

Live OpenAI requests, writes to GitLab, an actual Jenkins server job, Elasticsearch ingestion and Flux/k3s reconciliation need separately configured external environments and are not established by mocked tests. GitLab API tests inspect payloads and no-redirect/timeouts without contacting GitLab. No original internship benchmark receipt is included.

The GitHub Actions badge and run logs are the source of truth for current CI status. Successful CI artifacts include scanner and audit reports, with a 30-day retention period.
