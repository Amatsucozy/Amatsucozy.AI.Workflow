---
slug: sarif-uri-resolution
use-when: Resolving SARIF artifactLocation URIs to repo-relative file paths
domain: build-tooling
tags: [sarif, uri-parsing, windows-paths]
symptom: file paths in SARIF reports render as absolute paths or wrong drive letters
confidence: medium
date: 2026-02-01
source-task: adhoc-amtcz-mcp
---

# SARIF URI resolution

`uri_to_rel` calls `urlparse` and `unquote` on `file:` URIs and strips a
leading slash before a Windows drive letter (`/C:/...` becomes `C:/...`)
before computing a path relative to root.
