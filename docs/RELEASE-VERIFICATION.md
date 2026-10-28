# Verify source and source bundles

The public repository contains readable source and synthetic tests. key.txt, settings.json, .env files, caches, local Git metadata and old build archives are excluded from publication. Only this project's directory is published.

SOURCE-MANIFEST.json lists the relative path, byte length and SHA-256 of the intended project source files. It excludes itself to avoid a circular hash. Commit IDs and tags identify the repository revision; the manifest identifies source bytes within that revision.

From a trusted checkout of the published tag:

```powershell
python tools/provenance.py --check
python -m unittest discover -s tests -v
python tools/build_release.py
python tools/provenance.py --archive dist/ForeverRP-v0.5.zip
python tools/provenance.py --archive dist/ForeverRP-addon-v0.5.zip
```

The Lua tests need the optional developer package Lupa 2.8. The installed addon and companion do not depend on it. Without Lupa, the test runner explicitly skips the Lua simulations; it must not be described as a full 72-check execution.

The archive verifier checks the exact expected file set and each file's SHA-256 against the checkout manifest, including MIT license notices. The full source bundle also embeds that manifest. ZIP entries use fixed timestamps and permissions; compression-library differences can still change the archive's overall hash, so file-by-file verification is the portable check.

Build output prints each ZIP's SHA-256. Record that hash for a particular downloaded archive. A checksum copied from an untrusted source does not authenticate that source, and matching files do not establish policy approval or account behavior.
