"""Validate candidate distributions against the checkout before release."""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def source_version(root: Path) -> str:
    tree = ast.parse((root / "unrooted/_version.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        ):
            return str(ast.literal_eval(node.value))
    raise ValueError("No literal __version__ in unrooted/_version.py")


def release_notes(root: Path, version: str) -> str:
    changelog = (root / "CHANGELOG.md").read_text()
    match = re.search(
        rf"^## {re.escape(version)}(?:\s|$).*?(?=^## |\Z)",
        changelog,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValueError(f"Missing changelog entry for {version}")
    return match.group().strip() + "\n"


def validate_artifacts(root: Path, dist: Path, tag: str | None = None) -> str:
    version = source_version(root)
    if tag is not None and tag != f"v{version}":
        raise ValueError(f"Tag {tag!r} does not match source version v{version}")
    release_notes(root, version)
    wheels = list(dist.glob("*.whl"))
    sdists = list(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError(
            "Expected exactly one wheel and one sdist in candidate directory"
        )
    if wheels[0].name != f"unrooted-{version}-py3-none-any.whl":
        raise ValueError("Unexpected wheel name/version")
    if sdists[0].name != f"unrooted-{version}.tar.gz":
        raise ValueError("Unexpected sdist name/version")
    with zipfile.ZipFile(wheels[0]) as archive:
        wheel = {name: archive.read(name) for name in archive.namelist()}
    prefix = f"unrooted-{version}/"
    with tarfile.open(sdists[0]) as archive:
        sdist = {}
        for member in archive.getmembers():
            if member.isfile():
                if not member.name.startswith(prefix):
                    raise ValueError("Unexpected sdist root")
                stream = archive.extractfile(member)
                assert stream is not None
                sdist[member.name.removeprefix(prefix)] = stream.read()
    info = f"unrooted-{version}.dist-info/"
    metadata = [
        BytesParser().parsebytes(data)
        for data in (wheel[info + "METADATA"], sdist["PKG-INFO"])
    ]
    for item in metadata:
        for key, expected in {
            "Name": "unrooted",
            "Version": version,
            "License-Expression": "MIT",
            "License-File": "LICENSE",
            "Requires-Python": ">=3.11",
            "Description-Content-Type": "text/markdown",
        }.items():
            if item[key] != expected:
                raise ValueError(f"Invalid {key}: {item[key]!r}; expected {expected!r}")
        if not item["Summary"] or not item["Maintainer"]:
            raise ValueError("Missing description or maintainer metadata")
        readme = item.get_payload(decode=True).decode("utf-8")
        if readme.strip() != (root / "README.md").read_text().strip():
            raise ValueError("Distribution README differs from checkout")
    if metadata[0].get_all("Requires-Dist") != metadata[1].get_all("Requires-Dist"):
        raise ValueError("Wheel and sdist dependency metadata disagree")
    license_text = (root / "LICENSE").read_bytes()
    if (
        wheel[info + "licenses/LICENSE"] != license_text
        or sdist["LICENSE"] != license_text
    ):
        raise ValueError("Missing or changed distribution license")
    for path in (root / "unrooted").rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(root).as_posix()
        expected = path.read_bytes()
        if wheel.get(relative) != expected or sdist.get(relative) != expected:
            raise ValueError(f"Missing or changed package file: {relative}")
        if expected.startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise ValueError(f"Unresolved LFS pointer: {relative}")
    for name in ("pyproject.toml", "CHANGELOG.md", "README.md"):
        if sdist.get(name) != (root / name).read_bytes():
            raise ValueError(f"Missing or changed sdist file: {name}")
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist", type=Path)
    parser.add_argument("--tag")
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--checksums", action="store_true")
    args = parser.parse_args()
    version = validate_artifacts(ROOT, args.dist, args.tag)
    if args.notes:
        args.notes.write_text(release_notes(ROOT, version))
    if args.checksums:
        artifacts = sorted([*args.dist.glob("*.whl"), *args.dist.glob("*.tar.gz")])
        (args.dist / "SHA256SUMS").write_text(
            "".join(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
                for path in artifacts
            )
        )
    print(
        f"Validated unrooted {version}: metadata, version, license, and package files."
    )


if __name__ == "__main__":
    main()
