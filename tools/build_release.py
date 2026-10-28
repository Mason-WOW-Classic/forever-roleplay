"""Build reproducible source bundles without local settings, keys or caches."""
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from provenance import MANIFEST, ROOT, digest, source_files, verify_archive, write_manifest


def build(path, entries):
    with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, source in sorted(entries):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, source.read_bytes(), compresslevel=9)
    count = verify_archive(path)
    print(f"{path.name}: {count} files, {path.stat().st_size} bytes, SHA256 {digest(path.read_bytes())}")


def main():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    write_manifest()
    files = source_files()
    build(dist / "ForeverRP-v0.5.zip",
          [("wow-rp/" + p.relative_to(ROOT).as_posix(), p) for p in files + [MANIFEST]])
    addon = ROOT / "addon" / "ForeverRP"
    build(dist / "ForeverRP-addon-v0.5.zip",
          [("ForeverRP/" + p.relative_to(addon).as_posix(), p)
           for p in files if p.is_relative_to(addon)])


if __name__ == "__main__":
    main()
