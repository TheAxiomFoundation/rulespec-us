"""The diagnostic must retain failure status under Actions' implicit bash -e."""
import os
from pathlib import Path
import subprocess

import pytest
import yaml


@pytest.mark.parametrize('status', [0, 1, 124])
def test_fingerprint_exit_status_survives_errexit(tmp_path, status):
    workflow = yaml.safe_load(
        (Path(__file__).parents[1] / '.github/workflows/issue233-ch50-diagnostic.yml').read_text()
    )
    step = next(s for s in workflow['jobs']['diagnostic']['steps']
                if s['name'] == 'Protected single-module fingerprint (diagnostic only)')
    report = tmp_path / 'issue233-diagnostic'
    report.mkdir()
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    timeout = binaries / 'timeout'
    timeout.write_text(f'#!/bin/sh\necho diagnostic-stderr >&2\nexit {status}\n')
    timeout.chmod(0o755)
    # This regression tests shell status handling, not Linux /proc collection.
    observer = binaries / 'python'
    observer.write_text('#!/bin/sh\ncat >/dev/null\nexit 0\n')
    observer.chmod(0o755)
    env = dict(os.environ, RUNNER_TEMP=str(tmp_path), GITHUB_WORKSPACE=str(tmp_path))
    env['PATH'] = f'{binaries}:{env["PATH"]}'
    result = subprocess.run(['bash', '--noprofile', '--norc', '-eo', 'pipefail', '-c', step['run']],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == status
    assert (report / 'exit-code.txt').read_text().strip() == str(status)
    assert (report / 'stderr.log').read_text().strip() == 'diagnostic-stderr'
    assert (report / 'fingerprint.json').read_bytes() == b''


def observer_module():
    workflow = yaml.safe_load((Path(__file__).parents[1] / '.github/workflows/issue233-ch50-diagnostic.yml').read_text())
    step = next(s for s in workflow['jobs']['diagnostic']['steps'] if s['name'].startswith('Protected single-module'))
    code = step['run'].split("<<'OBSERVER' &\n")[1].split('\nOBSERVER')[0]
    namespace = {'__name__': 'observer_test'}
    exec(compile(code, '<workflow-observer>', 'exec'), namespace)
    return namespace


def proc_entry(root, pid, parent, start, children=(), thread=None):
    base = root / str(pid)
    base.mkdir(exist_ok=True)
    fields = ['S', str(parent)] + ['0'] * 17 + [str(start)]
    (base / 'stat').write_text(f'{pid} (worker) ' + ' '.join(fields))
    (base / 'io').write_text('read_bytes: 0')
    (base / 'wchan').write_text('0')
    task = base / 'task' / str(thread or pid)
    task.mkdir(parents=True, exist_ok=True)
    (task / 'children').write_text(' '.join(map(str, children)))


def test_observer_finds_worker_thread_child(tmp_path):
    m = observer_module()
    proc_entry(tmp_path, 10, 1, 100, [20], thread=11)
    proc_entry(tmp_path, 20, 10, 200)
    result = m['collect'](tmp_path, 10, '100')
    assert {p['pid'] for p in result['processes']} == {10, 20}
    assert not result['truncated']


def test_observer_rejects_queued_child_reused_by_other_parent(tmp_path):
    m = observer_module()
    proc_entry(tmp_path, 10, 1, 100, [20])
    proc_entry(tmp_path, 20, 99, 201)
    result = m['collect'](tmp_path, 10, '100')
    assert [p['pid'] for p in result['processes']] == [10]


def test_observer_rejects_parent_reuse_after_queueing(tmp_path):
    m = observer_module()
    proc_entry(tmp_path, 10, 1, 100, [20])
    proc_entry(tmp_path, 20, 10, 200)
    original = m['stat']
    def replaced_parent(proc, pid):
        if pid == 20:
            proc_entry(tmp_path, 10, 1, 101, [20])
        return original(proc, pid)
    m['stat'] = replaced_parent
    assert [p['pid'] for p in m['collect'](tmp_path, 10, '100')['processes']] == [10]


def test_observer_marks_thread_truncation(tmp_path):
    m = observer_module()
    proc_entry(tmp_path, 10, 1, 100)
    for tid in range(1000, 1129):
        (tmp_path / '10' / 'task' / str(tid)).mkdir()
    assert m['collect'](tmp_path, 10, '100')['truncated']
