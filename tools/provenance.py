"""Inventory public source and verify bundles without extracting files."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "SOURCE-MANIFEST.json"
ROOT_FILES = {"README.md", "LICENSE", "Start.cmd", "Launch.ps1",
              "config.example.json", ".gitignore", ".gitattributes"}
SOURCE_DIRS = {"companion", "addon", "docs", "tests", "tools", ".github"}
SUFFIXES = {".py", ".lua", ".toc", ".md", ".yml", ".yaml"}


def source_files():
    """Explicit public file types; exclude settings, keys and caches."""
    files = [ROOT / name for name in ROOT_FILES if (ROOT / name).is_file()]
    for folder in SOURCE_DIRS:
        for path in (ROOT / folder).rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(ROOT)
            if any(part.startswith(".") and part != ".github" for part in relative.parts):
                continue
            if "__pycache__" in relative.parts:
                continue
            if path.name.lower() in {"settings.json", "key.txt"}:
                continue
            if (path.suffix in SUFFIXES or path.name == "LICENSE"
                    or (path.parent == ROOT / "docs" and path.name.startswith("openai-live-")
                        and path.suffix == ".json")):
                files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def manifest_bytes():
    records = []
    for path in source_files():
        data = path.read_bytes()
        records.append({"path": path.relative_to(ROOT).as_posix(),
                        "bytes": len(data), "sha256": digest(data)})
    return (json.dumps({"schema": 1, "project": "ForeverRP", "version": "0.5.0",
                        "files": records}, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def write_manifest():
    MANIFEST.write_bytes(manifest_bytes())


def check_manifest():
    expected = manifest_bytes()
    if not MANIFEST.is_file() or MANIFEST.read_bytes() != expected:
        raise ValueError("Source manifest is missing or stale; review changes before regenerating it")
    return json.loads(expected)


def verify_archive(path):
    manifest = check_manifest()
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP entries")
        if names and all(name.startswith("wow-rp/") for name in names):
            expected = {"wow-rp/" + row["path"]: row for row in manifest["files"]}
            expected["wow-rp/SOURCE-MANIFEST.json"] = {
                "bytes": MANIFEST.stat().st_size, "sha256": digest(MANIFEST.read_bytes())}
        elif names and all(name.startswith("ForeverRP/") for name in names):
            prefix = "addon/ForeverRP/"
            expected = {"ForeverRP/" + row["path"][len(prefix):]: row
                        for row in manifest["files"] if row["path"].startswith(prefix)}
        else:
            raise ValueError("Unknown bundle layout")
        if set(names) != set(expected):
            raise ValueError("ZIP file set does not match the source manifest")
        for name, row in expected.items():
            data = archive.read(name)
            if len(data) != row["bytes"] or digest(data) != row["sha256"]:
                raise ValueError("ZIP content mismatch: " + name)
    return len(names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--archive", type=Path)
    args = parser.parse_args()
    try:
        if args.archive:
            print(f"Verified {args.archive.name}: {verify_archive(args.archive)} files")
        elif args.check:
            print(f"Verified manifest: {len(check_manifest()['files'])} source files")
        else:
            write_manifest()
            print("Wrote SOURCE-MANIFEST.json")
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
