import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

spec = importlib.util.spec_from_file_location('workflow', Path(__file__).parents[1] / 'scripts/workflow.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

@pytest.fixture
def manifest():
    return {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': 'demo'},
            'spec': {'template': {'spec': {'containers': [{'name': 'app', 'image': 'example:v1',
            'securityContext': {'runAsNonRoot': True, 'allowPrivilegeEscalation': False, 'capabilities': {'drop': ['ALL']}}}]}}}}

@pytest.fixture
def workspace(tmp_path, monkeypatch, manifest):
    monkeypatch.setattr(w, 'ROOT', tmp_path)
    (tmp_path / 'k8s').mkdir()
    (tmp_path / 'k8s/demo.yaml').write_text(yaml.safe_dump(manifest))
    w.save('kube-linter.json', {'Reports': [], 'Summary': {'Errored': False}})
    w.save('kube-score.json', [{'object': {}}])
    return tmp_path

@pytest.mark.parametrize('mutation', [
    lambda p: p.update(hostNetwork=True),
    lambda p: p.update(volumes=[{'hostPath': {'path': '/'}}]),
    lambda p: p['containers'][0]['securityContext'].update(privileged=True),
    lambda p: p['containers'][0]['securityContext'].update(runAsUser=0),
    lambda p: p['containers'][0]['securityContext'].update(allowPrivilegeEscalation=True),
    lambda p: p['containers'][0]['securityContext'].update(capabilities={'add': ['SYS_ADMIN']}),
])
def test_policy_blocks_unsafe_resources(manifest, mutation):
    assert not w.policy([manifest])
    mutation(manifest['spec']['template']['spec'])
    assert w.policy([manifest])

@pytest.mark.parametrize('path', ['../../evil.yaml', '/tmp/evil.yaml', 'k8s/unscanned.yaml'])
def test_patch_path_allowlist(manifest, path):
    with pytest.raises(ValueError):
        w.validate_patches({'patches': {path: yaml.safe_dump(manifest)}}, {'manifest': {'k8s/demo.yaml': yaml.safe_dump(manifest)}})

def test_identity_and_secret_rejection(manifest):
    original = yaml.safe_dump(manifest)
    manifest['metadata']['name'] = 'hijacked'
    with pytest.raises(ValueError):
        w.validate_patches({'patches': {'k8s/demo.yaml': yaml.safe_dump(manifest)}}, {'manifest': {'k8s/demo.yaml': original}})
    with pytest.raises(ValueError):
        w.documents('apiVersion: v1\nkind: Secret\nmetadata: {name: credentials}\n')

def test_failed_scanner_not_empty_success(workspace):
    w.save('kube-linter.json', {'Summary': {'Errored': True}})
    with pytest.raises(ValueError): w.consolidate()
    (workspace / 'kube-linter.json').write_text('not JSON')
    with pytest.raises(ValueError): w.consolidate()

def test_low_ai_cannot_override_policy(workspace, manifest):
    manifest['spec']['template']['spec']['containers'][0]['securityContext']['privileged'] = True
    (workspace / 'k8s/demo.yaml').write_text(yaml.safe_dump(manifest))
    w.consolidate()
    w.save('ai-report.json', {'criticite': 'LOW'})
    with pytest.raises(ValueError): w.gate()

@pytest.mark.parametrize('level', ['HIGH', 'UNKNOWN', None])
def test_gate_fails_closed(workspace, level):
    w.consolidate(); w.save('ai-report.json', {'criticite': level})
    with pytest.raises(ValueError): w.gate()

def test_safe_draft_mr_pinned_to_audited_commit(workspace, monkeypatch, manifest):
    w.consolidate()
    w.save('ai-report.json', {'criticite': 'LOW', 'resume': 'Review required', 'patches': {'k8s/demo.yaml': yaml.safe_dump(manifest)}})
    env = {'GIT_COMMIT': 'a'*40, 'GITLAB_TOKEN': 'fake-test-only', 'GITLAB_PROJECT_ID': '123', 'BUILD_NUMBER': '42'}
    for k, v in env.items(): monkeypatch.setenv(k,v)
    session = Mock()
    session.post.return_value = SimpleNamespace(status_code=201, json=lambda: {'web_url': 'https://example.test/mr/1'})
    w.remediation(session=session)
    session.post.assert_not_called()
    w.remediation(apply=True, session=session)
    assert session.post.call_count == 2
    assert session.post.call_args_list[0].kwargs['json']['start_sha'] == 'a'*40
    assert session.post.call_args_list[1].kwargs['json']['title'].startswith('Draft:')
    assert all(c.kwargs['timeout'] == 30 and not c.kwargs['allow_redirects'] for c in session.post.call_args_list)

def test_structured_request_and_transient_retry(workspace):
    w.consolidate()
    client = Mock()
    client.chat.completions.create.side_effect = [w.APIConnectionError(request=Mock()), SimpleNamespace(ok=True)]
    result = w.request_analysis.retry_with(wait=__import__('tenacity').wait_none())(client, w.load('analysis.json'))
    assert result.ok
    assert client.chat.completions.create.call_count == 2
    assert client.chat.completions.create.call_args.kwargs['response_format']['json_schema']['strict']

def test_offline_does_not_contact_openai(workspace, monkeypatch):
    w.consolidate()
    monkeypatch.setattr(w, 'OpenAI', Mock(side_effect=AssertionError('No paid API calls')))
    assert w.analyse(offline=True)['mode'] == 'offline'


def test_invalid_yaml_rejected():
    with pytest.raises(Exception): w.documents('apiVersion: [broken')
