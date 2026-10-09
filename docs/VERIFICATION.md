# Verification scope

Local validation on 9 October 2026: 19 Python tests passed, including unsafe workload checks, path traversal rejection, resource identity changes, malformed scanner results, a LOW AI result unable to bypass HIGH policy, draft MR request payloads pinned to an audited SHA, bounded transient retries and offline isolation.

GitHub CI executes the real kube-linter and kube-score binaries (checksum verified), creates offline JSON/HTML reports and asserts an expected blocked gate for the unsafe fixture. Its lab job validates Compose configuration and builds/runs the Jenkins image with its actual scanner and Python dependencies.

Live OpenAI requests, writes to GitLab, an actual Jenkins server job, Elasticsearch ingestion and Flux/k3s reconciliation need separately configured external environments and are not established by mocked tests. GitLab API tests inspect payloads and no-redirect/timeouts without contacting GitLab. No original internship benchmark receipt is included.

The GitHub Actions badge and run logs are the source of truth for current CI status. Successful CI artifacts include scanner and audit reports, with a 30-day retention period.

## Verified CI receipt

- [Successful run 37934279809](https://github.com/Rayenne10/devsecops-talan/actions/runs/37934279809)
- Verified code commit: `4f4f9ea52434ca00ec1d1a6f484c3ce72407b408`
- Both `tests` and `lab` jobs passed. Python: 19 tests; dependency audit: no known vulnerabilities in the resolved requirements; real scanner demo: expected HIGH gate blocked.
- Jenkins image built with the installed plugins and ran as `uid=1000(jenkins)`. Both scanner binaries and Python imports executed successfully.
- [Download audit reports](https://github.com/Rayenne10/devsecops-talan/actions/runs/37934279809/artifacts/11617477908): raw scanner reports, consolidated JSON, offline review JSON and HTML. Expires 8 November 2026; rerun CI to regenerate.

A dependency audit is not a complete container vulnerability scan. This verification does not establish live Jenkins server startup, Elasticsearch/Grafana runtime readiness or Flux reconciliation.
