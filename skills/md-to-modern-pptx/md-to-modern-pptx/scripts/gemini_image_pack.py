from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import re


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'").strip('"')
        if k and k not in os.environ:
            os.environ[k] = v


def resolve_dotenv_path(cli_value: str | None) -> Path | None:
    if cli_value:
        return Path(cli_value)

    candidates: list[Path] = []

    # 1) Project-local (CWD)
    candidates.append(Path.cwd() / ".env")

    # 2) Skill-local (repo checkout): <skill_root>/.env
    try:
        skill_root = Path(__file__).resolve().parents[1]
        candidates.append(skill_root / ".env")
    except Exception:
        pass

    # 3) Global skills directory: %USERPROFILE%\.agents\skills\md-to-modern-pptx\.env
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        candidates.append(
            Path(userprofile)
            / ".agents"
            / "skills"
            / "md-to-modern-pptx"
            / ".env"
        )

    for c in candidates:
        if c.exists():
            return c

    return None


def strip_md(text: str) -> str:
    return text.replace("**", "").replace("`", "").strip()


def section_between(md: str, start_heading: str, end_heading_or_none: str | None) -> str:
    start = md.find(start_heading)
    if start < 0:
        return ""
    after = md[start + len(start_heading) :]
    if not end_heading_or_none:
        return after.strip()
    end = after.find(end_heading_or_none)
    if end < 0:
        return after.strip()
    return after[:end].strip()


def normalize_paragraphs(raw: str) -> str:
    lines = []
    for l in raw.splitlines():
        s = l.strip()
        if not s:
            continue
        if s.startswith("生成日期："):
            continue
        lines.append(s)
    return "\n".join(lines)


def parse_detailed_analysis(md: str) -> list[dict[str, str]]:
    raw = section_between(md, "## Detailed Analysis", "## Areas of Consensus")
    if not raw:
        return []
    blocks = [b.strip() for b in re.split(r"(?:^|\r?\n)###\s+", raw) if b.strip()]
    out: list[dict[str, str]] = []
    for b in blocks:
        lines = b.splitlines()
        title = strip_md(lines[0].strip())
        body = strip_md(normalize_paragraphs("\n".join(lines[1:])))
        out.append({"title": title, "body": body})
    return out


def theme_style_hint(theme_slug: str) -> str:
    slug = theme_slug.lower().strip()
    hints: dict[str, str] = {
        "golden-hour": "warm mustard yellow + terracotta + soft beige palette, cozy but premium",
        "tech-innovation": "high-contrast dark gray with electric blue and neon cyan accents, sleek modern",
        "ocean-depths": "deep navy + teal + seafoam palette, clean and trustworthy",
        "modern-minimalist": "neutral grayscale, minimal, lots of whitespace",
        "midnight-galaxy": "dark cosmic palette, subtle glow accents",
    }
    return hints.get(slug, "consistent palette matching the deck theme")


def prompt_template(
    *,
    deck_title: str,
    section_title: str,
    section_body: str,
    theme_slug: str,
) -> str:
    style = theme_style_hint(theme_slug)
    body_hint = section_body[:260].replace("\n", " ")
    return (
        "Create a modern editorial illustration for a presentation slide.\n"
        f"Topic: {deck_title}\n"
        f"Slide focus: {section_title}\n"
        f"Context: {body_hint}\n"
        f"Style: {style}; flat vector / editorial, subtle grain, clean shapes.\n"
        "Composition: subject centered, plenty of negative space around edges, 16:9 friendly.\n"
        "Constraints: no text, no captions, no logos, no watermarks, no brand marks.\n"
        "Quality: crisp, high detail, professional, not cartoonish.\n"
    )


@dataclass(frozen=True)
class PlanItem:
    name: str
    slide_number: int
    prompt: str
    size: str = "16:9"
    resolution: str = "1K"


def make_plan(md_path: Path, theme_slug: str, start_slide: int) -> dict[str, Any]:
    md = md_path.read_text(encoding="utf-8")
    deck_title = (next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), None) or "Deck").strip()
    analyses = parse_detailed_analysis(md)
    images: list[dict[str, Any]] = []

    for i, a in enumerate(analyses[:5]):
        slide_number = start_slide + i
        images.append(
            {
                "name": f"slide-{slide_number:02d}",
                "slide_number": slide_number,
                "size": "16:9",
                "resolution": "1K",
                "prompt": prompt_template(
                    deck_title=deck_title,
                    section_title=a["title"],
                    section_body=a["body"],
                    theme_slug=theme_slug,
                ),
            }
        )

    return {
        "version": 1,
        "theme": theme_slug,
        "model_hint": "gemini-3-pro-image-preview",
        "images": images,
    }


def _auth_headers(api_key: str) -> dict[str, str]:
    """
    Gateways differ on how they expect keys:
    - Authorization: Bearer <key>
    - X-Api-Key: <key>
    - X-Goog-Api-Key: <key> (common for Google-style)

    Default to sending all three to reduce config friction.
    """
    return {
        "Authorization": f"Bearer {api_key}",
        "X-Api-Key": api_key,
        "X-Goog-Api-Key": api_key,
    }


def _download_to(url: str, out_path: Path, api_key: str | None = None) -> None:
    headers = {}
    if api_key:
        headers.update(_auth_headers(api_key))
    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def generate_one(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    size: str,
    resolution: str,
    out_path: Path,
    poll_interval_s: float,
    timeout_s: float,
) -> None:
    base = _normalize_base_url(base_url)
    url = f"{base}/v1/images/generations"

    payload = {"model": model, "prompt": prompt, "n": 1, "size": size, "resolution": resolution}
    r = requests.post(url, headers=_auth_headers(api_key), json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()

    # Common patterns:
    # 1) Task-based gateway: { data: { task_id, status } }
    # 2) OpenAI-like: { data: [ { url } ] } or { data: [ { b64_json } ] }
    # 3) Provider-specific variations.
    def poll_task(task_id: str) -> None:
        task_url = f"{base}/v1/tasks/{task_id}"
        started = time.time()
        while True:
            if time.time() - started > timeout_s:
                raise TimeoutError(f"Task {task_id} timed out after {timeout_s}s")

            tr = requests.get(f"{task_url}?language=en", headers=_auth_headers(api_key), timeout=120)
            tr.raise_for_status()
            td = tr.json()
            status = (td.get("data") or {}).get("status")

            if status in ("success", "succeeded", "completed"):
                result = (td.get("data") or {}).get("result") or {}
                images = result.get("images") or []
                if not images:
                    raise RuntimeError(f"Task {task_id} success but result.images missing")

                first = images[0]
                urls = first.get("url") or first.get("urls") or []
                if not urls:
                    raise RuntimeError(f"Task {task_id} success but url missing")

                _download_to(str(urls[0]), out_path, api_key=None)
                return

            if status in ("failed", "error", "canceled", "cancelled"):
                raise RuntimeError(f"Task {task_id} failed: {td}")

            time.sleep(poll_interval_s)

    if isinstance(data, dict) and isinstance(data.get("data"), dict) and (data["data"].get("task_id") or data["data"].get("id")):
        poll_task(str(data["data"].get("task_id") or data["data"].get("id")))
        return

    if isinstance(data, dict) and isinstance(data.get("data"), list) and data["data"]:
        item = data["data"][0]
        if isinstance(item, dict) and (item.get("task_id") or item.get("id")):
            poll_task(str(item.get("task_id") or item.get("id")))
            return
        if isinstance(item, dict) and item.get("url"):
            _download_to(str(item["url"]), out_path, api_key=None)
            return
        if isinstance(item, dict) and item.get("b64_json"):
            import base64

            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(base64.b64decode(item["b64_json"]))
            return

    raise RuntimeError(f"Unrecognized response shape: {data}")


def main() -> None:
    p = argparse.ArgumentParser(description="Generate slide images via a Gemini gateway (base_url + key).")
    p.add_argument("--dotenv", default=None, help="Path to .env (optional; auto-detect if omitted)")

    sub = p.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("make-plan", help="Create an images plan JSON from a Deep Research markdown")
    p_plan.add_argument("--in", dest="md_in", required=True, help="Input markdown file")
    p_plan.add_argument("--theme", default="golden-hour", help="Theme slug (theme-factory)")
    p_plan.add_argument("--analysis-start-slide", type=int, default=5, help="First analysis slide number (default: 5)")
    p_plan.add_argument("--out", required=True, help="Output plan JSON path")

    p_gen = sub.add_parser("generate", help="Generate images from a plan JSON")
    p_gen.add_argument("--plan", required=True, help="Plan JSON path")
    p_gen.add_argument("--out-dir", default="images", help="Output directory (default: images/)")
    p_gen.add_argument("--base-url", default=None, help="Override GEMINI_BASE_URL")
    p_gen.add_argument("--key", default=None, help="Override GEMINI_API_KEY")
    p_gen.add_argument("--model", default=None, help="Override GEMINI_MODEL")
    p_gen.add_argument("--poll-interval", type=float, default=1.5)
    p_gen.add_argument("--timeout", type=float, default=180.0)
    p_gen.add_argument("--overwrite", action="store_true")

    args = p.parse_args()

    dotenv_path = resolve_dotenv_path(args.dotenv)
    if dotenv_path is not None:
        load_dotenv(dotenv_path)

    if args.cmd == "make-plan":
        plan = make_plan(Path(args.md_in), args.theme, args.analysis_start_slide)
        out_path = Path(args.out)
        out_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote plan: {out_path}")
        return

    if args.cmd == "generate":
        plan_path = Path(args.plan)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        base_url = args.base_url or os.getenv("GEMINI_BASE_URL") or ""
        api_key = args.key or os.getenv("GEMINI_API_KEY") or ""
        model = args.model or os.getenv("GEMINI_MODEL") or "gemini-3-pro-image-preview"

        if not base_url:
            raise SystemExit("Missing GEMINI_BASE_URL (set in .env or pass --base-url)")
        if not api_key:
            raise SystemExit("Missing GEMINI_API_KEY (set in .env or pass --key)")

        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        images = plan.get("images") or []
        if not isinstance(images, list) or not images:
            raise SystemExit("Plan has no images[]")

        for i, img in enumerate(images, start=1):
            item = PlanItem(
                name=str(img.get("name") or f"image-{i:02d}"),
                slide_number=int(img.get("slide_number") or 0),
                prompt=str(img.get("prompt") or ""),
                size=str(img.get("size") or "16:9"),
                resolution=str(img.get("resolution") or "1K"),
            )
            if not item.prompt.strip():
                raise SystemExit(f"Plan item {item.name} missing prompt")

            out_path = out_dir / f"{item.name}.png"
            if out_path.exists() and not args.overwrite:
                print(f"[skip] {out_path} exists")
                continue

            print(f"[{i}/{len(images)}] {item.name} (slide {item.slide_number})")
            generate_one(
                base_url=base_url,
                api_key=api_key,
                model=model,
                prompt=item.prompt,
                size=item.size,
                resolution=item.resolution,
                out_path=out_path,
                poll_interval_s=args.poll_interval,
                timeout_s=args.timeout,
            )
            print(f"  -> {out_path}")

        print("Done.")
        return


if __name__ == "__main__":
    main()
