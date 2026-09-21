"""Verify the publishable DeltaLayer release surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
BANNED = (
    "qicetai",
    "db-gpt",
    "agentscope",
    "deepseek",
    "brave",
    "tavily",
    "cdb6799",
    "8a7a10",
    "source_session",
    "source_path",
    "C:\\Users\\",
    "/Users/",
    "/home/",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    corpus_path = EXPERIMENTS / "public-deltas.jsonl"
    lines = [line for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(lines) == 48, f"Expected 48 public deltas, got {len(lines)}")
    records = [json.loads(line) for line in lines]
    ids = [record.get("id") for record in records]
    require(ids == [f"delta-{index:03d}" for index in range(1, 49)], "Invalid public ids")
    require(all(record.get("source") == "agent" for record in records), "Unexpected source label")
    require(all(isinstance(record.get("changes"), list) for record in records), "Invalid changes")

    corpus_text = corpus_path.read_text(encoding="utf-8").rstrip("\n")
    metrics = read_json(EXPERIMENTS / "public-corpus-metrics.json")
    require(metrics["task_count"] == 48, "Public metric task count mismatch")
    require(metrics["public_jsonl_chars"] == len(corpus_text), "Public char count mismatch")
    require(metrics["public_jsonl_utf8_bytes"] == len(corpus_text.encode("utf-8")), "Public byte count mismatch")
    require(
        metrics["public_corpus_sha256"] == hashlib.sha256(corpus_text.encode("utf-8")).hexdigest(),
        "Public corpus hash mismatch",
    )
    require(read_json(EXPERIMENTS / "h5-summary.json")["h5_status"] == "PARTIALLY_SUPPORTED", "H5 conclusion changed")
    provenance = read_json(EXPERIMENTS / "public-provenance.json")
    require([item["id"] for item in provenance] == ids, "Public provenance mismatch")

    checked_files = [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and "qct-v0" not in path.parts
        and path.name != "verify_release.py"
    ]
    for path in checked_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        require(not any(term.lower() in lowered for term in BANNED), f"Private marker in {path.relative_to(ROOT)}")
        require("\ufffd" not in text, f"Replacement character in {path.relative_to(ROOT)}")
        if path.suffix.lower() in {".md", ".json", ".jsonl", ".py", ".ps1"}:
            require(
                not re.search(r"(?i)(api[_-]?key|password|secret|bearer\s+[A-Za-z0-9._-]{12,})", text),
                f"Credential marker in {path.relative_to(ROOT)}",
            )

    link_count = 0
    for page in [
        path for path in ROOT.rglob("*.md")
        if "__pycache__" not in path.parts and "qct-v0" not in path.parts
    ]:
        content = re.sub(r"```.*?```", "", page.read_text(encoding="utf-8"), flags=re.S)
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("#"):
                continue
            local = (page.parent / unquote(target.split("#", 1)[0])).resolve()
            require(local.is_relative_to(ROOT), f"External local link: {page}: {target}")
            require(local.exists(), f"Broken link: {page}: {target}")
            link_count += 1

    print(f"PASS: public corpus 48 records; {link_count} local links; H5 PARTIALLY_SUPPORTED.")
    print(f"PASS: {metrics['public_jsonl_chars']} public JSONL characters; private markers absent.")
    print("LIMIT: source-corpus measurements remain historical metadata; raw sessions and source checkout are excluded.")


if __name__ == "__main__":
    main()
