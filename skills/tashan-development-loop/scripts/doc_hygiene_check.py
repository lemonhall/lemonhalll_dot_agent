#!/usr/bin/env python3
"""
Doc Hygiene Check (PRD / plan alignment)

Checks:
1) Fuzzy terms in Markdown (discouraged phrases).
2) Traceability chain: PRD Req IDs referenced by plan docs.
3) Plan docs have a PRD Trace section (or are explicitly marked as infra/debt).

Exit code:
  0 - no issues
  1 - issues found
  2 - invalid usage / unexpected error
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import re
import sys
from pathlib import Path


REQ_ID_RE = re.compile(r"\bREQ-\d{3}\b")


DEFAULT_FUZZY_TERMS = [
    # vague quality / hand-wavy acceptance
    "差不多",
    "尽量",
    "优化一下",
    "提升一下",
    "应该没问题",
    "看起来不错",
    "跑起来不崩",
    # scope escapes
    "后面再说",
    "先写着",
    "先随便",
]


@dataclasses.dataclass(frozen=True)
class Finding:
    kind: str
    path: Path
    line_no: int
    message: str


def _iter_md_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.lower().endswith(".md"):
                files.append(Path(dirpath) / name)
    return sorted(files)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _find_fuzzy_terms_in_file(path: Path, terms: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    lines = _read_text(path).splitlines()
    for idx, line in enumerate(lines, start=1):
        for term in terms:
            if term and term in line:
                findings.append(
                    Finding(
                        kind="fuzzy-term",
                        path=path,
                        line_no=idx,
                        message=f"Found fuzzy term: {term}",
                    )
                )
    return findings


def _collect_req_ids(md_files: list[Path]) -> set[str]:
    ids: set[str] = set()
    for path in md_files:
        ids.update(REQ_ID_RE.findall(_read_text(path)))
    return ids


def _plan_has_prd_trace(path: Path) -> bool:
    text = _read_text(path)
    # Simple heuristics:
    # - contains "PRD Trace" OR "Req ID" OR explicit opt-out keywords
    if re.search(r"\bPRD\s*Trace\b", text, flags=re.IGNORECASE):
        return True
    if "Req ID" in text or "REQ-" in text:
        return True
    if re.search(r"\b(infra|infrastructure|debt|tech\s*debt)\b", text, flags=re.IGNORECASE):
        return True
    if "基础设施" in text or "偿债" in text:
        return True
    return False


def _print_findings(findings: list[Finding]) -> None:
    for f in findings:
        rel = f.path.as_posix()
        print(f"[{f.kind}] {rel}:{f.line_no} {f.message}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Doc hygiene check for PRD/plan alignment.")
    parser.add_argument("--root", default=".", help="Repository root (default: .)")
    parser.add_argument("--prd-dir", default="docs/prd", help="PRD directory (default: docs/prd)")
    parser.add_argument("--plan-dir", default="docs/plan", help="Plan directory (default: docs/plan)")
    parser.add_argument(
        "--fuzzy-terms",
        default="",
        help="Comma-separated extra fuzzy terms (optional).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if PRD or plan dirs are missing (default: warn only).",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    prd_dir = (root / args.prd_dir).resolve()
    plan_dir = (root / args.plan_dir).resolve()

    findings: list[Finding] = []

    # Fuzzy terms scan (all markdown under root by default)
    terms = list(DEFAULT_FUZZY_TERMS)
    if args.fuzzy_terms.strip():
        terms.extend([t.strip() for t in args.fuzzy_terms.split(",") if t.strip()])

    md_files = _iter_md_files(root)
    for path in md_files:
        findings.extend(_find_fuzzy_terms_in_file(path, terms))

    # Traceability checks
    prd_exists = prd_dir.exists() and prd_dir.is_dir()
    plan_exists = plan_dir.exists() and plan_dir.is_dir()

    if not prd_exists:
        msg = f"PRD dir missing: {prd_dir}"
        if args.strict:
            findings.append(Finding(kind="missing-prd-dir", path=prd_dir, line_no=1, message=msg))
        else:
            print(f"[warn] {msg}")

    if not plan_exists:
        msg = f"Plan dir missing: {plan_dir}"
        if args.strict:
            findings.append(Finding(kind="missing-plan-dir", path=plan_dir, line_no=1, message=msg))
        else:
            print(f"[warn] {msg}")

    prd_ids: set[str] = set()
    plan_ids: set[str] = set()

    if prd_exists:
        prd_files = _iter_md_files(prd_dir)
        prd_ids = _collect_req_ids(prd_files)
        if not prd_ids:
            findings.append(
                Finding(
                    kind="no-req-ids",
                    path=prd_dir,
                    line_no=1,
                    message="No REQ-### IDs found in PRD docs. Add Req IDs for traceability.",
                )
            )

    if plan_exists:
        plan_files = _iter_md_files(plan_dir)
        plan_ids = _collect_req_ids(plan_files)
        for path in plan_files:
            # Skip index-only? Still should have trace info.
            if not _plan_has_prd_trace(path):
                findings.append(
                    Finding(
                        kind="missing-prd-trace",
                        path=path,
                        line_no=1,
                        message='Plan doc lacks PRD Trace (expected "PRD Trace" / Req IDs / explicit infra/debt note).',
                    )
                )

    if prd_ids and plan_exists:
        missing = sorted(prd_ids - plan_ids)
        for req_id in missing:
            findings.append(
                Finding(
                    kind="req-unreferenced",
                    path=plan_dir,
                    line_no=1,
                    message=f"Req ID not referenced by any plan doc: {req_id}",
                )
            )

    # Output
    if findings:
        _print_findings(findings)
        return 1

    print("OK: no doc hygiene issues found.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(2)
    except Exception as exc:
        print(f"[error] unexpected failure: {exc}", file=sys.stderr)
        raise SystemExit(2)

