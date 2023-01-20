from typing import List, Tuple

import env
import pytest

import plumbum
from plumbum.commands import BaseCommand


@pytest.mark.xfail(env.WIN, reason="TODO: only fixed on posix systems")
@pytest.mark.timeout(3)
def test_draining_stderr(generate_cmd, process_cmd):
    stdout, stderr = get_output_with_iter_lines(
        generate_cmd | process_cmd | process_cmd
    )
    assert len(stderr) == 15000
    assert len(stdout) == 5000


@pytest.mark.xfail(env.WIN, reason="TODO: only fixed on posix systems")
@pytest.mark.timeout(3)
def test_draining_stderr_with_stderr_redirect(tmp_path, generate_cmd, process_cmd):
    stdout, stderr = get_output_with_iter_lines(
        generate_cmd | (process_cmd >= str(tmp_path / "output.txt")) | process_cmd
    )
    assert len(stderr) == 10000
    assert len(stdout) == 5000


@pytest.mark.xfail(env.WIN, reason="TODO: only fixed on posix systems")
@pytest.mark.timeout(3)
def test_draining_stderr_with_stdout_redirect(tmp_path, generate_cmd, process_cmd):
    stdout, stderr = get_output_with_iter_lines(
        generate_cmd | process_cmd | process_cmd > str(tmp_path / "output.txt")
    )
    assert len(stderr) == 15000
    assert len(stdout) == 0


@pytest.fixture()
def generate_cmd(tmp_path):
    generate = tmp_path / "generate.py"
    generate.write_text(
        """\
import sys
for i in range(5000):
    print("generated", i, file=sys.stderr)
    print(i)
"""
    )
    return plumbum.local["python"][generate]


@pytest.fixture()
def process_cmd(tmp_path):
    process = tmp_path / "process.py"
    process.write_text(
        """\
import sys
for line in sys.stdin:
    i = line.strip()
    print("consumed", i, file=sys.stderr)
    print(i)
"""
    )
    return plumbum.local["python"][process]


def get_output_with_iter_lines(cmd: BaseCommand) -> Tuple[List[str], List[str]]:
    stderr, stdout = [], []
    proc = cmd.popen()
    for stdout_line, stderr_line in proc.iter_lines(retcode=[0, None]):
        if stderr_line is not None:
            stderr.append(stderr_line)
        if stdout_line is not None:
            stdout.append(stdout_line)
    proc.wait()
    return stdout, stderr
