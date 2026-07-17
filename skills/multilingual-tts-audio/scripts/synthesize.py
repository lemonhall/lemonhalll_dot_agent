#!/usr/bin/env python3
"""Generate validated multilingual MP3 files with edge-tts."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import edge_tts


MIN_AUDIO_BYTES = 1024
DEFAULT_RATE = "+0%"
DEFAULT_VOLUME = "+0%"
DEFAULT_PITCH = "+0Hz"


class TtsError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate local multilingual MP3 files with validation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    voices = subparsers.add_parser("voices", help="List current Edge TTS voices.")
    voices.add_argument("--language", help="Exact locale, for example ja-JP.")
    voices.add_argument("--gender", choices=("Female", "Male"))
    voices.add_argument("--proxy")
    voices.add_argument("--retries", type=int, default=3)

    synthesize = subparsers.add_parser(
        "synthesize", help="Generate one file or a JSON manifest."
    )
    source = synthesize.add_mutually_exclusive_group(required=True)
    source.add_argument("--text-file", type=Path)
    source.add_argument("--manifest", type=Path)
    synthesize.add_argument("--output", type=Path)
    synthesize.add_argument("--voice")
    synthesize.add_argument("--language")
    synthesize.add_argument("--gender", choices=("Female", "Male"))
    synthesize.add_argument("--rate", default=DEFAULT_RATE)
    synthesize.add_argument("--volume", default=DEFAULT_VOLUME)
    synthesize.add_argument("--pitch", default=DEFAULT_PITCH)
    synthesize.add_argument("--proxy")
    synthesize.add_argument("--overwrite", action="store_true")
    synthesize.add_argument("--retries", type=int, default=3)
    synthesize.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Maximum concurrent synthesis jobs for manifest mode (default: 1).",
    )
    synthesize.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Finish the manifest and report failed items instead of stopping at the first failure.",
    )
    synthesize.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Write manifest progress to stderr every N completed items (default: 100).",
    )
    synthesize.add_argument("--report", type=Path, help="Write detailed JSON results to this path.")
    return parser


def effective_proxy(explicit: str | None) -> str | None:
    return explicit or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")


async def get_voices(proxy: str | None, retries: int) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await edge_tts.list_voices(proxy=proxy)
        except Exception as error:  # Service and transport errors vary by version.
            last_error = error
            if attempt < retries:
                await asyncio.sleep(2 ** (attempt - 1))
    raise TtsError(f"Voice discovery failed after {retries} attempts: {last_error}")


def filter_voices(
    voices: list[dict[str, Any]],
    language: str | None,
    gender: str | None,
) -> list[dict[str, Any]]:
    selected = voices
    if language:
        selected = [v for v in selected if v.get("Locale", "").lower() == language.lower()]
    if gender:
        selected = [v for v in selected if v.get("Gender") == gender]
    return sorted(selected, key=lambda item: item.get("ShortName", ""))


def read_utf8(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig").strip()
    except UnicodeDecodeError as error:
        raise TtsError(f"Text file is not valid UTF-8: {path}") from error
    if not text:
        raise TtsError(f"Text file is empty: {path}")
    return text


def resolve_path(value: str | Path, base: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def fingerprint(text: str, config: dict[str, str]) -> str:
    payload = json.dumps(
        {"text": text, **config}, ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def metadata_path(output: Path) -> Path:
    return output.with_suffix(output.suffix + ".tts.json")


def is_valid_audio(output: Path) -> bool:
    return output.is_file() and output.stat().st_size > MIN_AUDIO_BYTES


def matching_existing(output: Path, expected_fingerprint: str) -> bool:
    sidecar = metadata_path(output)
    if not is_valid_audio(output) or not sidecar.is_file():
        return False
    try:
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return metadata.get("fingerprint") == expected_fingerprint


def probe_audio(output: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"bytes": output.stat().st_size}
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        result["ffprobe"] = "unavailable"
        return result

    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise TtsError(f"ffprobe rejected {output}: {completed.stderr.strip()}")
    result["duration_seconds"] = round(float(completed.stdout.strip()), 3)
    return result


async def choose_voice(
    item: dict[str, Any],
    voices: list[dict[str, Any]],
) -> str:
    if item.get("voice"):
        return str(item["voice"])

    language = item.get("language")
    if not language:
        raise TtsError("Each item needs either voice or language.")
    candidates = filter_voices(voices, str(language), item.get("gender"))
    if not candidates:
        raise TtsError(
            f"No voice found for language={language!r}, gender={item.get('gender')!r}. "
            "Run the voices command to inspect current choices."
        )
    return str(candidates[0]["ShortName"])


async def generate_one(
    item: dict[str, Any],
    base: Path,
    voices: list[dict[str, Any]],
    proxy: str | None,
    overwrite: bool,
    retries: int,
) -> dict[str, Any]:
    output = resolve_path(item["output"], base)
    if output.suffix.lower() != ".mp3":
        raise TtsError(f"Output must use the .mp3 extension: {output}")

    has_inline_text = "text" in item
    has_text_file = "text_file" in item
    if has_inline_text == has_text_file:
        raise TtsError("Each item requires exactly one of text or text_file.")
    if has_inline_text:
        text = item["text"]
        if not isinstance(text, str) or not text:
            raise TtsError("Inline text must be a non-empty string.")
        source = "manifest:inline"
    else:
        text_file = resolve_path(item["text_file"], base)
        text = read_utf8(text_file)
        source = str(text_file)

    voice = await choose_voice(item, voices)
    config = {
        "voice": voice,
        "rate": str(item.get("rate", DEFAULT_RATE)),
        "volume": str(item.get("volume", DEFAULT_VOLUME)),
        "pitch": str(item.get("pitch", DEFAULT_PITCH)),
    }
    expected_fingerprint = fingerprint(text, config)

    if matching_existing(output, expected_fingerprint):
        return {"status": "skipped", "output": str(output), "voice": voice, **probe_audio(output)}
    if output.exists() and not overwrite:
        raise TtsError(
            f"Output exists with a different or missing fingerprint: {output}. "
            "Use --overwrite to replace it."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f"{output.name}.part-{os.getpid()}")
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            communicate = edge_tts.Communicate(text=text, proxy=proxy, **config)
            await communicate.save(str(temporary))
            if not is_valid_audio(temporary):
                raise TtsError(f"Generated audio is too small: {temporary}")
            probe_audio(temporary)
            os.replace(temporary, output)
            metadata = {
                "fingerprint": expected_fingerprint,
                "source": source,
                **config,
            }
            sidecar = metadata_path(output)
            temporary_sidecar = sidecar.with_name(f"{sidecar.name}.part-{os.getpid()}")
            temporary_sidecar.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            os.replace(temporary_sidecar, sidecar)
            return {"status": "generated", "output": str(output), "voice": voice, **probe_audio(output)}
        except Exception as error:  # Network and codec failures vary by edge-tts version.
            last_error = error
            if temporary.exists():
                temporary.unlink()
            if attempt < retries:
                await asyncio.sleep(2 ** (attempt - 1))

    raise TtsError(f"Failed after {retries} attempts for {output}: {last_error}")


def manifest_items(path: Path) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    manifest_path = path.expanduser().resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    defaults = data.get("defaults", {})
    raw_items = data.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise TtsError("Manifest must contain a non-empty items array.")
    items = [{**defaults, **item} for item in raw_items]
    base_dir = resolve_path(data.get("base_dir", "."), manifest_path.parent)
    return base_dir, items, data


async def run(args: argparse.Namespace) -> int:
    proxy = effective_proxy(args.proxy)
    voices = await get_voices(proxy, args.retries)

    if args.command == "voices":
        selected = filter_voices(voices, args.language, args.gender)
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return 0 if selected else 2

    if args.manifest:
        base, items, manifest = manifest_items(args.manifest)
        overwrite = args.overwrite or bool(manifest.get("overwrite", False))
    else:
        if not args.output:
            raise TtsError("--output is required with --text-file.")
        base = Path.cwd()
        items = [{
            "text_file": str(args.text_file),
            "output": str(args.output),
            "voice": args.voice,
            "language": args.language,
            "gender": args.gender,
            "rate": args.rate,
            "volume": args.volume,
            "pitch": args.pitch,
        }]
        overwrite = args.overwrite

    outputs: set[Path] = set()
    for item in items:
        if "output" not in item:
            raise TtsError("Each item requires output.")
        output = resolve_path(item["output"], base)
        if output in outputs:
            raise TtsError(f"Manifest contains a duplicate output: {output}")
        outputs.add(output)

    semaphore = asyncio.Semaphore(args.jobs)

    async def generate_limited(index: int, item: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        async with semaphore:
            try:
                result = await generate_one(item, base, voices, proxy, overwrite, args.retries)
            except Exception as error:
                if not args.continue_on_error:
                    raise
                result = {
                    "status": "failed",
                    "output": str(resolve_path(item["output"], base)),
                    "error": str(error),
                }
            return index, result

    tasks = [
        asyncio.create_task(generate_limited(index, item))
        for index, item in enumerate(items)
    ]
    ordered_results: list[dict[str, Any] | None] = [None] * len(items)
    counts = {"generated": 0, "skipped": 0, "failed": 0}
    completed_count = 0
    for completed in asyncio.as_completed(tasks):
        index, result = await completed
        ordered_results[index] = result
        status = str(result["status"])
        counts[status] = counts.get(status, 0) + 1
        completed_count += 1
        if completed_count % args.progress_every == 0 or completed_count == len(items):
            print(
                f"progress: {completed_count}/{len(items)} "
                f"generated={counts['generated']} skipped={counts['skipped']} failed={counts['failed']}",
                file=sys.stderr,
                flush=True,
            )

    results = [result for result in ordered_results if result is not None]
    summary = {"total": len(results), **counts}
    if args.report:
        report = args.report.expanduser().resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        temporary_report = report.with_name(f"{report.name}.part-{os.getpid()}")
        temporary_report.write_text(
            json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary_report, report)
        print(json.dumps({"summary": summary, "report": str(report)}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if counts["failed"] else 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "retries", 1) < 1:
        parser.error("--retries must be at least 1")
    if getattr(args, "jobs", 1) < 1 or getattr(args, "jobs", 1) > 32:
        parser.error("--jobs must be between 1 and 32")
    if getattr(args, "progress_every", 1) < 1:
        parser.error("--progress-every must be at least 1")
    try:
        return asyncio.run(run(args))
    except (TtsError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
