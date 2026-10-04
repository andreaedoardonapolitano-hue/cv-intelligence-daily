#!/usr/bin/env python3
"""Genera gli episodi di CV Intelligence Daily.

Per ogni script in scripts/AAAA-MM-GG.md non ancora pubblicato:
  1. pulisce il testo per la sintesi vocale,
  2. lo manda a ElevenLabs a blocchi e unisce l'audio in un MP3,
  3. aggiorna episodes.json e il feed RSS in docs/feed.xml.

Uso:
  python tools/build_episode.py            # usa l'API ElevenLabs (serve ELEVENLABS_API_KEY)
  python tools/build_episode.py --dry-run  # audio muto di prova, nessuna chiamata API
  Il servizio vocale (google o elevenlabs) si sceglie con tts_provider in podcast.json.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
BUILD_DIR = ROOT / "build"
DOCS_DIR = ROOT / "docs"
EPISODES_FILE = ROOT / "episodes.json"
CONFIG_FILE = ROOT / "podcast.json"
SOURCES_MARKER = "===FONTI==="
CHUNK_LIMIT = 2400  # caratteri per richiesta: margine ampio sotto i limiti del modello
TZ = ZoneInfo("Europe/Rome")


# ---------------------------------------------------------------- parsing

def parse_script(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = raw
    if raw.startswith("---"):
        _, front, body = raw.split("---", 2)
        for line in front.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip('"')
    spoken, _, sources = body.partition(SOURCES_MARKER)
    date = meta.get("date") or path.stem
    return {
        "date": date,
        "title": meta.get("title", f"CV Intelligence Daily – {date}"),
        "description": meta.get("description", ""),
        "spoken": spoken.strip(),
        "sources": parse_sources(sources),
    }


def parse_sources(block: str) -> list[dict]:
    items = []
    for match in re.finditer(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", block):
        items.append({"title": match.group(1).strip(), "url": match.group(2).strip()})
    return items


def clean_for_speech(text: str) -> str:
    """Toglie tutto ciò che non va letto e rende il testo pronunciabile."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\[[^\]]*\](?!\()", "", text)              # [regia]
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)       # [testo](link)
    text = re.sub(r"[*_`]+", "", text)                         # grassetti, corsivi
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or set(line) <= {"-", "=", "|"}:
            lines.append("")
            continue
        heading = line.startswith("#")
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^[-•]\s+", "", line)
        if heading or not line.endswith((".", "!", "?", ":", ";", ",")):
            if not line.endswith((".", "!", "?")):
                line += "."
        lines.append(line)
    paragraphs = re.split(r"\n\s*\n", "\n".join(lines))
    paragraphs = [" ".join(p.split()) for p in paragraphs if p.strip()]
    return "\n\n".join(paragraphs)


def chunk_text(text: str, limit: int = CHUNK_LIMIT) -> list[str]:
    chunks: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        pieces = [para]
        if len(para) > limit:  # paragrafo lunghissimo: spezza per frasi
            pieces = re.split(r"(?<=[.!?])\s+", para)
        for piece in pieces:
            candidate = f"{current}\n\n{piece}" if current else piece
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = piece
    if current:
        chunks.append(current)
    return chunks


# ---------------------------------------------------------------- audio

def synthesize(chunks: list[str], cfg: dict, out_dir: Path, dry_run: bool) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = cfg.get("tts_provider", "elevenlabs")
    el = cfg.get("elevenlabs", {})
    files = []
    for i, chunk in enumerate(chunks):
        target = out_dir / f"part_{i:03d}.mp3"
        if dry_run:
            seconds = max(1.0, len(chunk) / 15.0)  # ~15 caratteri al secondo
            run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                 "anullsrc=r=44100:cl=mono", "-t", f"{seconds:.1f}",
                 "-b:a", "64k", str(target)])
        elif provider == "google":
            target.write_bytes(call_google(chunk, cfg["google"]))
        else:
            payload = {
                "text": chunk,
                "model_id": el["model_id"],
                "voice_settings": el["voice_settings"],
                "previous_text": chunks[i - 1][-600:] if i > 0 else None,
                "next_text": chunks[i + 1][:600] if i + 1 < len(chunks) else None,
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            target.write_bytes(call_elevenlabs(payload, el))
        files.append(target)
        print(f"  blocco {i + 1}/{len(chunks)} pronto ({len(chunk)} caratteri)")
    return files


def call_elevenlabs(payload: dict, el: dict) -> bytes:
    if "DA_COMPILARE" in el["voice_id"]:
        sys.exit("voice_id non impostato in podcast.json.")
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY mancante: aggiungila nei secrets del repository.")
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{el['voice_id']}"
           f"?output_format={el['output_format']}")
    for attempt in range(1, 5):
        resp = requests.post(url, json=payload, timeout=180,
                             headers={"xi-api-key": key, "Accept": "audio/mpeg"})
        if resp.ok:
            return resp.content
        print(f"  ElevenLabs ha risposto {resp.status_code}: {resp.text[:300]}")
        if resp.status_code in (401, 402, 403, 404, 422):
            sys.exit("Errore non recuperabile da ElevenLabs (chiave, credito o voice_id).")
        time.sleep(10 * attempt)
    sys.exit("ElevenLabs non risponde dopo 4 tentativi.")


def call_google(text: str, g: dict) -> bytes:
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        sys.exit("GOOGLE_TTS_API_KEY mancante: aggiungila nei secrets del repository.")
    body = {
        "input": {"text": text},
        "voice": {"languageCode": g["language_code"], "name": g["voice_name"]},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": g.get("speaking_rate", 1.0)},
    }
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    for attempt in range(1, 5):
        resp = requests.post(url, params={"key": key}, json=body, timeout=180)
        if resp.ok:
            return base64.b64decode(resp.json()["audioContent"])
        print(f"  Google TTS ha risposto {resp.status_code}: {resp.text[:300]}")
        if resp.status_code in (400, 401, 403, 404):
            sys.exit("Errore non recuperabile da Google TTS (chiave, API non attiva o voce errata).")
        time.sleep(10 * attempt)
    sys.exit("Google TTS non risponde dopo 4 tentativi.")


def concat(parts: list[Path], target: Path) -> None:
    listing = target.with_suffix(".txt")
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", str(target)])
    listing.unlink()


def duration_seconds(path: Path) -> int:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return round(float(out.strip()))


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


# ---------------------------------------------------------------- feed

def audio_url(date: str) -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "OWNER/cv-intelligence-daily")
    return f"https://github.com/{repo}/releases/download/ep-{date}/cvid-{date}.mp3"


def episode_html(ep: dict) -> str:
    parts = [f"<p>{html.escape(ep['description'])}</p>"] if ep["description"] else []
    if ep["sources"]:
        items = "".join(f'<li><a href="{html.escape(s["url"])}">{html.escape(s["title"])}</a></li>'
                        for s in ep["sources"])
        parts.append(f"<p>Fonti:</p><ul>{items}</ul>")
    parts.append("<p>Voce sintetica generata con AI. Contenuti basati su fonti pubbliche.</p>")
    return "".join(parts)


def hhmmss(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def write_feed(cfg: dict, episodes: list[dict]) -> None:
    e = html.escape
    site = cfg["site_url"].rstrip("/")
    items = []
    for ep in sorted(episodes, key=lambda x: x["date"], reverse=True):
        items.append(f"""    <item>
      <title>{e(ep['title'])}</title>
      <description><![CDATA[{episode_html(ep)}]]></description>
      <enclosure url="{e(ep['url'])}" length="{ep['bytes']}" type="audio/mpeg"/>
      <guid isPermaLink="false">cvid-{ep['date']}</guid>
      <pubDate>{ep['pub_date']}</pubDate>
      <itunes:duration>{hhmmss(ep['seconds'])}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{e(cfg['title'])}</title>
    <link>{e(site)}/</link>
    <atom:link href="{e(site)}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>{e(cfg['language'])}</language>
    <description>{e(cfg['description'])}</description>
    <itunes:subtitle>{e(cfg['subtitle'])}</itunes:subtitle>
    <itunes:summary>{e(cfg['description'])}</itunes:summary>
    <itunes:author>{e(cfg['author'])}</itunes:author>
    <itunes:owner>
      <itunes:name>{e(cfg['owner_name'])}</itunes:name>
      <itunes:email>{e(cfg['owner_email'])}</itunes:email>
    </itunes:owner>
    <itunes:image href="{e(site)}/cover.jpg"/>
    <image><url>{e(site)}/cover.jpg</url><title>{e(cfg['title'])}</title><link>{e(site)}/</link></image>
    <itunes:category text="{e(cfg['category'])}"><itunes:category text="{e(cfg['subcategory'])}"/></itunes:category>
    <itunes:explicit>{'true' if cfg['explicit'] else 'false'}</itunes:explicit>
    <itunes:type>episodic</itunes:type>
{chr(10).join(items)}
  </channel>
</rss>
"""
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "feed.xml").write_text(feed, encoding="utf-8")


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="audio muto, nessuna chiamata API")
    parser.add_argument("--feed-only", action="store_true", help="rigenera solo il feed")
    args = parser.parse_args()

    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    episodes = json.loads(EPISODES_FILE.read_text(encoding="utf-8")) if EPISODES_FILE.exists() else []
    done = {ep["date"] for ep in episodes}

    built = []
    if not args.feed_only:
        for path in sorted(SCRIPTS_DIR.glob("*.md")):
            script = parse_script(path)
            if script["date"] in done:
                continue
            print(f"Episodio {script['date']}: {script['title']}")
            text = clean_for_speech(script["spoken"])
            # Google accetta al massimo 5.000 byte per richiesta: blocchi più corti
            limit = 1800 if cfg.get("tts_provider") == "google" else CHUNK_LIMIT
            chunks = chunk_text(text, limit)
            parts = synthesize(chunks, cfg, BUILD_DIR / script["date"], args.dry_run)
            mp3 = BUILD_DIR / f"cvid-{script['date']}.mp3"
            concat(parts, mp3)
            pub = datetime.fromisoformat(script["date"]).replace(hour=5, tzinfo=TZ)
            episodes.append({
                "date": script["date"],
                "title": script["title"],
                "description": script["description"],
                "sources": script["sources"],
                "url": audio_url(script["date"]),
                "bytes": mp3.stat().st_size,
                "seconds": duration_seconds(mp3),
                "characters": len(text),
                "pub_date": format_datetime(pub),
            })
            built.append(script["date"])
            print(f"  MP3 pronto: {mp3.name}, {episodes[-1]['seconds'] // 60} minuti")

    EPISODES_FILE.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_feed(cfg, episodes)

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"built={' '.join(built)}\n")
    print(f"Episodi generati in questa esecuzione: {built or 'nessuno'}")


if __name__ == "__main__":
    main()
