"""Release gates must reject incomplete or mismatched candidate artifacts."""

from __future__ import annotations

import runpy
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RELEASE = runpy.run_path(str(ROOT / "tools/release/validate.py"))
VERSION = RELEASE["source_version"](ROOT)


@pytest.fixture(scope="module")
def built_candidate(tmp_path_factory):
    dist = tmp_path_factory.mktemp("candidate-build")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "hatchling",
            "build",
            "-t",
            "sdist",
            "-t",
            "wheel",
            "-d",
            str(dist),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return dist


@pytest.fixture
def candidate(built_candidate, tmp_path):
    dist = tmp_path / "dist"
    shutil.copytree(built_candidate, dist)
    return dist


def test_complete_candidate_matches_checkout(candidate):
    assert RELEASE["validate_artifacts"](ROOT, candidate, f"v{VERSION}") == VERSION
    assert "Known limitations" in RELEASE["release_notes"](ROOT, VERSION)


def test_mismatched_tag_is_rejected(candidate):
    with pytest.raises(ValueError, match="does not match"):
        RELEASE["validate_artifacts"](ROOT, candidate, "v9.9.9")


def test_stale_candidate_is_rejected(candidate):
    wheel = next(candidate.glob("*.whl"))
    shutil.copyfile(wheel, candidate / "stale.whl")
    with pytest.raises(ValueError, match="exactly one"):
        RELEASE["validate_artifacts"](ROOT, candidate)


@pytest.mark.parametrize(
    "member",
    [
        "unrooted/resources/odd/colors.json",
        f"unrooted-{VERSION}.dist-info/licenses/LICENSE",
    ],
)
def test_changed_asset_or_license_is_rejected(candidate, member):
    wheel = next(candidate.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    files[member] = b"changed"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with pytest.raises(ValueError, match="changed"):
        RELEASE["validate_artifacts"](ROOT, candidate)


def test_missing_changelog_entry_is_rejected():
    with pytest.raises(ValueError, match="Missing changelog"):
        RELEASE["release_notes"](ROOT, "9.9.9")
