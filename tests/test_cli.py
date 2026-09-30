import io

import pytest

from defect_logger.cli import main


def run(path, *args):
    out, err = io.StringIO(), io.StringIO()
    code = main([args[0], "--file", str(path), *args[1:]], out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def start(path, size="40", batch="B-1"):
    return run(path, "start", "--batch-id", batch, "--sample-size", size)


def add(path, severity, desc="thing"):
    return run(path, "add", "--severity", severity, "--description", desc)


def test_full_flow_start_add_list_verdict(tmp_path):
    p = tmp_path / "i.json"
    assert start(p)[0] == 0
    assert add(p, "major", "cracked housing")[0] == 0
    assert add(p, "minor", "scuff")[0] == 0
    code, out, _ = run(p, "list")
    assert code == 0
    assert "1. [major] cracked housing" in out
    assert "2. [minor] scuff" in out
    code, out, _ = run(p, "verdict")
    assert code == 0 and "Verdict: ACCEPT" in out


def test_verdict_flips_to_reject_when_limit_exceeded(tmp_path):
    p = tmp_path / "i.json"
    start(p, "40")
    for _ in range(3):
        add(p, "major")
    assert "Verdict: ACCEPT" in run(p, "verdict")[1]
    add(p, "major")
    assert "Verdict: REJECT" in run(p, "verdict")[1]


def test_zero_defects_is_accept(tmp_path):
    p = tmp_path / "i.json"
    start(p)
    code, out, _ = run(p, "verdict")
    assert code == 0 and "Verdict: ACCEPT" in out
    assert "No defects recorded." in run(p, "list")[1]


def test_critical_rejects(tmp_path):
    p = tmp_path / "i.json"
    start(p, "60")
    add(p, "critical")
    assert "Verdict: REJECT" in run(p, "verdict")[1]


@pytest.mark.parametrize("size", ["0", "-3", "12.5", "abc", "", "4_0"])
def test_invalid_sample_size_reports_error_and_creates_nothing(tmp_path, size):
    p = tmp_path / "i.json"
    code, out, err = start(p, size)
    assert code == 1
    assert "Sample size" in err
    assert "Verdict" not in out
    assert not p.exists()


def test_bad_severity_and_empty_description_are_errors(tmp_path):
    p = tmp_path / "i.json"
    start(p)
    code, _, err = add(p, "urgent")
    assert code == 1 and "Severity" in err
    code, _, err = add(p, "minor", "  ")
    assert code == 1 and "Description" in err
    assert "No defects recorded." in run(p, "list")[1]


@pytest.mark.parametrize("cmd", [["list"], ["verdict"], ["add", "--severity", "minor", "--description", "x"]])
def test_commands_before_start_give_clear_error(tmp_path, cmd):
    code, _, err = run(tmp_path / "i.json", *cmd)
    assert code == 1 and "No inspection started" in err


def test_start_twice_refuses_unless_forced(tmp_path):
    p = tmp_path / "i.json"
    start(p, batch="OLD")
    add(p, "minor")
    code, _, err = start(p, batch="NEW")
    assert code == 1 and "--force" in err
    assert "OLD" in run(p, "verdict")[1]  # untouched
    assert run(p, "start", "--batch-id", "NEW", "--sample-size", "10", "--force")[0] == 0
    assert "NEW" in run(p, "verdict")[1]


def test_corrupt_file_does_not_crash(tmp_path):
    p = tmp_path / "i.json"
    p.write_text("garbage", encoding="utf-8")
    code, _, err = run(p, "verdict")
    assert code == 1 and "not valid JSON" in err


@pytest.mark.parametrize("size", ["0", "-5", "12.5", "ab"])
def test_invalid_sample_size_is_reported_even_if_inspection_exists(tmp_path, size):
    p = tmp_path / "i.json"
    start(p)
    code, _, err = start(p, size)
    assert code == 1
    assert "Sample size" in err
    assert "already exists" not in err


def test_force_start_replaces_a_corrupt_file(tmp_path):
    p = tmp_path / "i.json"
    p.write_text("garbage", encoding="utf-8")
    # Without --force the corrupt file is reported, not silently overwritten.
    assert start(p)[0] == 1
    code, _, _ = run(p, "start", "--batch-id", "B", "--sample-size", "40", "--force")
    assert code == 0
    assert "Verdict: ACCEPT" in run(p, "verdict")[1]