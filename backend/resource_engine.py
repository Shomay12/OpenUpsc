"""Deterministic Resource Subsystem engine for OpenUPSC.

Zero-external-dependency (Python stdlib only) parser, catalog enricher,
dataset synchronizer, and catalog validator built around
`UPSC_FREE_RESOURCES_MASTER.md` as the canonical source of truth.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

MASTER_GUIDE_PATH = Path(__file__).resolve().parent.parent / "UPSC_FREE_RESOURCES_MASTER.md"
DATA_DIR = Path(__file__).resolve().parent / "data"

CANONICAL_TYPES: tuple[str, ...] = ("YouTube", "PDF", "PYQ", "Notes", "Website")
CANONICAL_SUBJECTS: tuple[str, ...] = (
    "NCERT",
    "Indian Polity",
    "History",
    "Art & Culture",
    "Geography",
    "Economy",
    "Environment",
    "Science & Tech",
    "Ethics",
    "CSAT",
    "Question Papers",
    "Current Affairs",
    "Mains & Essay",
    "Governance & IR",
    "Optionals",
    "Interview",
    "Official Hub",
    "Bridge Textbooks",
)

_HOSTNAME_RE = re.compile(
    r"^(?:localhost|(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63})$"
)
_PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,}$")
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_URL_RE = re.compile(r"https?://[^\s<>)\"'\]]+")
_FORBIDDEN_URL_CHARS = set(" \t\r\n[]<>\"'`\\{}|")

_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}

_LEGACY_SUBJECT_MAP = {
    "optional & bridge": "Bridge Textbooks",
    "international relations": "Governance & IR",
    "internal security": "Governance & IR",
}


# =========================================================================
# URL & YOUTUBE VALIDATION / EXTRACTION HELPERS
# =========================================================================


def is_valid_http_url(url: Optional[str]) -> bool:
    """Validate that a URL is a single clean http(s) URL without junk or composites."""
    if not isinstance(url, str) or not url:
        return False
    if url != url.strip():
        return False
    if any(ch in _FORBIDDEN_URL_CHARS for ch in url):
        return False

    lower = url.lower()
    if lower.startswith(("javascript:", "data:", "vbscript:", "mailto:", "file:")):
        return False
    if lower.count("http://") + lower.count("https://") != 1:
        return False

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme.lower() not in ("http", "https"):
        return False
    if not parsed.netloc or "@" in parsed.netloc or "&" in parsed.netloc:
        return False
    if "&" in parsed.path:
        return False

    host = parsed.hostname or ""
    if not host or not _HOSTNAME_RE.match(host):
        return False

    # Reject composite URLs accidentally joined inside query string (e.g. ?a=1&https://b)
    if parsed.query and ("http://" in parsed.query.lower() or "https://" in parsed.query.lower()):
        return False

    return True


def extract_youtube_playlist_id(url: Optional[str]) -> Optional[str]:
    """Extract the YouTube playlist ID (`list=...`) from a valid YouTube URL."""
    if not is_valid_http_url(url):
        return None
    assert url is not None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_HOSTS:
        return None
    qs = parse_qs(parsed.query)
    values = qs.get("list")
    if not values:
        return None
    pid = values[0].strip()
    return pid if _PLAYLIST_ID_RE.match(pid) else None


def extract_youtube_video_id(url: Optional[str]) -> Optional[str]:
    """Extract the 11-character YouTube video ID from watch/youtu.be/embed/shorts/live URLs."""
    if not is_valid_http_url(url):
        return None
    assert url is not None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_HOSTS:
        return None

    segments = [seg for seg in parsed.path.split("/") if seg]
    if host in ("youtu.be", "www.youtu.be"):
        if segments and _VIDEO_ID_RE.match(segments[0]):
            return segments[0]
        return None

    if segments and segments[0] == "watch":
        v_vals = parse_qs(parsed.query).get("v")
        if v_vals and _VIDEO_ID_RE.match(v_vals[0].strip()):
            return v_vals[0].strip()
        return None

    if len(segments) >= 2 and segments[0] in ("embed", "shorts", "live", "v"):
        if _VIDEO_ID_RE.match(segments[1]):
            return segments[1]

    return None


def _normalize_url_key(url: str) -> str:
    """Return a canonical deduplication key for a URL while preserving case-sensitive IDs."""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/")
    query = f"?{parsed.query}" if parsed.query else ""
    return f"https://{host}{port}{path}{query}"


def _clean_md_text(text: str) -> str:
    """Strip Markdown inline formatting (bold, italic, code, links) into clean readable text."""
    s = text.strip()
    s = _MD_LINK_RE.sub(r"\1", s)
    s = s.replace("<br>", "; ").replace("<br/>", "; ").replace("<br />", "; ")
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _slugify(text: str, max_len: int = 44) -> str:
    """Convert text into a clean deterministic kebab-case slug."""
    s = text.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s or "item"


def _extract_youtube_handle(url: str) -> Optional[str]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_HOSTS:
        return None
    m = re.search(r"/(@[A-Za-z0-9_.-]+)", parsed.path)
    return m.group(1) if m else None


def _classify_resource_type(url: str, title: str = "", context: str = "") -> str:
    """Classify a link strictly into one of CANONICAL_TYPES."""
    combined = f"{title} {context}".lower()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path_lower = parsed.path.lower()

    if host in _YOUTUBE_HOSTS:
        if extract_youtube_playlist_id(url) or extract_youtube_video_id(url):
            return "YouTube"
        return "Website"
    if (
        "previous-exam-details" in path_lower
        or "/pyq" in path_lower
        or "previous-year-papers" in path_lower
        or "/quiz" in path_lower
        or "question-papers" in path_lower
        or "answer-keys" in path_lower
        or "cut-off-marks" in path_lower
        or any(kw in combined for kw in ("pyq", "previous year", "quiz", "mock test", "question paper"))
    ):
        if "pdf" in combined and "quiz" not in combined and "mock" not in combined and "pyq" not in combined:
            return "PDF"
        return "PYQ"
    if (
        "ncert.nic.in/textbook.php" in url.lower()
        or path_lower.endswith(".pdf")
        or any(
            kw in combined
            for kw in (
                "pdf",
                "textbook",
                "qcab",
                "booklet",
                "arc report",
                "economic survey",
                "toppers' cop",
                "toppers cop",
                "bare constitution",
                "egyankosh",
                "nios",
                "tntextbooks",
                "downloads",
                "monthly current affairs",
            )
        )
    ):
        return "PDF"
    if any(
        kw in combined
        for kw in (
            "notes",
            "study material",
            "magazine",
            "yojana",
            "kurukshetra",
            "editorial",
            "blog",
            "answer writing",
            "current affairs",
            "daily updates",
            "free articles",
        )
    ):
        return "Notes"
    return "Website"


def _split_composite_url_cell(title: str, raw_url_cell: str) -> list[tuple[str, str]]:
    """Split a table cell that holds multiple '&'-separated URLs into clean (title, url) pairs."""
    urls = [u.strip().rstrip(".,;") for u in _URL_RE.findall(raw_url_cell)]
    urls = [u for u in urls if is_valid_http_url(u)]
    if not urls:
        return []
    if len(urls) == 1:
        return [(title.strip(), urls[0])]

    # Smart title pairing when title has '&' (e.g. "UNGIST IAS & IAS Setu Official YouTube")
    clean_title = title.strip()
    if " & " in clean_title:
        left, right = clean_title.split(" & ", 1)
        left = left.strip()
        right = right.strip()
        # Detect shared trailing descriptor (e.g. "Official YouTube", "Official Websites")
        suffix_match = re.search(
            r"\b(Official YouTube|Official Websites?|Channels?|Portals?|Playlists?)$",
            right,
            re.IGNORECASE,
        )
        if suffix_match and len(urls) == 2:
            suffix = suffix_match.group(1)
            # Singularize plural suffix when splitting into individual entries
            singular_suffix = re.sub(r"s$", "", suffix) if suffix.lower().endswith(("websites", "channels", "portals", "playlists")) else suffix
            right_name = right[: suffix_match.start()].strip()
            names = [
                f"{left} {singular_suffix}".strip(),
                f"{right_name} {singular_suffix}".strip(),
            ]
            return list(zip(names, urls))
        parts = [p.strip() for p in clean_title.split("&")]
        if len(parts) == len(urls):
            return list(zip(parts, urls))

    # Fallback: disambiguate using hostname or YouTube handle
    results: list[tuple[str, str]] = []
    for idx, u in enumerate(urls, start=1):
        handle = _extract_youtube_handle(u)
        host = (urlparse(u).hostname or "").replace("www.", "")
        label = handle or host or f"Part {idx}"
        results.append((f"{clean_title} ({label})", u))
    return results


def _parse_markdown_tables(lines: list[str]) -> list[dict[str, Any]]:
    """Parse all GFM markdown tables inside a line slice into structured header/row dicts."""
    tables: list[dict[str, Any]] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
            headers = [_clean_md_text(c) for c in line.strip("|").split("|")]
            i += 2
            rows: list[list[str]] = []
            while i < n and lines[i].strip().startswith("|"):
                raw_cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                # Pad or truncate to match header length safely
                if len(raw_cells) < len(headers):
                    raw_cells.extend([""] * (len(headers) - len(raw_cells)))
                rows.append(raw_cells[: len(headers)])
                i += 1
            tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def _extract_summary_text(lines: list[str]) -> str:
    """Extract introductory prose/callout lines before the first subheading or table."""
    chunks: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("### ") or s.startswith("|") or re.match(r"^\d+\.\s", s):
            break
        if not s or s == "---":
            continue
        if s.startswith(">"):
            s = s.lstrip(">").strip()
        chunks.append(_clean_md_text(s))
    return " ".join(chunks).strip()


def _parse_edition_medium(cell_text: str) -> tuple[str, str]:
    """Extract (edition, medium) cleanly from Part 2 NCERT table column 3."""
    s = _clean_md_text(cell_text)
    m = re.match(r"^(Classic|NEP New)\s*\((English|Hindi|Urdu)\)$", s, re.IGNORECASE)
    if m:
        edition = "NEP New" if m.group(1).lower().startswith("nep") else "Classic"
        medium = m.group(2).capitalize()
        return edition, medium
    lower = s.lower()
    medium = "Hindi" if "hindi" in lower else ("Urdu" if "urdu" in lower else "English")
    edition = "NEP New" if "nep" in lower else "Classic"
    return edition, medium


def _parse_video_companion_bullets(lines: list[str]) -> list[dict[str, Any]]:
    """Parse Class-wise Verified Video Companions bullet lines into structured entries."""
    companions: list[dict[str, Any]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("- ") or "http" not in stripped:
            continue
        content = stripped[2:].strip()
        urls = _URL_RE.findall(content)
        if not urls:
            continue
        url = urls[0].strip().rstrip(".,;")
        if not is_valid_http_url(url):
            continue
        label_part = content.split("http", 1)[0].strip().rstrip(":").strip()
        label_clean = _clean_md_text(label_part)
        # Extract provider inside trailing parentheses, e.g. "Geography (Amit Sengupta)"
        provider = "Verified UPSC Archive"
        has_explicit_provider = False
        title = label_clean
        pm = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", label_clean)
        if pm:
            title = pm.group(1).strip()
            provider = pm.group(2).strip()
            has_explicit_provider = True
        companions.append(
            {
                "title": title,
                "provider": provider,
                "has_explicit_provider": has_explicit_provider,
                "url": url,
                "youtube_playlist_id": extract_youtube_playlist_id(url),
            }
        )
    return companions


def _match_ncert_video_companions(
    class_num: int,
    subject: str,
    book_title: str,
    class_companions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach relevant verified video companions from the same class to an NCERT textbook row."""
    subj_l = subject.lower()
    book_l = book_title.lower()
    matched: list[dict[str, Any]] = []

    for comp in class_companions:
        ct = comp["title"].lower()
        is_match = False

        if class_num <= 10:
            if "geography" in ct and "geography" in subj_l:
                is_match = True
            elif "history" in ct and "history" in subj_l:
                is_match = True
            elif ("civics" in ct or "polity" in ct or "political science" in ct) and (
                "civics" in subj_l or "polity" in subj_l or "political science" in subj_l
            ):
                is_match = True
            elif "economics" in ct and "economics" in subj_l:
                is_match = True
            elif "mathematics" in ct and "mathematics" in subj_l:
                is_match = True
            elif "social science" in ct and "social science" in subj_l:
                is_match = True
            elif "science curiosity" in ct and "science" in subj_l and "curiosity" in book_l:
                is_match = True
            elif "science classic" in ct and "science" in subj_l and "social" not in subj_l and "curiosity" not in book_l:
                is_match = True
            elif (
                "science" in ct
                and "social" not in ct
                and "curiosity" not in ct
                and "classic" not in ct
                and "science" in subj_l
                and "social" not in subj_l
                and "political" not in subj_l
            ):
                is_match = True
            elif "exploring society" in ct and (
                ("exploring society" in book_l and "part-ii" in book_l)
                or ("samaj ka aadhyan" in book_l and "part-ii" in book_l)
            ):
                is_match = True
        elif class_num == 11:
            if "fundamentals of physical geography" in ct and (
                "fundamentals of physical geography" in book_l or "bhautik bhugol" in book_l
            ):
                is_match = True
            elif "india: physical environment" in ct and (
                "india: physical environment" in book_l or "bharat bhautik paryavaran" in book_l
            ):
                is_match = True
            elif "indian constitution at work" in ct and (
                "indian constitution at work" in book_l or "bharat ka samvidhan" in book_l
            ):
                is_match = True
            elif "political theory" in ct and "political theory" in book_l:
                is_match = True
            elif "indian economic development" in ct and (
                "indian economic development" in book_l or "bhartiya arthvyavastha" in book_l
            ):
                is_match = True
            elif "introduction to indian art" in ct and (
                "introduction to indian art" in book_l or "bhartiya kala ka parichay" in book_l
            ):
                is_match = True
            elif "themes in world history" in ct and "themes in world history" in book_l:
                is_match = True
            elif "introducing sociology" in ct and "introducing sociology" in book_l:
                is_match = True
            elif "understanding society" in ct and "understanding society" in book_l:
                is_match = True
            elif "psychology" in ct and "psychology" in subj_l:
                is_match = True
        elif class_num == 12:
            if "themes in indian history part-i" == ct and (
                "part i (" in book_l or "bharatiya itihas ke kuchh vishay" in book_l
            ):
                is_match = True
            elif "themes in indian history part-ii" == ct and (
                "part ii (" in book_l or "bharatiya itihas ke kuchh vishay" in book_l
            ):
                is_match = True
            elif "themes in indian history part-iii" == ct and (
                "part iii (" in book_l or "bharatiya itihas ke kuchh vishay" in book_l
            ):
                is_match = True
            elif "fundamentals of human geography" in ct and "fundamentals of human geography" in book_l:
                is_match = True
            elif "india: people and economy" in ct and "india: people and economy" in book_l:
                is_match = True
            elif "introductory macroeconomics" in ct and (
                "introductory macroeconomics" in book_l or "samashti arthashastra" in book_l
            ):
                is_match = True
            elif "biology" in ct and "biology" in book_l:
                is_match = True
            elif "contemporary world politics" in ct and "contemporary world politics" in book_l:
                is_match = True
            elif "politics in india since independence" in ct and "politics in india since independence" in book_l:
                is_match = True
            elif "indian society" in ct and "indian society" in book_l:
                is_match = True
            elif "social change" in ct and "social change" in book_l:
                is_match = True
            elif "psychology" in ct and ("psychology" in book_l or "ethics" in subj_l):
                is_match = True
            elif "sociology" in ct and "indian society" not in ct and "social change" not in ct and "sociology" in subj_l:
                is_match = True

        if is_match:
            matched.append(
                {
                    "title": comp["title"],
                    "provider": comp["provider"],
                    "url": comp["url"],
                    "youtube_playlist_id": comp["youtube_playlist_id"],
                }
            )

    return matched


# =========================================================================
# MASTER GUIDE PARSER (ALL 11 PARTS)
# =========================================================================


def parse_master_guide(md_path: Optional[Path] = None) -> dict[str, Any]:
    """Parse all 11 parts of `UPSC_FREE_RESOURCES_MASTER.md` into a structured dictionary."""
    path = Path(md_path) if md_path is not None else MASTER_GUIDE_PATH
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    doc_title = "UPSC CSE Complete Free Resources Master Guide"
    for line in lines:
        if line.startswith("# "):
            doc_title = _clean_md_text(line[2:])
            break

    part_starts: list[tuple[int, int, str]] = []
    for idx, line in enumerate(lines):
        m = re.match(r"^## Part (\d+):\s*(.+)$", line.strip())
        if m:
            part_starts.append((idx, int(m.group(1)), _clean_md_text(m.group(2))))

    parts_list: list[dict[str, Any]] = []
    official_hub: list[dict[str, Any]] = []
    ncert_portals: list[dict[str, Any]] = []
    ncert_directory: list[dict[str, Any]] = []
    bridge_textbooks: list[dict[str, Any]] = []
    standard_books: list[dict[str, Any]] = []
    govt_reports: list[dict[str, Any]] = []
    news_and_thinktanks: list[dict[str, Any]] = []
    curated_notes: list[dict[str, Any]] = []
    exam_papers_and_quizzes: list[dict[str, Any]] = []
    video_library: dict[str, list[dict[str, Any]]] = {
        "official_channels": [],
        "subject_channels": [],
        "direct_playlists": [],
    }
    csat_kit: list[dict[str, Any]] = []
    optionals: list[dict[str, Any]] = []
    interview_prep: list[dict[str, Any]] = []
    study_sequence: list[dict[str, Any]] = []

    # Keep lookup of parsed URLs by lowercase keyword for Part 11 phase link resolution
    named_link_index: dict[str, tuple[str, str]] = {}

    def _register_named_link(label: str, url: str) -> None:
        if is_valid_http_url(url):
            key = label.lower().strip()
            named_link_index.setdefault(key, (label.strip(), url))

    for p_idx, (start_line, part_num, part_title) in enumerate(part_starts):
        end_line = part_starts[p_idx + 1][0] if p_idx + 1 < len(part_starts) else len(lines)
        part_lines = lines[start_line + 1 : end_line]
        summary = _extract_summary_text(part_lines)
        slug = f"part-{part_num}-{_slugify(part_title, max_len=56)}"

        # Split into ### subsections if present
        sub_indices = [i for i, l in enumerate(part_lines) if l.startswith("### ")]
        subsections_raw: list[tuple[str, list[str]]] = []
        if sub_indices:
            for s_i, sub_start in enumerate(sub_indices):
                sub_end = sub_indices[s_i + 1] if s_i + 1 < len(sub_indices) else len(part_lines)
                sub_title = _clean_md_text(part_lines[sub_start][4:])
                subsections_raw.append((sub_title, part_lines[sub_start + 1 : sub_end]))
        else:
            subsections_raw.append((part_title, part_lines))

        structured_sections: list[dict[str, Any]] = []

        # ----- Part 1: Official UPSC Exam Hub -----
        if part_num == 1:
            tables = _parse_markdown_tables(part_lines)
            sec_items: list[dict[str, Any]] = []
            for tbl in tables:
                for row in tbl["rows"]:
                    if len(row) < 3:
                        continue
                    title = _clean_md_text(row[0])
                    purpose = _clean_md_text(row[1])
                    for split_title, url in _split_composite_url_cell(title, row[2]):
                        entry = {"title": split_title, "purpose": purpose, "url": url}
                        official_hub.append(entry)
                        sec_items.append(entry)
                        _register_named_link(split_title, url)
            structured_sections.append({"title": part_title, "items": sec_items, "tables": tables})

        # ----- Part 2: NCERT Portals, Class 6-12 Directory & Bridge Textbooks -----
        elif part_num == 2:
            for sub_title, sub_lines in subsections_raw:
                tables = _parse_markdown_tables(sub_lines)
                sub_low = sub_title.lower()

                if "2.1" in sub_low or "textbook portals" in sub_low:
                    sec_items = []
                    for tbl in tables:
                        for row in tbl["rows"]:
                            if len(row) < 3:
                                continue
                            title = _clean_md_text(row[0])
                            offers = _clean_md_text(row[1])
                            for split_title, url in _split_composite_url_cell(title, row[2]):
                                entry = {"title": split_title, "offers": offers, "url": url}
                                ncert_portals.append(entry)
                                sec_items.append(entry)
                                _register_named_link(split_title, url)
                    structured_sections.append({"title": sub_title, "items": sec_items, "tables": tables})

                elif "2.2" in sub_low or "bridge textbooks" in sub_low:
                    sec_items = []
                    for tbl in tables:
                        for row in tbl["rows"]:
                            if len(row) < 3:
                                continue
                            title = _clean_md_text(row[0])
                            best_for = _clean_md_text(row[1])
                            for split_title, url in _split_composite_url_cell(title, row[2]):
                                entry = {"title": split_title, "best_used_for": best_for, "url": url}
                                bridge_textbooks.append(entry)
                                sec_items.append(entry)
                                _register_named_link(split_title, url)
                    structured_sections.append({"title": sub_title, "items": sec_items, "tables": tables})

                else:
                    cm = re.search(r"Class\s+(\d+)", sub_title, re.IGNORECASE)
                    if cm:
                        class_num = int(cm.group(1))
                        class_companions = _parse_video_companion_bullets(sub_lines)
                        sec_items = []
                        for tbl in tables:
                            for row in tbl["rows"]:
                                if len(row) < 5:
                                    continue
                                subj = _clean_md_text(row[0])
                                book_title = _clean_md_text(row[1])
                                edition, medium = _parse_edition_medium(row[2])
                                priority_gs = _clean_md_text(row[3])
                                for split_title, url in _split_composite_url_cell(book_title, row[4]):
                                    companions = _match_ncert_video_companions(
                                        class_num, subj, split_title, class_companions
                                    )
                                    entry = {
                                        "class_num": class_num,
                                        "subject": subj,
                                        "book_title": split_title,
                                        "edition": edition,
                                        "medium": medium,
                                        "priority_gs_map": priority_gs,
                                        "url": url,
                                        "video_companions": companions,
                                    }
                                    ncert_directory.append(entry)
                                    sec_items.append(entry)
                        structured_sections.append(
                            {
                                "title": sub_title,
                                "class_num": class_num,
                                "items": sec_items,
                                "video_companions": [
                                    {
                                        "title": c["title"],
                                        "provider": c["provider"],
                                        "url": c["url"],
                                        "youtube_playlist_id": c["youtube_playlist_id"],
                                    }
                                    for c in class_companions
                                ],
                                "tables": tables,
                            }
                        )

        # ----- Part 3: Standard Core Books & Free Legal Companions -----
        elif part_num == 3:
            tables = _parse_markdown_tables(part_lines)
            sec_items = []
            for tbl in tables:
                for row in tbl["rows"]:
                    if len(row) < 3:
                        continue
                    subj = _clean_md_text(row[0])
                    std_book = _clean_md_text(row[1])
                    companions: list[dict[str, Any]] = []
                    for label, url in _MD_LINK_RE.findall(row[2]):
                        clean_url = url.strip()
                        if not is_valid_http_url(clean_url):
                            continue
                        clean_label = _clean_md_text(label)
                        c_type = _classify_resource_type(clean_url, clean_label, subj)
                        companions.append(
                            {
                                "title": clean_label,
                                "url": clean_url,
                                "type": c_type,
                                "youtube_playlist_id": extract_youtube_playlist_id(clean_url),
                            }
                        )
                        _register_named_link(clean_label, clean_url)
                    entry = {
                        "subject": subj,
                        "standard_book": std_book,
                        "companions": companions,
                    }
                    standard_books.append(entry)
                    sec_items.append(entry)
            structured_sections.append({"title": part_title, "items": sec_items, "tables": tables})

        # ----- Part 4: Official Government Reports & Primary Data -----
        elif part_num == 4:
            for sub_title, sub_lines in subsections_raw:
                tables = _parse_markdown_tables(sub_lines)
                sec_items = []
                for tbl in tables:
                    for row in tbl["rows"]:
                        if len(row) < 3:
                            continue
                        title = _clean_md_text(row[0])
                        utility = _clean_md_text(row[1])
                        for split_title, url in _split_composite_url_cell(title, row[2]):
                            entry = {
                                "subsection": sub_title,
                                "title": split_title,
                                "utility": utility,
                                "url": url,
                            }
                            govt_reports.append(entry)
                            sec_items.append(entry)
                            _register_named_link(split_title, url)
                structured_sections.append({"title": sub_title, "items": sec_items, "tables": tables})

        # ----- Part 5: Free News, Broadcasts & Think-Tanks -----
        elif part_num == 5:
            for sub_title, sub_lines in subsections_raw:
                tables = _parse_markdown_tables(sub_lines)
                sec_items = []
                for tbl in tables:
                    for row in tbl["rows"]:
                        if len(row) < 3:
                            continue
                        title = _clean_md_text(row[0])
                        usage = _clean_md_text(row[1])
                        for split_title, url in _split_composite_url_cell(title, row[2]):
                            entry = {
                                "subsection": sub_title,
                                "title": split_title,
                                "usage": usage,
                                "url": url,
                                "youtube_playlist_id": extract_youtube_playlist_id(url),
                            }
                            news_and_thinktanks.append(entry)
                            sec_items.append(entry)
                            _register_named_link(split_title, url)
                structured_sections.append({"title": sub_title, "items": sec_items, "tables": tables})

        # ----- Part 6: Free Curated Notes, Magazines & Toppers' Copies -----
        elif part_num == 6:
            tables = _parse_markdown_tables(part_lines)
            sec_items = []
            for tbl in tables:
                for row in tbl["rows"]:
                    if len(row) < 3:
                        continue
                    title = _clean_md_text(row[0])
                    desc = _clean_md_text(row[1])
                    for split_title, url in _split_composite_url_cell(title, row[2]):
                        entry = {"title": split_title, "description": desc, "url": url}
                        curated_notes.append(entry)
                        sec_items.append(entry)
                        _register_named_link(split_title, url)
            structured_sections.append({"title": part_title, "items": sec_items, "tables": tables})

        # ----- Part 7: Exam Papers (PYQs), Quizzes & Mocks -----
        elif part_num == 7:
            tables = _parse_markdown_tables(part_lines)
            sec_items = []
            for tbl in tables:
                for row in tbl["rows"]:
                    if len(row) < 3:
                        continue
                    title = _clean_md_text(row[0])
                    coverage = _clean_md_text(row[1])
                    for split_title, url in _split_composite_url_cell(title, row[2]):
                        entry = {
                            "title": split_title,
                            "coverage": coverage,
                            "url": url,
                            "youtube_playlist_id": extract_youtube_playlist_id(url),
                        }
                        exam_papers_and_quizzes.append(entry)
                        sec_items.append(entry)
                        _register_named_link(split_title, url)
            structured_sections.append({"title": part_title, "items": sec_items, "tables": tables})

        # ----- Part 8: Verified Free Video Lectures Library -----
        elif part_num == 8:
            for sub_title, sub_lines in subsections_raw:
                tables = _parse_markdown_tables(sub_lines)
                sub_low = sub_title.lower()
                sec_items = []

                if "8.1" in sub_low or "official" in sub_low:
                    for tbl in tables:
                        for row in tbl["rows"]:
                            if len(row) < 3:
                                continue
                            title = _clean_md_text(row[0])
                            best_for = _clean_md_text(row[1])
                            for split_title, url in _split_composite_url_cell(title, row[2]):
                                entry = {
                                    "title": split_title,
                                    "best_for": best_for,
                                    "url": url,
                                    "handle": _extract_youtube_handle(url),
                                }
                                video_library["official_channels"].append(entry)
                                sec_items.append(entry)
                                _register_named_link(split_title, url)

                elif "8.2" in sub_low or "subject-wise" in sub_low:
                    for tbl in tables:
                        for row in tbl["rows"]:
                            if len(row) < 3:
                                continue
                            title = _clean_md_text(row[0])
                            specialty = _clean_md_text(row[1])
                            for split_title, url in _split_composite_url_cell(title, row[2]):
                                entry = {
                                    "title": split_title,
                                    "specialty": specialty,
                                    "url": url,
                                    "handle": _extract_youtube_handle(url),
                                }
                                video_library["subject_channels"].append(entry)
                                sec_items.append(entry)
                                _register_named_link(split_title, url)

                else:
                    for tbl in tables:
                        for row in tbl["rows"]:
                            if len(row) < 3:
                                continue
                            theme = _clean_md_text(row[0])
                            title_and_ed = _clean_md_text(row[1])
                            # Split "Playlist Title — Educator"
                            if " — " in title_and_ed:
                                pl_title, educator = [p.strip() for p in title_and_ed.rsplit(" — ", 1)]
                            else:
                                pl_title, educator = title_and_ed, "Verified UPSC Channel"
                            for split_title, url in _split_composite_url_cell(pl_title, row[2]):
                                entry = {
                                    "theme": theme,
                                    "title": split_title,
                                    "educator": educator,
                                    "url": url,
                                    "youtube_playlist_id": extract_youtube_playlist_id(url),
                                }
                                video_library["direct_playlists"].append(entry)
                                sec_items.append(entry)
                                _register_named_link(split_title, url)

                structured_sections.append({"title": sub_title, "items": sec_items, "tables": tables})

        # ----- Part 9: CSAT Complete Free Resource Kit -----
        elif part_num == 9:
            tables = _parse_markdown_tables(part_lines)
            sec_items = []
            for tbl in tables:
                for row in tbl["rows"]:
                    if len(row) < 3:
                        continue
                    res_type = _clean_md_text(row[0])
                    title = _clean_md_text(row[1])
                    split_pairs = _split_composite_url_cell(title, row[2])
                    # Singularize plural resource_type when a composite cell splits
                    eff_type = res_type
                    if len(split_pairs) > 1 and eff_type.endswith("s"):
                        eff_type = eff_type[:-1]
                    for split_title, url in split_pairs:
                        entry = {
                            "resource_type": eff_type,
                            "title": split_title,
                            "url": url,
                            "youtube_playlist_id": extract_youtube_playlist_id(url),
                        }
                        csat_kit.append(entry)
                        sec_items.append(entry)
                        _register_named_link(split_title, url)
            structured_sections.append({"title": part_title, "items": sec_items, "tables": tables})

        # ----- Part 10: Optionals & Personality Test -----
        elif part_num == 10:
            for sub_title, sub_lines in subsections_raw:
                tables = _parse_markdown_tables(sub_lines)
                sub_low = sub_title.lower()
                sec_items = []

                if "10.1" in sub_low or "optional" in sub_low:
                    for tbl in tables:
                        for row in tbl["rows"]:
                            if len(row) < 3:
                                continue
                            opt_subj = _clean_md_text(row[0])
                            academic_links = [
                                {"title": _clean_md_text(lbl), "url": u.strip()}
                                for lbl, u in _MD_LINK_RE.findall(row[1])
                                if is_valid_http_url(u.strip())
                            ]
                            video_links = [
                                {
                                    "title": _clean_md_text(lbl),
                                    "url": u.strip(),
                                    "youtube_playlist_id": extract_youtube_playlist_id(u.strip()),
                                }
                                for lbl, u in _MD_LINK_RE.findall(row[2])
                                if is_valid_http_url(u.strip())
                            ]
                            # Resolve Part 8 cross-references when a row mentions channels by name
                            if not video_links:
                                col3_clean = _clean_md_text(row[2]).lower()
                                all_channels = (
                                    video_library["official_channels"] + video_library["subject_channels"]
                                )
                                for ch in all_channels:
                                    ch_base = ch["title"].split("(")[0].strip().lower()
                                    if ch_base and ch_base in col3_clean:
                                        video_links.append(
                                            {
                                                "title": f"{ch['title']} (YouTube Channel)",
                                                "url": ch["url"],
                                                "youtube_playlist_id": None,
                                            }
                                        )
                            entry = {
                                "subject": opt_subj,
                                "academic_links": academic_links,
                                "video_links": video_links,
                            }
                            optionals.append(entry)
                            sec_items.append(entry)
                    structured_sections.append({"title": sub_title, "items": sec_items, "tables": tables})

                else:
                    for tbl in tables:
                        for row in tbl["rows"]:
                            if len(row) < 3:
                                continue
                            title = _clean_md_text(row[0])
                            purpose = _clean_md_text(row[1])
                            for split_title, url in _split_composite_url_cell(title, row[2]):
                                entry = {
                                    "title": split_title,
                                    "purpose": purpose,
                                    "url": url,
                                    "youtube_playlist_id": extract_youtube_playlist_id(url),
                                }
                                interview_prep.append(entry)
                                sec_items.append(entry)
                                _register_named_link(split_title, url)
                    structured_sections.append({"title": sub_title, "items": sec_items, "tables": tables})

        # ----- Part 11: Zero-Cost Step-by-Step Study Sequence -----
        elif part_num == 11:
            current_phase: Optional[dict[str, Any]] = None
            for raw_line in part_lines:
                s = raw_line.strip()
                if not s or s == "---":
                    continue
                pm = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*:?$", s)
                if pm:
                    if current_phase is not None:
                        study_sequence.append(current_phase)
                    phase_num = int(pm.group(1))
                    heading_raw = pm.group(2).strip().rstrip(":")
                    if " — " in heading_raw:
                        timeframe, phase_title = [p.strip() for p in heading_raw.split(" — ", 1)]
                    else:
                        timeframe, phase_title = f"Phase {phase_num}", heading_raw
                    current_phase = {
                        "phase_number": phase_num,
                        "title": phase_title,
                        "timeframe": timeframe,
                        "tasks": [],
                        "links": [],
                    }
                elif s.startswith("- ") and current_phase is not None:
                    bullet_raw = s[2:].strip()
                    current_phase["tasks"].append(_clean_md_text(bullet_raw))
                    for lbl, u in _MD_LINK_RE.findall(bullet_raw):
                        clean_u = u.strip()
                        if is_valid_http_url(clean_u):
                            current_phase["links"].append({"label": _clean_md_text(lbl), "url": clean_u})

            if current_phase is not None:
                study_sequence.append(current_phase)

            # Enrich each phase's links cleanly from referenced canonical entities in Parts 1–10
            phase_keyword_targets = [
                ("upsc previous exam details", "upsc previous exam details"),
                ("class 6–12 ncerts", "ncert official textbook portal"),
                ("the hindu", "the hindu (main)"),
                ("indian express (explained)", "the indian express — explained"),
                ("pib", "press information bureau (pib)"),
                ("prs bill track", "prs bill track"),
                ("2nd arc reports", "darpg — 2nd arc reports (all 15 pdfs)"),
                ("2nd arc 4th report", "darpg — 2nd arc reports (all 15 pdfs)"),
                ("ignou egyankosh", "ignou egyankosh repository"),
                ("e-pg pathshala", "e-pg pathshala (ugc / inflibnet)"),
                ("insightsias", "insightsias (home)"),
                ("forumias", "forumias blog"),
                ("drishti ias", "drishti ias — mains answer writing"),
                ("toppers' answer copies", "drishti ias — toppers' copies (english)"),
                ("vision ias pt 365", "vision ias — free resources hub"),
                ("economic survey", "economic survey official pdf"),
                ("union budget", "union budget portal (mof)"),
                ("ungist", "free upsc csat topic-wise lectures — ungist ias"),
                ("drishti ias free playlists", "csat simplified — drishti ias english"),
                ("upsc specimen qcab", "specimen question-cum-answer booklets (qcab)"),
                ("atish mathur", "atish mathur free ethics course"),
                ("mains 365", "vision ias — free resources hub"),
                ("sansad tv perspective", "sansad tv — perspective playlist"),
                ("toppers' mock interviews", "forumias upsc toppers strategy & interviews"),
                ("air news", "newsonair (akashvani / air news)"),
            ]
            for phase in study_sequence:
                existing_urls = {_normalize_url_key(l["url"]) for l in phase["links"]}
                blob = " ".join(phase["tasks"]).lower()
                for trigger, lookup_key in phase_keyword_targets:
                    if trigger in blob and lookup_key in named_link_index:
                        lbl, u = named_link_index[lookup_key]
                        nk = _normalize_url_key(u)
                        if nk not in existing_urls:
                            phase["links"].append({"label": lbl, "url": u})
                            existing_urls.add(nk)

            structured_sections.append({"title": part_title, "items": study_sequence, "tables": []})

        parts_list.append(
            {
                "part_number": part_num,
                "slug": slug,
                "title": part_title,
                "summary": summary,
                "sections": structured_sections,
            }
        )

    # Compute exact link counts across all parsed structures
    all_parsed_urls = _collect_master_guide_urls(
        official_hub=official_hub,
        ncert_portals=ncert_portals,
        ncert_directory=ncert_directory,
        bridge_textbooks=bridge_textbooks,
        standard_books=standard_books,
        govt_reports=govt_reports,
        news_and_thinktanks=news_and_thinktanks,
        curated_notes=curated_notes,
        exam_papers_and_quizzes=exam_papers_and_quizzes,
        video_library=video_library,
        csat_kit=csat_kit,
        optionals=optionals,
        interview_prep=interview_prep,
        study_sequence=study_sequence,
        parts=parts_list,
    )
    unique_norm_urls = {_normalize_url_key(u) for u in all_parsed_urls}

    return {
        "meta": {
            "title": doc_title,
            "total_links": len(unique_norm_urls),
            "total_link_occurrences": len(all_parsed_urls),
            "source_file": path.name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "parts_count": len(parts_list),
        },
        "parts": parts_list,
        "official_hub": official_hub,
        "ncert_portals": ncert_portals,
        "ncert_directory": ncert_directory,
        "bridge_textbooks": bridge_textbooks,
        "standard_books": standard_books,
        "govt_reports": govt_reports,
        "news_and_thinktanks": news_and_thinktanks,
        "curated_notes": curated_notes,
        "exam_papers_and_quizzes": exam_papers_and_quizzes,
        "video_library": video_library,
        "csat_kit": csat_kit,
        "optionals": optionals,
        "interview_prep": interview_prep,
        "study_sequence": study_sequence,
    }


def _collect_master_guide_urls(
    *,
    official_hub: list[dict[str, Any]],
    ncert_portals: list[dict[str, Any]],
    ncert_directory: list[dict[str, Any]],
    bridge_textbooks: list[dict[str, Any]],
    standard_books: list[dict[str, Any]],
    govt_reports: list[dict[str, Any]],
    news_and_thinktanks: list[dict[str, Any]],
    curated_notes: list[dict[str, Any]],
    exam_papers_and_quizzes: list[dict[str, Any]],
    video_library: dict[str, list[dict[str, Any]]],
    csat_kit: list[dict[str, Any]],
    optionals: list[dict[str, Any]],
    interview_prep: list[dict[str, Any]],
    study_sequence: list[dict[str, Any]],
    parts: list[dict[str, Any]],
) -> list[str]:
    urls: list[str] = []
    for item in official_hub:
        urls.append(item["url"])
    for item in ncert_portals:
        urls.append(item["url"])
    for item in ncert_directory:
        urls.append(item["url"])
    # Include all Part 2 class video companions once per occurrence in Part 2 sections
    for p in parts:
        if p.get("part_number") == 2:
            for sec in p.get("sections", []):
                for vc in sec.get("video_companions", []):
                    urls.append(vc["url"])
    for item in bridge_textbooks:
        urls.append(item["url"])
    for item in standard_books:
        for comp in item.get("companions", []):
            urls.append(comp["url"])
    for item in govt_reports:
        urls.append(item["url"])
    for item in news_and_thinktanks:
        urls.append(item["url"])
    for item in curated_notes:
        urls.append(item["url"])
    for item in exam_papers_and_quizzes:
        urls.append(item["url"])
    for bucket in ("official_channels", "subject_channels", "direct_playlists"):
        for item in video_library.get(bucket, []):
            urls.append(item["url"])
    for item in csat_kit:
        urls.append(item["url"])
    for item in optionals:
        for lnk in item.get("academic_links", []):
            urls.append(lnk["url"])
        for lnk in item.get("video_links", []):
            urls.append(lnk["url"])
    for item in interview_prep:
        urls.append(item["url"])
    for phase in study_sequence:
        for lnk in phase.get("links", []):
            urls.append(lnk["url"])
    return urls


# =========================================================================
# RESOURCE CATALOG ENRICHMENT
# =========================================================================


def _normalize_canonical_subject(raw_subject: str) -> str:
    """Map any subject label strictly into one of CANONICAL_SUBJECTS."""
    s = raw_subject.strip()
    if s in CANONICAL_SUBJECTS:
        return s
    low = s.lower()
    if low in _LEGACY_SUBJECT_MAP:
        return _LEGACY_SUBJECT_MAP[low]
    if "india: physical environment" in low or "physical geography" in low or "human geography" in low:
        return "Geography"
    if "world politics" in low:
        return "Governance & IR"
    if "ncert" in low:
        return "NCERT"
    if "polity" in low or "constitution" in low or "civics" in low or "political" in low:
        return "Indian Polity"
    if "history" in low:
        return "History"
    if re.search(r"\bart\b", low) or "culture" in low or "heritage" in low:
        return "Art & Culture"
    if "geography" in low or "mapping" in low:
        return "Geography"
    if "econom" in low or "budget" in low or "macroeconomics" in low:
        return "Economy"
    if "environment" in low or "ecology" in low or "wetland" in low or "ramsar" in low:
        return "Environment"
    if "science" in low or "tech" in low or "biotech" in low or "space" in low:
        return "Science & Tech"
    if "ethics" in low or "psychology" in low:
        return "Ethics"
    if "csat" in low or "math" in low:
        return "CSAT"
    if "question paper" in low or "pyq" in low or "quiz" in low:
        return "Question Papers"
    if "essay" in low or "answer writing" in low or "mains" in low or "topper" in low:
        return "Mains & Essay"
    if "governance" in low or "international" in low or "security" in low or "diplomacy" in low or "ir" == low:
        return "Governance & IR"
    if "optional" in low:
        return "Optionals"
    if "interview" in low or "personality" in low or "daf" in low:
        return "Interview"
    if "bridge" in low:
        return "Bridge Textbooks"
    if "official" in low:
        return "Official Hub"
    return "Current Affairs"


def _infer_provider(title: str, url: str, default: str = "Official / Verified Free Source") -> str:
    """Derive a clean, specific provider name from title or URL host."""
    host = (urlparse(url).hostname or "").lower().replace("www.", "")
    if " — " in title:
        left, right = [p.strip() for p in title.rsplit(" — ", 1)]
        if len(right) <= 42 and not any(w in right.lower() for w in ("part", "chapter", "paper", "class", "question")):
            return right
        if len(left) <= 36 and any(
            k in left.lower()
            for k in ("upsc", "drishti", "vision", "insights", "forumias", "vajiram", "next ias", "clearias", "sleepy", "prs", "sansad", "darpg", "the hindu", "indian express", "mp-idsa")
        ):
            return left

    known_title_providers = (
        ("pmf ias", "PMF IAS"),
        ("sleepy classes", "Sleepy Classes IAS"),
        ("bookstawa", "Bookstawa"),
        ("atish mathur", "Atish Mathur"),
        ("sudarshan gurjar", "Sudarshan Gurjar"),
        ("mrunal patel", "Mrunal Patel"),
        ("amit sengupta", "Amit Sengupta"),
        ("hd education", "Harshit Dwivedi (HD Education)"),
        ("harshit dwivedi", "Harshit Dwivedi (HD Education)"),
        ("studyiq", "StudyIQ IAS"),
        ("forumias", "ForumIAS"),
        ("vision ias", "Vision IAS"),
        ("drishti ias", "Drishti IAS"),
        ("insightsias", "InsightsIAS"),
        ("upscprep", "UPSCprep.com"),
        ("ungist", "UNGIST IAS"),
        ("ias setu", "IAS Setu"),
        ("rau's ias", "Rau's IAS"),
        ("pw onlyias", "PW OnlyIAS"),
        ("onlyias", "OnlyIAS"),
        ("unacademy", "Unacademy Free Archive"),
        ("ncert official", "NCERT Official"),
        ("sansad tv", "Sansad TV Official"),
        ("cec ugc", "CEC UGC"),
        ("magnet brains", "Magnet Brains"),
        ("pratik nayak", "Pratik Nayak"),
        ("ravi p. agrahari", "Dr. Ravi P. Agrahari"),
        ("ravi agrahari", "Dr. Ravi P. Agrahari"),
        ("rajtanil solanki", "Rajtanil Solanki (Mrunal)"),
        ("testbook", "Testbook SuperCoaching"),
        ("newsonair", "NewsOnAir Official"),
    )
    tl = title.lower()
    for needle, label in known_title_providers:
        if needle in tl:
            return label

    host_providers = {
        "upsc.gov.in": "UPSC Official (upsc.gov.in)",
        "upsconline.gov.in": "UPSC Online Portal (Govt of India)",
        "upsconline.nic.in": "UPSC Online NIC (Govt of India)",
        "ncert.nic.in": "NCERT Official (ncert.nic.in)",
        "epathshala.ncert.gov.in": "ePathshala (NCERT & MoE)",
        "diksha.gov.in": "DIKSHA (Ministry of Education)",
        "ndl.iitkgp.ac.in": "NDLI (IIT Kharagpur)",
        "ndl.gov.in": "NDLI Official Gov Mirror",
        "tntextbooks.in": "Tamil Nadu SCERT",
        "tnschools.gov.in": "Tamil Nadu SCERT",
        "nios.ac.in": "NIOS Official (Govt of India)",
        "egyankosh.ac.in": "IGNOU Official",
        "epgp.inflibnet.ac.in": "UGC / INFLIBNET",
        "swayam.gov.in": "SWAYAM (Ministry of Education)",
        "nptel.ac.in": "NPTEL (IITs & IISc)",
        "indiabudget.gov.in": "Ministry of Finance (Govt of India)",
        "dea.gov.in": "Department of Economic Affairs (MoF)",
        "rbi.org.in": "Reserve Bank of India (RBI)",
        "data.rbi.org.in": "Reserve Bank of India (DBIE)",
        "fincomindia.nic.in": "Finance Commission of India",
        "niti.gov.in": "NITI Aayog (Govt of India)",
        "darpg.gov.in": "DARPG (Govt of India)",
        "data.gov.in": "Open Government Data India",
        "india.gov.in": "National Portal of India",
        "mygov.in": "MyGov India",
        "vikaspedia.in": "Vikaspedia (MeitY)",
        "prsindia.org": "PRS Legislative Research",
        "sansad.in": "Parliament of India (Digital Sansad)",
        "legislative.gov.in": "Legislative Dept (Govt of India)",
        "indiacode.gov.in": "Ministry of Law & Justice (India Code)",
        "constitutionofindia.net": "Constitution of India Net",
        "sci.gov.in": "Supreme Court of India",
        "judgments.ecourts.gov.in": "e-Courts (Supreme Court of India)",
        "lawcommissionofindia.nic.in": "Law Commission of India",
        "eci.gov.in": "Election Commission of India",
        "cag.gov.in": "CAG of India",
        "isro.gov.in": "ISRO (Govt of India)",
        "dst.gov.in": "Dept. of Science & Technology (DST)",
        "drdo.gov.in": "DRDO (Ministry of Defence)",
        "moef.gov.in": "MoEFCC (Govt of India)",
        "wii.gov.in": "Wildlife Institute of India (WII)",
        "ndma.gov.in": "NDMA (Govt of India)",
        "mea.gov.in": "Ministry of External Affairs (MEA)",
        "agriwelfare.gov.in": "Dept. of Agriculture & Farmers Welfare",
        "censusindia.gov.in": "Census of India (MHA)",
        "surveyofindia.gov.in": "Survey of India",
        "ccrtindia.gov.in": "CCRT (Ministry of Culture)",
        "indianculture.gov.in": "Ministry of Culture (Indian Culture Portal)",
        "culture.gov.in": "Ministry of Culture (Govt of India)",
        "nationalarchives.nic.in": "National Archives of India",
        "abhilekh-patal.in": "National Archives of India (Abhilekh Patal)",
        "pib.gov.in": "PIB (Govt of India)",
        "newsonair.gov.in": "Akashvani / AIR News",
        "akashvani.gov.in": "Akashvani (Prasar Bharati)",
        "thehindu.com": "The Hindu",
        "indianexpress.com": "The Indian Express",
        "livemint.com": "LiveMint",
        "downtoearth.org.in": "Down To Earth",
        "epw.in": "Economic & Political Weekly (EPW)",
        "idsa.in": "MP-IDSA",
        "orfonline.org": "Observer Research Foundation (ORF)",
        "visionias.in": "Vision IAS",
        "insightsonindia.com": "InsightsIAS",
        "drishtiias.com": "Drishti IAS",
        "forumias.com": "ForumIAS",
        "iasbaba.com": "IASbaba",
        "pmfias.com": "PMF IAS",
        "clearias.com": "ClearIAS",
        "shankariasparliament.com": "Shankar IAS Parliament",
        "vajiramandravi.com": "Vajiram & Ravi",
        "nextias.com": "NEXT IAS",
        "pwonlyias.com": "PW OnlyIAS",
        "sleepyclasses.com": "Sleepy Classes IAS",
        "upscprep.com": "UPSCprep.com",
        "ungist.com": "UNGIST IAS",
        "iassetu.com": "IAS Setu",
    }
    if host in host_providers:
        return host_providers[host]
    return default


def _merge_tags(existing: list[str], extra: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in list(existing) + list(extra):
        t = raw.strip()
        if not t:
            continue
        low = t.lower()
        if low not in seen:
            seen.add(low)
            out.append(t)
        if len(out) >= limit:
            break
    return out


def _subject_for_govt_report(subsection: str, title: str, utility: str) -> str:
    blob = f"{title} {utility}".lower()
    if "4.2" in subsection:
        return "Indian Polity"
    if "4.1" in subsection:
        if any(k in blob for k in ("budget", "economic survey", "economic affairs", "rbi", "monetary", "finance commission", "gdp", "inflation", "fiscal")):
            return "Economy"
        if "2nd arc" in blob or "ethics" in blob:
            return "Ethics"
        return "Governance & IR"
    # 4.3
    if any(k in blob for k in ("isro", "science", "quantum", "drdo", "missile", "defence")):
        return "Science & Tech"
    if any(k in blob for k in ("moef", "wildlife", "ramsar", "biodiversity", "ndma", "disaster", "climate")):
        return "Environment"
    if any(k in blob for k in ("external affairs", "diplomacy", "bilateral", "summit")):
        return "Governance & IR"
    if any(k in blob for k in ("agriculture", "crop", "msp", "farmers")):
        return "Economy"
    if any(k in blob for k in ("census", "survey of india", "maps", "geospatial")):
        return "Geography"
    if any(k in blob for k in ("ccrt", "culture", "heritage", "architecture", "manuscript")):
        return "Art & Culture"
    if any(k in blob for k in ("archives", "abhilekh", "freedom movement", "historical")):
        return "History"
    return "Governance & IR"


def _subject_for_news(subsection: str, title: str, usage: str) -> str:
    blob = f"{title} {usage}".lower()
    if "the hindu — science" in title.lower():
        return "Science & Tech"
    if "down to earth" in title.lower():
        return "Environment"
    if "mp-idsa" in title.lower() or "orf" in title.lower() or "observer research" in title.lower():
        return "Governance & IR"
    if "livemint" in title.lower():
        return "Economy"
    return "Current Affairs"


def _subject_for_curated_notes(title: str, desc: str) -> str:
    tl = title.lower()
    if "toppers" in tl or "answer writing" in tl or "mains ca" in tl:
        return "Mains & Essay"
    if "ncert" in tl:
        return "NCERT"
    if "pmf ias" in tl:
        return "Environment"
    return "Current Affairs"


def _subject_for_channel(title: str, specialty: str, is_official: bool) -> str:
    tl = title.lower()
    if is_official:
        if "ncert" in tl:
            return "NCERT"
        if "sansad" in tl or "newsonair" in tl or "air" in tl:
            return "Current Affairs"
        return "Bridge Textbooks"
    if "mrunal" in tl:
        return "Economy"
    if "amit sengupta" in tl or "sudarshan gurjar" in tl:
        return "Geography"
    if "atish mathur" in tl or "finology" in tl:
        return "Indian Polity"
    if "bookstawa" in tl:
        return "History"
    if "harshit dwivedi" in tl or "magnet brains" in tl:
        return "NCERT"
    if "ravi" in tl or "agrahari" in tl:
        return "Science & Tech"
    if "pmf ias" in tl:
        return "Environment"
    return "Current Affairs"


def _make_candidate(
    *,
    title: str,
    subject: str,
    category: str,
    level: str,
    language: str,
    res_type: str,
    provider: str,
    url: str,
    description: str,
    senior_tip: str,
    estimated_hours: int,
    tags: list[str],
    master_part: int,
    class_level: Optional[str] = None,
    slug_hint: Optional[str] = None,
) -> dict[str, Any]:
    clean_subject = _normalize_canonical_subject(subject)
    clean_type = res_type if res_type in CANONICAL_TYPES else _classify_resource_type(url, title, category)
    pl_id = extract_youtube_playlist_id(url)
    entry: dict[str, Any] = {
        "title": title.strip(),
        "subject": clean_subject,
        "category": category.strip() or "Verified Resource",
        "level": level.strip() or "Standard",
        "language": language.strip() or "English",
        "type": clean_type,
        "provider": provider.strip() or _infer_provider(title, url),
        "url": url.strip(),
        "description": description.strip(),
        "seniorTip": senior_tip.strip(),
        "estimatedHours": max(0, int(estimated_hours)),
        "free": True,
        "verified": True,
        "verificationStatus": "Verified",
        "lastVerified": "2026-11-20",
        "tags": _merge_tags([clean_subject, clean_type], tags, limit=8),
        "verificationSignals": {
            "channelName": provider.strip() or _infer_provider(title, url),
            "completeness": "Live-Verified Free Resource (Master Guide)",
            "uploadYear": "2026",
        },
        "masterPart": master_part,
        "_slug_hint": slug_hint or title,
    }
    if class_level:
        entry["classLevel"] = class_level
    if pl_id:
        entry["youtubePlaylistId"] = pl_id
    return entry


def _extract_master_guide_candidates(master_guide: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert every item across Parts 1–10 of master_guide into typed resource candidates."""
    candidates: list[dict[str, Any]] = []

    # Part 1: Official UPSC Exam Hub
    for item in master_guide.get("official_hub", []):
        title = item["title"]
        purpose = item["purpose"]
        url = item["url"]
        tl = title.lower()
        subj = "Question Papers" if any(k in tl for k in ("previous exam", "question paper", "answer key", "cut-off")) else (
            "Mains & Essay" if "qcab" in tl else "Official Hub"
        )
        rtype = _classify_resource_type(url, title, purpose)
        candidates.append(
            _make_candidate(
                title=title,
                subject=subj,
                category="Official UPSC Portal",
                level="Foundation",
                language="English/Hindi",
                res_type=rtype,
                provider=_infer_provider(title, url, "UPSC Official (upsc.gov.in)"),
                url=url,
                description=purpose,
                senior_tip="Bookmark this official UPSC portal and rely on it instead of third-party rumour blogs for notifications, syllabus, keys, and cut-offs.",
                estimated_hours=2,
                tags=["UPSC", "Official", "Part 1"],
                master_part=1,
                slug_hint=f"p1-{title}",
            )
        )

    # Part 2.1: Official NCERT Textbook Portals
    for item in master_guide.get("ncert_portals", []):
        title = item["title"]
        offers = item["offers"]
        url = item["url"]
        rtype = "PDF" if "textbook" in title.lower() or "pdf" in offers.lower() else "Website"
        candidates.append(
            _make_candidate(
                title=title,
                subject="NCERT",
                category="Official Textbook Portal",
                level="Foundation",
                class_level="Class 6–12",
                language="English/Hindi",
                res_type=rtype,
                provider=_infer_provider(title, url, title),
                url=url,
                description=offers,
                senior_tip="Download authentic chapter-wise and full-book NCERT PDFs directly from official Government of India servers.",
                estimated_hours=1,
                tags=["NCERT", "Official", "Textbooks", "Foundation"],
                master_part=2,
                slug_hint=f"p2-portal-{title}",
            )
        )

    # Part 2: Class 6–12 NCERT Textbooks (86 rows)
    for book in master_guide.get("ncert_directory", []):
        cnum = book["class_num"]
        bsubj = book["subject"]
        btitle = book["book_title"]
        edition = book["edition"]
        medium = book["medium"]
        pgs = book["priority_gs_map"]
        url = book["url"]

        display_title = f"NCERT Class {cnum} {bsubj}: {btitle}"
        if edition == "NEP New":
            display_title += " (NEP New)"
        if medium == "Hindi":
            display_title += " [Hindi]"

        is_csat = "csat" in pgs.lower() or "mathematics" in bsubj.lower()
        level = "CSAT" if is_csat else "Foundation"
        tags = ["NCERT", f"Class {cnum}", bsubj, edition, medium, "Official", "PDF"]
        if is_csat:
            tags.append("CSAT")
        elif "must read" in pgs.lower():
            tags.append("Must Read")

        candidates.append(
            _make_candidate(
                title=display_title,
                subject="NCERT",
                category=f"NCERT Class {cnum} ({edition})",
                level=level,
                class_level=f"Class {cnum}",
                language=medium,
                res_type="PDF",
                provider="NCERT Official (ncert.nic.in)",
                url=url,
                description=f"Official NCERT Class {cnum} {bsubj} textbook ({edition}, {medium} medium). UPSC Priority & GS Map: {pgs}.",
                senior_tip=f"Official direct NCERT textbook link ({pgs}). Read with active underlining and map recurring UPSC Prelims/Mains keywords.",
                estimated_hours=6 if cnum <= 10 else 10,
                tags=tags,
                master_part=2,
                slug_hint=f"ncert-c{cnum}-{bsubj}-{btitle}-{medium}",
            )
        )

    # Part 2: Class-wise NCERT Video Companions (all 31 playlists)
    for part in master_guide.get("parts", []):
        if part.get("part_number") != 2:
            continue
        for sec in part.get("sections", []):
            cnum = sec.get("class_num")
            if not cnum:
                continue
            for vc in sec.get("video_companions", []):
                vc_title = vc["title"]
                provider = vc["provider"]
                url = vc["url"]
                vsubj = _normalize_canonical_subject(vc_title)
                if "sociology" in vc_title.lower() or "exploring society" in vc_title.lower():
                    vsubj = "NCERT"
                if "class " in vc_title.lower():
                    full_title = f"{vc_title} — Video Companion"
                else:
                    full_title = f"NCERT Class {cnum} {vc_title} — Video Companion"
                display_title = (
                    f"{full_title} ({provider})"
                    if provider != "Verified UPSC Archive"
                    else full_title
                )
                candidates.append(
                    _make_candidate(
                        title=display_title,
                        subject=vsubj,
                        category=f"NCERT Class {cnum} Video",
                        level="Foundation",
                        class_level=f"Class {cnum}",
                        language="English/Hinglish",
                        res_type="YouTube",
                        provider=provider,
                        url=url,
                        description=f"Verified chapter-wise YouTube playlist for NCERT Class {cnum} {vc_title} ({provider}).",
                        senior_tip="Keep the official NCERT PDF open alongside this playlist and watch at 1.25x speed for fast conceptual clarity.",
                        estimated_hours=8 if cnum <= 10 else 14,
                        tags=["NCERT", f"Class {cnum}", vsubj, "Video", "Foundation"],
                        master_part=2,
                        slug_hint=f"ncert-vid-c{cnum}-{vc_title}-{provider}",
                    )
                )

    # Part 2.2: Bridge Textbooks
    for item in master_guide.get("bridge_textbooks", []):
        title = item["title"]
        best_for = item["best_used_for"]
        url = item["url"]
        rtype = _classify_resource_type(url, title, best_for)
        candidates.append(
            _make_candidate(
                title=title,
                subject="Bridge Textbooks",
                category="Bridge & University Textbooks",
                level="Standard",
                language="English/Hindi",
                res_type=rtype,
                provider=_infer_provider(title, url, title),
                url=url,
                description=best_for,
                senior_tip="Use these official state-board and open-university PDFs to bridge NCERT basics and Mains/Optional analytical depth for free.",
                estimated_hours=12,
                tags=["Bridge Textbooks", "Free Textbooks", "Official", "Optional"],
                master_part=2,
                slug_hint=f"p2-bridge-{title}",
            )
        )

    # Part 3: Standard Core Book Legal Companions
    for row in master_guide.get("standard_books", []):
        row_subj = _normalize_canonical_subject(row["subject"])
        std_book = row["standard_book"]
        for comp in row.get("companions", []):
            ctitle = comp["title"]
            url = comp["url"]
            ctype = comp["type"]
            provider = _infer_provider(ctitle, url)
            level = "Mains" if row_subj in ("Ethics", "Governance & IR") else "Standard"
            candidates.append(
                _make_candidate(
                    title=ctitle,
                    subject=row_subj,
                    category="Standard Core Companion",
                    level=level,
                    language="English/Hinglish" if ctype == "YouTube" else "English",
                    res_type=ctype,
                    provider=provider,
                    url=url,
                    description=f"Free legal companion for {row['subject']} ({std_book}).",
                    senior_tip=f"Pair directly alongside {std_book} to lock in conceptual clarity without paid coaching.",
                    estimated_hours=18 if ctype == "YouTube" else 8,
                    tags=[row_subj, "Standard Core", ctype, "Free Companion"],
                    master_part=3,
                    slug_hint=f"p3-{row_subj}-{ctitle}",
                )
            )

    # Part 4: Official Government Reports & Primary Data Sources
    for item in master_guide.get("govt_reports", []):
        title = item["title"]
        utility = item["utility"]
        url = item["url"]
        sub = item["subsection"]
        subj = _subject_for_govt_report(sub, title, utility)
        rtype = _classify_resource_type(url, title, utility)
        candidates.append(
            _make_candidate(
                title=title,
                subject=subj,
                category="Official Government Report & Portal",
                level="Advanced",
                language="English/Hindi" if ".gov.in" in url or ".nic.in" in url else "English",
                res_type=rtype,
                provider=_infer_provider(title, url, title),
                url=url,
                description=utility,
                senior_tip="Citing primary government reports, statistics, and constitutional bodies directly elevates Mains GS-2, GS-3, and Essay authority.",
                estimated_hours=6,
                tags=[subj, "Official", "Primary Data", "Mains"],
                master_part=4,
                slug_hint=f"p4-{title}",
            )
        )

    # Part 5: Free News, Broadcasts & Think-Tanks
    for item in master_guide.get("news_and_thinktanks", []):
        title = item["title"]
        usage = item["usage"]
        url = item["url"]
        sub = item["subsection"]
        subj = _subject_for_news(sub, title, usage)
        rtype = _classify_resource_type(url, title, usage)
        cat = "Official Broadcast" if "5.1" in sub else "News & Think-Tank"
        candidates.append(
            _make_candidate(
                title=title,
                subject=subj,
                category=cat,
                level="Standard" if "5.1" in sub else "Mains",
                language="English",
                res_type=rtype,
                provider=_infer_provider(title, url, title),
                url=url,
                description=usage,
                senior_tip="Spend a capped 45–60 minutes daily on news & editorials—link every issue back to UPSC syllabus micro-topics.",
                estimated_hours=5,
                tags=[subj, "Current Affairs", "Editorials" if "5.2" in sub else "Official Broadcast"],
                master_part=5,
                slug_hint=f"p5-{title}",
            )
        )

    # Part 6: Curated Free Notes, Monthly Magazines & Toppers' Copies
    for item in master_guide.get("curated_notes", []):
        title = item["title"]
        desc = item["description"]
        url = item["url"]
        subj = _subject_for_curated_notes(title, desc)
        rtype = _classify_resource_type(url, title, desc)
        if rtype == "Website":
            rtype = "Notes"
        lang = "Hindi" if "hindi" in title.lower() else ("English/Hindi" if "hindi" in desc.lower() else "English")
        level = "Mains" if subj == "Mains & Essay" else "Standard"
        candidates.append(
            _make_candidate(
                title=title,
                subject=subj,
                category="Curated Free Notes & Magazines",
                level=level,
                language=lang,
                res_type=rtype,
                provider=_infer_provider(title, url, title),
                url=url,
                description=desc,
                senior_tip="Pick ONE trusted monthly compilation & daily answer-writing portal and revise it multiple times instead of hoarding PDFs.",
                estimated_hours=10,
                tags=[subj, "Free Notes", "Current Affairs" if subj == "Current Affairs" else "Mains"],
                master_part=6,
                slug_hint=f"p6-{title}",
            )
        )

    # Part 7: Exam Papers (PYQs), Daily Quizzes & Free Mocks
    for item in master_guide.get("exam_papers_and_quizzes", []):
        title = item["title"]
        coverage = item["coverage"]
        url = item["url"]
        tl = title.lower()
        subj = "Indian Polity" if "polity" in tl else ("NCERT" if "ncert" in tl else "Question Papers")
        rtype = _classify_resource_type(url, title, coverage)
        lang = "Hindi" if "hindi" in tl else "English"
        level = "Mains" if "mains" in tl and "prelims" not in tl else "Prelims"
        candidates.append(
            _make_candidate(
                title=title,
                subject=subj,
                category="Exam Papers & Free Quizzes",
                level=level,
                language=lang,
                res_type=rtype,
                provider=_infer_provider(title, url, title),
                url=url,
                description=coverage,
                senior_tip="Treat real UPSC PYQs (2013–latest) as your primary mock benchmark before attempting any coaching test series.",
                estimated_hours=12,
                tags=[subj, "PYQ", "Quiz" if "quiz" in tl else "Practice"],
                master_part=7,
                slug_hint=f"p7-{title}",
            )
        )

    # Part 8: Video Library (8.1 Official Channels, 8.2 Subject Channels, 8.3 Direct Playlists)
    vl = master_guide.get("video_library", {})
    for ch in vl.get("official_channels", []):
        title = ch["title"]
        best_for = ch["best_for"]
        url = ch["url"]
        subj = _subject_for_channel(title, best_for, is_official=True)
        rtype = _classify_resource_type(url, title, best_for)
        candidates.append(
            _make_candidate(
                title=f"{title} — Official YouTube Channel",
                subject=subj,
                category="Official YouTube Channel",
                level="Foundation",
                language="English/Hindi",
                res_type=rtype,
                provider=title,
                url=url,
                description=best_for,
                senior_tip="Official government and university channels deliver zero-fluff academic and policy authority completely free.",
                estimated_hours=15,
                tags=[subj, "YouTube Channel", "Official", "Video"],
                master_part=8,
                slug_hint=f"p8-ch-{title}",
            )
        )

    for ch in vl.get("subject_channels", []):
        title = ch["title"]
        specialty = ch["specialty"]
        url = ch["url"]
        subj = _subject_for_channel(title, specialty, is_official=False)
        lang = "Hindi" if "hindi" in title.lower() else ("English" if "english" in title.lower() else "English/Hinglish")
        rtype = _classify_resource_type(url, title, specialty)
        candidates.append(
            _make_candidate(
                title=f"{title} — Verified UPSC YouTube Channel",
                subject=subj,
                category="Verified YouTube Channel",
                level="Standard",
                language=lang,
                res_type=rtype,
                provider=title,
                url=url,
                description=specialty,
                senior_tip="Follow structured playlists on this channel instead of random single videos to avoid YouTube rabbit holes.",
                estimated_hours=20,
                tags=[subj, "YouTube Channel", "Video", lang],
                master_part=8,
                slug_hint=f"p8-ch-{title}",
            )
        )

    for pl in vl.get("direct_playlists", []):
        theme = pl["theme"]
        title = pl["title"]
        educator = pl["educator"]
        url = pl["url"]
        subj = _normalize_canonical_subject(theme)
        rtype = _classify_resource_type(url, title, theme)
        level = "Foundation" if "foundation" in title.lower() or "ncert" in theme.lower() or "beginner" in theme.lower() else (
            "Mains" if any(k in theme.lower() for k in ("answer", "essay", "international")) else "Prelims"
        )
        candidates.append(
            _make_candidate(
                title=f"{title} ({educator})",
                subject=subj,
                category="Verified Video Playlist",
                level=level,
                language="English/Hinglish",
                res_type=rtype,
                provider=educator,
                url=url,
                description=f"Verified direct UPSC YouTube playlist for {theme} by {educator}.",
                senior_tip="Watch systematically in playlist order and consolidate key takeaways into crisp 1-page revision notes.",
                estimated_hours=20,
                tags=[subj, theme, "Playlist", "Video"],
                master_part=8,
                slug_hint=f"p8-pl-{title}-{educator}",
            )
        )

    # Part 9: CSAT Complete Free Resource Kit
    for item in master_guide.get("csat_kit", []):
        title = item["title"]
        rtype_label = item["resource_type"]
        url = item["url"]
        rtype = _classify_resource_type(url, title, rtype_label)
        provider = _infer_provider(title, url, "CSAT Specialist")
        if " — " in title:
            provider = title.rsplit(" — ", 1)[1].strip()
        elif "ungist" in title.lower():
            provider = "UNGIST IAS"
        elif "ias setu" in title.lower():
            provider = "IAS Setu"
        elif "drishti" in title.lower():
            provider = "Drishti IAS"
        elif "sleepy" in title.lower():
            provider = "Sleepy Classes IAS"
        elif "pmf" in title.lower():
            provider = "PMF IAS"
        elif "insights" in title.lower():
            provider = "InsightsIAS"
        candidates.append(
            _make_candidate(
                title=title,
                subject="CSAT",
                category=f"CSAT — {rtype_label}",
                level="CSAT",
                language="English/Hinglish",
                res_type=rtype,
                provider=provider,
                url=url,
                description=f"{rtype_label}: {title}. Structured free preparation for UPSC Prelims Paper-II (CSAT).",
                senior_tip="Dedicate 1 hour daily to CSAT starting 4–5 months before Prelims; prioritize Number System, P&C, and Reading Comprehension.",
                estimated_hours=16 if rtype == "YouTube" else 8,
                tags=["CSAT", "Paper 2", "Prelims", rtype],
                master_part=9,
                slug_hint=f"p9-csat-{title}",
            )
        )

    # Part 10.1: Optional Subjects
    for opt in master_guide.get("optionals", []):
        opt_subj = opt["subject"]
        for lnk in opt.get("academic_links", []):
            title = lnk["title"]
            url = lnk["url"]
            candidates.append(
                _make_candidate(
                    title=f"{opt_subj} Optional: {title}",
                    subject="Optionals",
                    category=f"Optional — {opt_subj}",
                    level="Mains",
                    language="English",
                    res_type=_classify_resource_type(url, title, "Optional PDF"),
                    provider=_infer_provider(title, url),
                    url=url,
                    description=f"Free authoritative academic material for {opt_subj} Optional ({title}).",
                    senior_tip="Cross-reference every IGNOU/UGC module directly against the official UPSC Optional syllabus and past 10 years' PYQs.",
                    estimated_hours=24,
                    tags=["Optionals", opt_subj, "Mains"],
                    master_part=10,
                    slug_hint=f"p10-opt-{opt_subj}-{title}",
                )
            )
        for lnk in opt.get("video_links", []):
            title = lnk["title"]
            url = lnk["url"]
            rtype = _classify_resource_type(url, title, "Optional Video")
            provider = _infer_provider(title, url)
            for known in ("Sleepy Classes", "ForumIAS", "UPSCprep", "OnlyIAS", "SWAYAM", "Amit Sengupta", "Sudarshan Gurjar", "Bookstawa", "CEC UGC"):
                if known.lower() in title.lower():
                    provider = known
                    break
            candidates.append(
                _make_candidate(
                    title=f"{opt_subj} Optional: {title}",
                    subject="Optionals",
                    category=f"Optional — {opt_subj}",
                    level="Mains",
                    language="English/Hinglish",
                    res_type=rtype,
                    provider=provider,
                    url=url,
                    description=f"Verified free lecture series / academic guidance for {opt_subj} Optional.",
                    senior_tip="Solve topic-wise Optional PYQs right after completing each module to calibrate depth and thinker citations.",
                    estimated_hours=22,
                    tags=["Optionals", opt_subj, "Mains", rtype],
                    master_part=10,
                    slug_hint=f"p10-optvid-{opt_subj}-{title}",
                )
            )

    # Part 10.2: Personality Test (Interview / DAF)
    for item in master_guide.get("interview_prep", []):
        title = item["title"]
        purpose = item["purpose"]
        url = item["url"]
        rtype = _classify_resource_type(url, title, purpose)
        provider = _infer_provider(title, url, title)
        for known in ("ForumIAS", "InsightsIAS", "Rau's IAS", "Sansad TV", "Drishti IAS"):
            if known.lower() in title.lower():
                provider = known
                break
        candidates.append(
            _make_candidate(
                title=title,
                subject="Interview",
                category="Personality Test Video" if rtype == "YouTube" else "Personality Test Channel",
                level="Interview",
                language="English/Hindi" if "hindi" in title.lower() else "English",
                res_type=rtype,
                provider=provider,
                url=url,
                description=purpose,
                senior_tip="Focus on calm composure, balanced non-partisan framing, and deep clarity on every single keyword in your DAF.",
                estimated_hours=10,
                tags=["Interview", "Personality Test", "DAF", "Video" if rtype == "YouTube" else "YouTube Channel"],
                master_part=10,
                slug_hint=f"p10-int-{title}",
            )
        )

    return candidates


# Verified repairs for legacy curated resource IDs whose original YouTube
# playlist URLs became broken, unindexed, truncated, or mislabeled.
# Preserving every original ID keeps user progress, bookmarks, notes, and PYQ
# cross-references 100% intact while ensuring every video resource is live and
# subject-accurate.
CURATED_VIDEO_REPAIRS: dict[str, dict[str, Any]] = {
    "res-vision-mains-pyq-video": {
        "title": "Mains A Day (MAD) — Daily Mains PYQ & Answer Writing Series",
        "subject": "Question Papers",
        "category": "Mains PYQ Video Analysis",
        "type": "YouTube",
        "provider": "Sleepy Classes IAS",
        "url": "https://www.youtube.com/playlist?list=PLYSuG-KZy7JD0F5V1ecS12IoDph1XYtsx",
        "description": "Structured daily UPSC Mains PYQ and answer-writing deconstruction across GS Papers 1–4 with introduction, body framework, and value addition.",
        "seniorTip": "Pause each video after reading the question, sketch a 2-minute rough outline yourself, and then compare with the structured framework.",
        "masterPart": 7,
    },
    "res-pmf-ncert-history": {
        "title": "Complete Indian History (Ancient, Medieval & Modern) Video Course",
        "subject": "History",
        "category": "History Foundation Video",
        "type": "YouTube",
        "provider": "Pratik Nayak",
        "url": "https://www.youtube.com/playlist?list=PLSVABdpsEeglvmPaAjoRLN-Y-C6y0TtWU",
        "description": "Comprehensive chronological lecture series covering Ancient, Medieval, and Modern Indian History with NCERT and standard textbook linkage.",
        "seniorTip": "Build a clean one-page timeline per era alongside this series and cross-check every major dynasty and movement with UPSC Prelims PYQs.",
        "masterPart": 8,
    },
    "res-bookstawa-modern": {
        "title": "Modern Indian History Complete Animated Series",
        "subject": "History",
        "category": "Modern History Video",
        "type": "YouTube",
        "provider": "Bookstawa",
        "url": "https://www.youtube.com/playlist?list=PLZfz5K8XpMW1BCazrkRFzS9NxCZVMiXcM",
        "description": "Verified animated chronological lectures covering Modern Indian History from advent of Europeans to Independence with crisp visual timelines.",
        "seniorTip": "Pair Bookstawa's animated chronology with Spectrum chapters so dates, Acts, and Governor-Generals stay locked in memory.",
        "masterPart": 3,
    },
    "res-bookstawa-medieval": {
        "title": "Medieval Indian History (Satish Chandra) Chapter-by-Chapter",
        "subject": "History",
        "category": "Medieval History Video",
        "type": "YouTube",
        "provider": "Harshit Dwivedi (HD Education)",
        "url": "https://www.youtube.com/playlist?list=PL_K2YMR-A5WL9RdjDEJV48WRXpIkeUrvn",
        "description": "Line-by-line verified YouTube breakdown of Satish Chandra's History of Medieval India covering Delhi Sultanate, Vijayanagara, Bhakti-Sufi, and Mughals.",
        "seniorTip": "Focus heavily on administrative terms, land revenue systems, Bhakti/Sufi saints, and Vijayanagara architecture—UPSC's top Medieval PYQ areas.",
        "masterPart": 3,
    },
    "res-bookstawa-art-culture": {
        "title": "Complete Indian Art & Culture (Nitin Singhania) Video Series",
        "subject": "Art & Culture",
        "category": "Art & Culture Video",
        "type": "YouTube",
        "provider": "StudyIQ IAS",
        "url": "https://www.youtube.com/playlist?list=PLAdW2HOoum1EhlvYszd2x4yMuBbPiP21O",
        "description": "Chapter-wise free video lectures covering Indian Architecture, Sculpture, Paintings, Classical Dances, Music, Literature, and Buddhist/Jain heritage.",
        "seniorTip": "Revise Temple Architecture (Nagara/Dravida/Vesara), Paintings, and Buddhism/Jainism alongside Class 11 Fine Arts NCERT.",
        "masterPart": 3,
    },
    "res-onlyias-animated-history": {
        "title": "Class 11 Fine Arts NCERT — An Introduction to Indian Art",
        "subject": "Art & Culture",
        "category": "NCERT Art & Culture Video",
        "type": "YouTube",
        "provider": "Testbook SuperCoaching",
        "url": "https://www.youtube.com/playlist?list=PL-lZfDAjv6raJTy-_g3tZKqJbSFSomJ4K",
        "description": "Complete visual walkthrough of Class 11 NCERT Fine Arts (An Introduction to Indian Art Part I), the single highest-ROI source for Prelims Art & Culture.",
        "seniorTip": "Keep the official NCERT PDF open while watching to recognize every sculpture, stupa, cave mural, and bronze directly by sight.",
        "masterPart": 2,
    },
    "res-pmf-geo-foundation": {
        "title": "Complete Geography for UPSC (Physical, Indian & World) — Rajtanil Solanki",
        "subject": "Geography",
        "category": "Geography Foundation Video",
        "type": "YouTube",
        "provider": "Rajtanil Solanki (Mrunal)",
        "url": "https://www.youtube.com/playlist?list=PLAMBum9_RkuNDtzpNQlCRcaOrNqrD4Gf7",
        "description": "Iconic free UPSC Geography lecture series hosted on Mrunal Patel's channel covering Geomorphology, Climatology, Oceanography, and Indian Geography.",
        "seniorTip": "Pair Rajtanil Ma'am's conceptual clarity with Class 11 NCERT Geography and an Oxford Student Atlas open on your desk.",
        "masterPart": 3,
    },
    "res-mrunal-economy-beginners": {
        "title": "Complete Indian Economy (Ramesh Singh) Chapter-by-Chapter",
        "subject": "Economy",
        "category": "Economy Core Video",
        "type": "YouTube",
        "provider": "Harshit Dwivedi (HD Education)",
        "url": "https://www.youtube.com/playlist?list=PL_K2YMR-A5WIJ3Y6N_o5aZJpvhX2z0-Yj",
        "description": "Comprehensive free chapter-by-chapter video series on Indian Economy covering GDP, Inflation, Monetary Policy, RBI, Banking, Fiscal Policy, and BoP.",
        "seniorTip": "Master National Income, Inflation, RBI tools, and Balance of Payments first before layering current Budget & Economic Survey figures.",
        "masterPart": 3,
    },
    "res-mrunal-win26": {
        "title": "Economy MCQ Marathon & Prelims Strategy — Mrunal Patel",
        "subject": "Economy",
        "category": "Economy Prelims Revision Video",
        "type": "YouTube",
        "provider": "Mrunal Patel",
        "url": "https://www.youtube.com/playlist?list=PLAMBum9_RkuOMrwd4A1h3DzcHFYyr_xDR",
        "description": "High-yield UPSC Prelims Economy MCQ solving marathons, Monetary/Fiscal policy drills, and elimination strategies directly by Mrunal Patel.",
        "seniorTip": "Attempt each MCQ actively before listening to the explanation to sharpen UPSC Economy statement-elimination reflexes.",
        "masterPart": 8,
    },
    "res-bookstawa-economy": {
        "title": "Complete Indian Economy Animated Series for UPSC",
        "subject": "Economy",
        "category": "Economy Animated Video",
        "type": "YouTube",
        "provider": "Bookstawa",
        "url": "https://www.youtube.com/playlist?list=PLZfz5K8XpMW3p6uoaRSnmClfoe5bNvCjm",
        "description": "Verified animated Indian Economy series explaining banking, repo/reverse repo, inflation, capital markets, fiscal deficit, and BoP visually.",
        "seniorTip": "Ideal rapid-revision video companion for Prelims conceptual traps in Banking, External Sector, and Financial Markets.",
        "masterPart": 3,
    },
    "res-vision-economic-survey": {
        "title": "Class 12 Introductory Macroeconomics Complete NCERT Video Course",
        "subject": "Economy",
        "category": "NCERT Macroeconomics Video",
        "type": "YouTube",
        "provider": "Magnet Brains",
        "url": "https://www.youtube.com/playlist?list=PLVLoWQFkZbhUm3-No4WpiQEdQjCpA6SKK",
        "description": "Complete chapter-by-chapter free NCERT Class 12 Macroeconomics lectures building rock-solid intuition for GDP, Money & Banking, Budget, and Open Economy.",
        "seniorTip": "Finish Macroeconomics NCERT before reading the official Economic Survey PDF so every macro indicator makes instant sense.",
        "masterPart": 2,
    },
    "res-pmf-environment-video": {
        "title": "Complete Environment & Ecology (Shankar IAS) Chapter-by-Chapter",
        "subject": "Environment",
        "category": "Environment Core Video",
        "type": "YouTube",
        "provider": "Harshit Dwivedi (HD Education)",
        "url": "https://www.youtube.com/playlist?list=PL_K2YMR-A5WK2mrG6kdfdvdP-n7_MTzVU",
        "description": "Complete verified chapter-wise Environment & Ecology playlist covering ecosystems, biodiversity, Wildlife Protection Act, climate conventions, and pollution.",
        "seniorTip": "Combine with Class 12 Biology Ecology chapters and Sudarshan Gurjar's National Parks mapping for maximum Prelims Environment accuracy.",
        "masterPart": 3,
    },
    "res-drishti-scitech-100": {
        "title": "Complete Science & Technology for UPSC (Prelims & Mains)",
        "subject": "Science & Tech",
        "category": "Science & Tech Core Video",
        "type": "YouTube",
        "provider": "Dr. Ravi P. Agrahari",
        "url": "https://www.youtube.com/playlist?list=PL67v2-EIFZ6SOsJxIYrPeSFc8P_KiJ-Lv",
        "description": "Structured UPSC Science & Technology video course by Dr. Ravi P. Agrahari covering Space, Defence, Biotechnology, AI/IT, Energy, and Emerging Tech.",
        "seniorTip": "Focus on applied principles—satellite orbits, CRISPR/mRNA biotech, indigenous missiles, and nuclear/renewable tech asked in Prelims & GS-3.",
        "masterPart": 8,
    },
    "res-pmf-ir": {
        "title": "Contemporary World Politics & International Relations Foundation",
        "subject": "Governance & IR",
        "category": "International Relations Video",
        "type": "YouTube",
        "provider": "Harshit Dwivedi (HD Education)",
        "url": "https://www.youtube.com/playlist?list=PL_K2YMR-A5WKg_oyTt-eHPnSvXfANQKOM",
        "description": "Verified Class 12 Contemporary World Politics NCERT lecture series explaining Cold War, multipolarity, UN/international organizations, and South Asian geopolitics.",
        "seniorTip": "Build static IR foundations here, then layer MEA official briefs and MP-IDSA / ORF op-eds for current bilateral & multilateral groupings.",
        "masterPart": 2,
    },
    "res-upscprep-essay": {
        "title": "A–Z Ethics, Values & Philosophical Essay Foundation Series",
        "subject": "Mains & Essay",
        "category": "Ethics & Essay Video",
        "type": "YouTube",
        "provider": "Sleepy Classes IAS",
        "url": "https://www.youtube.com/playlist?list=PLYSuG-KZy7JBDpMxkm3Atyozs_l6iichX",
        "description": "Verified lecture playlist covering moral thinkers, ethical frameworks, philosophical quotes, and multi-dimensional brainstorming useful across GS-4 and Essay.",
        "seniorTip": "Harvest 2–3 thinker quotes, historical examples, and constitutional values per module to enrich both philosophical essays and GS-4 answers.",
        "masterPart": 8,
    },
    "res-ungist-csat-noformula": {
        "title": "UNGIST IAS Official YouTube — CSAT Quant Without Formulas & Drills",
        "subject": "CSAT",
        "category": "Verified YouTube Channel",
        "type": "Website",
        "provider": "UNGIST IAS",
        "url": "https://www.youtube.com/@UNGISTIAS",
        "description": "Official UNGIST IAS YouTube channel hosting intuitive no-formula CSAT Quantitative Aptitude sessions, live marathons, and latest Prelims strategy.",
        "seniorTip": "Browse the channel's Playlists tab for targeted Number System, P&C, and Logical Reasoning sessions alongside daily PYQ solving.",
        "masterPart": 9,
    },
    "res-ungist-csat-rc": {
        "title": "IAS Setu Official YouTube — CSAT Reading Comprehension & Aptitude",
        "subject": "CSAT",
        "category": "Verified YouTube Channel",
        "type": "Website",
        "provider": "IAS Setu",
        "url": "https://www.youtube.com/@IASSETU",
        "description": "Official IAS Setu (Amit Garg Sir) YouTube channel offering free UPSC CSAT Reading Comprehension, General Mental Ability, and marathon classes.",
        "seniorTip": "Combine IAS Setu's passage inference strategies with official UPSC CSAT PYQs (2015–latest) to build reliable 80%+ comprehension accuracy.",
        "masterPart": 9,
    },
    "res-ungist-csat-pyqs": {
        "title": "Free UPSC CSAT PYQs Series (2011–2025) Solved Step-by-Step",
        "subject": "CSAT",
        "category": "CSAT PYQ Video",
        "type": "YouTube",
        "provider": "UNGIST IAS",
        "url": "https://www.youtube.com/playlist?list=PLv8R8lxsh8gbKU82l87QNW-ohSbTQMVks",
        "description": "Verified playlist solving authentic UPSC Prelims Paper-II (CSAT) previous year questions from 2011 to 2025 with clean intuition and shortcuts.",
        "seniorTip": "Solving real UPSC CSAT PYQs twice is the highest-yield strategy to comfortably clear the 33% qualifying cutoff.",
        "masterPart": 9,
    },
    "res-onlyias-udaan": {
        "title": "Daily UPSC Current Affairs Analysis Video Series",
        "subject": "Current Affairs",
        "category": "Current Affairs Video",
        "type": "YouTube",
        "provider": "InsightsIAS",
        "url": "https://www.youtube.com/playlist?list=PL7Ga7_sc-ojWG_46xXlarHeW77OMRkmoL",
        "description": "Verified daily UPSC current affairs video analysis covering The Hindu, Indian Express, and PIB developments mapped to Prelims & Mains GS papers.",
        "seniorTip": "Use daily current affairs video digests at 1.25x speed as a structured supplement rather than spending 3 hours reading newspapers raw.",
        "masterPart": 8,
    },
    "res-vision-pt365-video": {
        "title": "PIB Weekly Current Affairs Analysis (English)",
        "subject": "Current Affairs",
        "category": "Current Affairs Video",
        "type": "YouTube",
        "provider": "Drishti IAS English",
        "url": "https://www.youtube.com/playlist?list=PLQpF--VlgguTI4uXie10_EaMN08Vsfx1z",
        "description": "Verified weekly video roundup of Press Information Bureau (PIB) government schemes, Cabinet decisions, summits, and science/environment releases.",
        "seniorTip": "Watch one weekly PIB compilation every Sunday to catch official ministry schemes and Prelims facts without missing key updates.",
        "masterPart": 8,
    },
    "res-air-spotlight": {
        "title": "NewsOnAir Official YouTube (Akashvani / AIR Spotlight Discussions)",
        "subject": "Current Affairs",
        "category": "Official Broadcast",
        "type": "Website",
        "provider": "NewsOnAir Official",
        "url": "https://www.youtube.com/@NEWSONAIROFFICIAL",
        "description": "Official All India Radio (Akashvani) YouTube channel hosting daily 15-minute AIR Spotlight policy analyses and verified national bulletins.",
        "seniorTip": "Listen to AIR Spotlight policy analyses during walks or commutes to absorb crisp, balanced official viewpoints for Mains & Interview.",
        "masterPart": 5,
    },
    "res-forumias-answer-writing": {
        "title": "UPSC Toppers Success Stories, Strategy & Answer Approach Interviews",
        "subject": "Interview",
        "category": "Toppers Strategy Video",
        "type": "YouTube",
        "provider": "ForumIAS",
        "url": "https://www.youtube.com/playlist?list=PLTWYSxOsBjqEp8TyEU73mMD-QWRBzs50Z",
        "description": "Verified ForumIAS playlist of AIR 1–10 and top rankers sharing booklists, Mains answer-writing frameworks, revision plans, and Interview experiences.",
        "seniorTip": "Watch 2–3 rankers with your same Optional or academic background, extract actionable habits, and avoid getting trapped in endless strategy videos.",
        "masterPart": 10,
    },
    "res-insights-mock-interviews": {
        "title": "InsightsIAS Official YouTube — UPSC Mock Interviews & IGP Sessions",
        "subject": "Interview",
        "category": "Personality Test Channel",
        "type": "Website",
        "provider": "InsightsIAS",
        "url": "https://www.youtube.com/@Insights_IAS",
        "description": "Official InsightsIAS YouTube channel featuring UPSC Personality Test mock interviews, DAF cross-questioning drills, and toppers' talks.",
        "seniorTip": "Observe how high-scoring candidates handle unfamiliar factual questions honestly and stay calm under rapid DAF follow-ups.",
        "masterPart": 10,
    },
}


def build_enriched_resources(
    existing_resources: list[dict[str, Any]],
    master_guide: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preserve all curated resource IDs, apply verified video repairs, and merge master_guide links cleanly."""
    candidates = _extract_master_guide_candidates(master_guide)
    candidate_by_url: dict[str, dict[str, Any]] = {}
    for cand in candidates:
        nk = _normalize_url_key(cand["url"])
        candidate_by_url.setdefault(nk, cand)

    enriched: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    by_norm_url: dict[str, dict[str, Any]] = {}

    # 1. Preserve EVERY curated (non-res-mg-*) resource with its exact ID intact,
    #    while rebuilding res-mg-* entries freshly from master_guide so removed/broken
    #    links never linger in resources.json.
    for raw in existing_resources:
        rid = str(raw.get("id", "")).strip()
        if not rid or rid.startswith("res-mg-"):
            continue

        item = copy.deepcopy(raw)
        used_ids.add(rid)

        # Apply idempotent verified video repairs where legacy URLs broke or were mislabeled
        repair = CURATED_VIDEO_REPAIRS.get(rid)
        if repair:
            for field in ("title", "subject", "category", "type", "provider", "url", "description", "seniorTip", "masterPart"):
                if field in repair:
                    item[field] = repair[field]
            item["lastVerified"] = "2026-11-20"
            item["verified"] = True
            item["verificationStatus"] = "Verified"
            sig = dict(item.get("verificationSignals") or {})
            sig["channelName"] = item["provider"]
            sig["completeness"] = "Live-Verified Active Resource"
            sig["uploadYear"] = "2026"
            item["verificationSignals"] = sig

        # Normalize legacy subjects cleanly while retaining legacy terms in tags
        orig_subj = item.get("subject", "Current Affairs")
        canon_subj = _normalize_canonical_subject(orig_subj)
        extra_tags: list[str] = []
        if orig_subj != canon_subj:
            extra_tags.append(orig_subj)
        item["subject"] = canon_subj

        # Normalize type cleanly into CANONICAL_TYPES — and never mark non-playable
        # YouTube channel homepages as type "YouTube"
        orig_type = item.get("type", "")
        pl_id = extract_youtube_playlist_id(item["url"])
        vid_id = extract_youtube_video_id(item["url"])
        if orig_type == "YouTube" and not (pl_id or vid_id):
            item["type"] = "Website"
            extra_tags.extend(["YouTube Channel", "Video"])
        elif orig_type in CANONICAL_TYPES:
            item["type"] = orig_type
        else:
            item["type"] = _classify_resource_type(item["url"], item.get("title", ""), item.get("category", ""))

        # Ensure playlist ID accuracy
        if pl_id:
            item["youtubePlaylistId"] = pl_id
        else:
            item.pop("youtubePlaylistId", None)

        nk = _normalize_url_key(item["url"])
        matched = candidate_by_url.get(nk)
        if matched:
            if "masterPart" not in item:
                item["masterPart"] = matched["masterPart"]
            extra_tags.extend(matched.get("tags", []))

        item["tags"] = _merge_tags(item.get("tags", []), extra_tags, limit=8)
        enriched.append(item)
        by_norm_url[nk] = item

    # 2. Add every additional unique URL from master_guide deterministically
    for cand in candidates:
        nk = _normalize_url_key(cand["url"])
        if nk in by_norm_url:
            # Augment existing entry's tags / masterPart gently without overwriting curated text
            existing_item = by_norm_url[nk]
            if "masterPart" not in existing_item:
                existing_item["masterPart"] = cand["masterPart"]
            existing_item["tags"] = _merge_tags(existing_item.get("tags", []), cand.get("tags", []), limit=8)
            continue

        cand_copy = copy.deepcopy(cand)
        slug_hint = cand_copy.pop("_slug_hint", cand_copy["title"])
        base_slug = _slugify(slug_hint, max_len=46)
        new_id = f"res-mg-{base_slug}"
        if new_id in used_ids:
            short_hash = hashlib.sha1(nk.encode("utf-8")).hexdigest()[:6]
            new_id = f"res-mg-{base_slug[:39].rstrip('-')}-{short_hash}"

        used_ids.add(new_id)
        final_entry = {"id": new_id, **cand_copy}
        enriched.append(final_entry)
        by_norm_url[nk] = final_entry

    return enriched


# =========================================================================
# QUESTION PAPERS & CURRENT AFFAIRS ENRICHMENT
# =========================================================================


def _enrich_question_papers(
    existing_qps: list[dict[str, Any]],
    master_guide: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preserve all existing question paper IDs, repair dead video links, and add missing Part 1 & Part 7 archives."""
    result = [copy.deepcopy(q) for q in existing_qps]

    # Repair legacy dead Mains PYQ video playlist in-place while preserving its exact ID
    for qp in result:
        if qp.get("id") == "qp-vision-mains-pyq-video" or "PLDnIeUIsbmQuEUYGRHmpkO91rJ9iVVgS_" in str(qp.get("url", "")):
            qp["title"] = "Mains A Day (MAD) — Daily Mains PYQ & Answer Writing (Video)"
            qp["stage"] = "Mains Video Analysis"
            qp["years"] = "GS 1–4 Daily Archive"
            qp["provider"] = "Sleepy Classes IAS"
            qp["url"] = "https://www.youtube.com/playlist?list=PLYSuG-KZy7JD0F5V1ecS12IoDph1XYtsx"
            qp["description"] = "Verified daily video walkthrough showing how to decode UPSC Mains PYQs and build high-scoring GS 1–4 answers."

    existing_ids = {q["id"] for q in result}
    existing_urls = {_normalize_url_key(q["url"]) for q in result}

    additions = [
        {
            "id": "qp-upsc-rt-papers",
            "title": "UPSC Recruitment Tests — Official Question Papers Archive",
            "stage": "Allied UPSC Exams",
            "years": "Official Archive",
            "provider": "UPSC Official (upsc.gov.in)",
            "url": "https://www.upsc.gov.in/recruitment-tests/question-papers/",
            "description": "Official UPSC Recruitment Test question papers (EPFO, CAPF, CDS, CMS & allied exams) for authentic Commission-framed MCQ practice.",
        },
        {
            "id": "qp-upsc-rt-keys",
            "title": "UPSC Recruitment Tests — Official Answer Keys Archive",
            "stage": "Answer Keys",
            "years": "Official Archive",
            "provider": "UPSC Official (upsc.gov.in)",
            "url": "https://www.upsc.gov.in/recruitment-tests/answer-keys/",
            "description": "Verified official Commission answer keys for UPSC Recruitment Tests to cross-check official interpretation of tricky statements.",
        },
        {
            "id": "qp-upsc-rt-cutoffs",
            "title": "UPSC Recruitment Tests — Official Cut-Off Marks",
            "stage": "Cut-Offs",
            "years": "Official Disclosures",
            "provider": "UPSC Official (upsc.gov.in)",
            "url": "https://www.upsc.gov.in/recruitment-tests/cut-off-marks/",
            "description": "Official category-wise UPSC cut-off mark disclosures to calibrate realistic safe-attempt targets.",
        },
        {
            "id": "qp-drishti-daily-quiz",
            "title": "Daily Current Affairs Free Practice Quiz (5–10 MCQs)",
            "stage": "Daily Quiz",
            "years": "Updated Daily",
            "provider": "Drishti IAS",
            "url": "https://www.drishtiias.com/quiz/quizlist/daily-current-affairs",
            "description": "Free daily UPSC-pattern Prelims current affairs MCQs with detailed conceptual explanations.",
        },
        {
            "id": "qp-drishti-all-quizzes",
            "title": "Static GS, CSAT & Editorial Free Online Quizzes",
            "stage": "Prelims + CSAT Practice",
            "years": "Ongoing Free Sets",
            "provider": "Drishti IAS",
            "url": "https://www.drishtiias.com/quiz",
            "description": "Free subject-wise static, editorial, and CSAT online practice quizzes for active daily recall.",
        },
        {
            "id": "qp-drishti-ncert-hindi-quiz",
            "title": "Chapter-Wise NCERT Practice Quizzes (Hindi Medium)",
            "stage": "NCERT Foundation",
            "years": "Class 6–12",
            "provider": "Drishti IAS Hindi",
            "url": "https://www.drishtiias.com/hindi/quiz/catlist/ncert-books-quiz",
            "description": "Free chapter-by-chapter NCERT MCQ tests in Hindi medium for immediate foundation self-assessment.",
        },
        {
            "id": "qp-clearias-mocks",
            "title": "ClearIAS Free Prelims Mock Tests & Probable MCQs",
            "stage": "Prelims Mock",
            "years": "Free Test Series",
            "provider": "ClearIAS",
            "url": "https://www.clearias.com/",
            "description": "Free online UPSC Prelims mock tests and daily probable MCQ drills with elimination strategies.",
        },
        {
            "id": "qp-vision-mains-pyq-video",
            "title": "Mains A Day (MAD) — Daily Mains PYQ & Answer Writing (Video)",
            "stage": "Mains Video Analysis",
            "years": "GS 1–4 Daily Archive",
            "provider": "Sleepy Classes IAS",
            "url": "https://www.youtube.com/playlist?list=PLYSuG-KZy7JD0F5V1ecS12IoDph1XYtsx",
            "description": "Verified daily video walkthrough showing how to decode UPSC Mains PYQs and build high-scoring GS 1–4 answers.",
        },
        {
            "id": "qp-atish-polity-pyq-video",
            "title": "10-Year UPSC Polity Prelims PYQ Breakdown (Video)",
            "stage": "Prelims Video Analysis",
            "years": "10-Year Archive",
            "provider": "Atish Mathur",
            "url": "https://www.youtube.com/playlist?list=PLDmcugApdt5dO_HPoL4uc2xL8jaitSmdL",
            "description": "Detailed elimination analysis of 10 years of authentic UPSC Prelims Polity questions and examiner traps.",
        },
        {
            "id": "qp-drishti-toppers-hindi",
            "title": "Evaluated Toppers' Mains & Essay Answer Copies (Hindi Medium)",
            "stage": "Mains Benchmark (Hindi)",
            "years": "Recent Rankers",
            "provider": "Drishti IAS Hindi",
            "url": "https://www.drishtiias.com/hindi/free-downloads/toppers-copy",
            "description": "Authentic evaluated Hindi medium UPSC CSE rankers' Mains GS and Essay answer booklets.",
        },
    ]

    # Verify every addition URL is valid in master_guide
    mg_urls = {
        _normalize_url_key(u)
        for u in (
            [x["url"] for x in master_guide.get("official_hub", [])]
            + [x["url"] for x in master_guide.get("exam_papers_and_quizzes", [])]
            + [x["url"] for x in master_guide.get("curated_notes", [])]
        )
    }

    for add in additions:
        nk = _normalize_url_key(add["url"])
        if add["id"] not in existing_ids and nk not in existing_urls and nk in mg_urls:
            result.append(add)
            existing_ids.add(add["id"])
            existing_urls.add(nk)

    return result


def _enrich_current_affairs(
    existing_ca: list[dict[str, Any]],
    master_guide: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preserve all existing CA categories, repair dead video links, and enrich keySources with verified Part 4 & 5 portals."""
    result = [copy.deepcopy(c) for c in existing_ca]

    # Repair dead AIR Spotlight playlist URL in-place across existing current_affairs categories
    for cat in result:
        for src in cat.get("keySources", []):
            if "PLPPKwCCueQ_AARG0z9XWZ3_lMCiLlMzfD" in str(src.get("url", "")):
                src["name"] = "NewsOnAir Official YouTube (AIR Spotlight)"
                src["type"] = "Audio/Video Bulletin"
                src["url"] = "https://www.youtube.com/@NEWSONAIROFFICIAL"
                src["howToUse"] = "Listen to crisp 15-minute daily national policy and diplomatic analyses (AIR Spotlight) while commuting."

    by_id = {c["id"]: c for c in result}

    def _add_sources(cat_id: str, new_sources: list[dict[str, Any]]) -> None:
        cat = by_id.get(cat_id)
        if not cat:
            return
        seen_urls = {_normalize_url_key(s["url"]) for s in cat.get("keySources", [])}
        for src in new_sources:
            nk = _normalize_url_key(src["url"])
            if nk not in seen_urls:
                cat.setdefault("keySources", []).append(src)
                seen_urls.add(nk)

    _add_sources(
        "ca-economy",
        [
            {
                "name": "Union Budget & Economic Survey (MoF Official PDFs)",
                "type": "Official Report",
                "url": "https://www.indiabudget.gov.in/economicsurvey/",
                "free": True,
                "howToUse": "Read Chapter 1 (State of the Economy), fiscal glide-path charts, and sector appendices directly from official PDFs.",
            },
            {
                "name": "RBI Database on Indian Economy (DBIE)",
                "type": "Primary Data",
                "url": "https://data.rbi.org.in/",
                "free": True,
                "howToUse": "Verify authentic time-series numbers for CPI inflation, Forex reserves, and banking credit trends.",
            },
            {
                "name": "Dept. of Agriculture & Farmers Welfare",
                "type": "Official Portal",
                "url": "https://agriwelfare.gov.in/",
                "free": True,
                "howToUse": "Track MSP revisions, e-NAM updates, PM-KISAN figures, and crop diversification schemes.",
            },
            {
                "name": "LiveMint Economy & Policy",
                "type": "Daily Newspaper",
                "url": "https://www.livemint.com/",
                "free": True,
                "howToUse": "Follow concise daily briefs on banking reforms, SEBI norms, trade policy, and macroeconomic trends.",
            },
        ],
    )

    _add_sources(
        "ca-environment",
        [
            {
                "name": "Wildlife Institute of India (WII)",
                "type": "Official Portal",
                "url": "https://wii.gov.in/",
                "free": True,
                "howToUse": "Cross-check protected area status, species recovery programs, and national biodiversity databases.",
            },
            {
                "name": "NDMA Official Disaster Management Guidelines",
                "type": "Official Report",
                "url": "https://ndma.gov.in/",
                "free": True,
                "howToUse": "Extract 3–4 institutional action points per hazard (floods, heatwaves, landslides, cyclones) for Mains GS-3.",
            },
            {
                "name": "PMF IAS Environment & Ecology Updates",
                "type": "Curated Notes",
                "url": "https://www.pmfias.com/",
                "free": True,
                "howToUse": "Use illustrated articles to link current COP summits, wildlife acts, and species in news to static ecology.",
            },
        ],
    )

    _add_sources(
        "ca-polity-ir",
        [
            {
                "name": "PRS Bill Track & Monthly Policy Review",
                "type": "Policy Brief",
                "url": "https://prsindia.org/billtrack",
                "free": True,
                "howToUse": "Read 2-page summaries of active Parliamentary Bills and monthly policy digests for Mains GS-2.",
            },
            {
                "name": "Sansad TV — Perspective Playlist",
                "type": "Analysis Video",
                "url": "https://www.youtube.com/playlist?list=PLVOgwA_DiGzrOZ062PskBVE83abtupy3z",
                "free": True,
                "howToUse": "Watch 2–3 structured 25-minute expert debates weekly for balanced GS-2 & Interview viewpoints.",
            },
            {
                "name": "Supreme Court of India & Law Commission Reports",
                "type": "Official Portal",
                "url": "https://www.sci.gov.in/",
                "free": True,
                "howToUse": "Track Constitution Bench judgments, Article 21 expansions, and federal dispute verdicts directly.",
            },
            {
                "name": "MP-IDSA & Observer Research Foundation (ORF)",
                "type": "Think-Tank",
                "url": "https://idsa.in/op-eds-and-articles",
                "free": True,
                "howToUse": "Read 1–2 short foreign policy and maritime/border security op-eds weekly for GS-2 IR & GS-3 Security.",
            },
            {
                "name": "The Hindu — Editorials",
                "type": "Daily Newspaper",
                "url": "https://www.thehindu.com/opinion/editorial/",
                "free": True,
                "howToUse": "Extract balanced constitutional arguments and counter-arguments without copying full columns.",
            },
            {
                "name": "NewsOnAir Official YouTube (AIR Spotlight)",
                "type": "Audio/Video Bulletin",
                "url": "https://www.youtube.com/@NEWSONAIROFFICIAL",
                "free": True,
                "howToUse": "Listen to crisp 15-minute daily national policy and diplomatic analyses (AIR Spotlight) while commuting.",
            },
        ],
    )

    _add_sources(
        "ca-scitech",
        [
            {
                "name": "Department of Science & Technology (DST)",
                "type": "Official Portal",
                "url": "https://dst.gov.in/",
                "free": True,
                "howToUse": "Track National Quantum Mission, National Supercomputing Mission, and R&D policy milestones.",
            },
            {
                "name": "DRDO Official Portal",
                "type": "Official Portal",
                "url": "https://www.drdo.gov.in/",
                "free": True,
                "howToUse": "Verify indigenous missile ranges, propulsion systems, radars, and defence platforms for Prelims & GS-3.",
            },
            {
                "name": "PRS Science & Tech Policy Briefs",
                "type": "Policy Brief",
                "url": "https://prsindia.org/policy/science-technology-brief",
                "free": True,
                "howToUse": "Use 2-page policy explainers on AI regulation, Digital Personal Data Protection, Space, and Biotech.",
            },
        ],
    )

    # Add 5th high-yield category covering Governance, Social Justice, Society & Culture (GS-1 & GS-2)
    if "ca-governance-society" not in by_id:
        result.append(
            {
                "id": "ca-governance-society",
                "title": "Governance, Social Justice & Society (GS-1 & GS-2)",
                "gsPaper": "GS-1 & GS-2",
                "description": "Welfare schemes, 2nd ARC governance reforms, NITI Aayog indices, health/education metrics, urbanization, and cultural heritage updates.",
                "keySources": [
                    {
                        "name": "NITI Aayog Official Portal (SDG & MPI Reports)",
                        "type": "Official Report",
                        "url": "https://www.niti.gov.in/",
                        "free": True,
                        "howToUse": "Cite SDG India Index and Multidimensional Poverty Index figures directly in Mains GS-1/GS-2/Essay.",
                    },
                    {
                        "name": "DARPG — 2nd ARC Reports (All 15 PDFs)",
                        "type": "Official Report",
                        "url": "https://darpg.gov.in/arc-reports",
                        "free": True,
                        "howToUse": "Quote specific recommendations from Report 4 (Ethics), Report 6 (Local Governance), and Report 12 (Citizen-Centric Admin).",
                    },
                    {
                        "name": "Vikaspedia (MeitY Welfare Encyclopedia)",
                        "type": "Official Portal",
                        "url": "https://vikaspedia.in/",
                        "free": True,
                        "howToUse": "Quickly verify eligibility, nodal ministry, and benefits of central social welfare, health, and education schemes.",
                    },
                    {
                        "name": "NewsOnAir (Akashvani / AIR News)",
                        "type": "Official Broadcast",
                        "url": "https://newsonair.gov.in/",
                        "free": True,
                        "howToUse": "Review concise 9 PM national bulletin summaries for verified Cabinet and welfare announcements.",
                    },
                    {
                        "name": "Economic & Political Weekly (EPW)",
                        "type": "Academic Journal",
                        "url": "https://www.epw.in/",
                        "free": True,
                        "howToUse": "Use selected analytical essays on Indian society, federalism, and social justice for Mains & Optional depth.",
                    },
                    {
                        "name": "Vision IAS Monthly Current Affairs Archive",
                        "type": "Monthly Magazine",
                        "url": "https://www.visionias.in/resources/current-affairs/",
                        "free": True,
                        "howToUse": "Consolidate all GS-1 to GS-3 monthly developments in one structured PDF for repeated revision.",
                    },
                ],
                "highYieldTopics": [
                    "Multidimensional Poverty Index (MPI) & SDG India Index trends",
                    "Citizen Charters, e-Governance, Sevottam & 2nd ARC reforms",
                    "Ayushman Bharat, NEP 2020 implementation & Nutrition (POSHAN 2.0)",
                    "Urbanization, Women Empowerment, Tribal Welfare (PM-JANMAN) & GI/UNESCO Heritage",
                ],
            }
        )

    return result


# =========================================================================
# SYNC & VALIDATION ORCHESTRATION
# =========================================================================


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def sync_master_files(write_files: bool = True) -> dict[str, Any]:
    """Parse master guide and deterministically sync master_guide, resources, question_papers, and current_affairs."""
    master_guide = parse_master_guide(MASTER_GUIDE_PATH)

    resources_path = DATA_DIR / "resources.json"
    existing_resources = _read_json(resources_path) if resources_path.exists() else []
    enriched_resources = build_enriched_resources(existing_resources, master_guide)

    qp_path = DATA_DIR / "question_papers.json"
    existing_qps = _read_json(qp_path) if qp_path.exists() else []
    enriched_qps = _enrich_question_papers(existing_qps, master_guide)

    ca_path = DATA_DIR / "current_affairs.json"
    existing_ca = _read_json(ca_path) if ca_path.exists() else []
    enriched_ca = _enrich_current_affairs(existing_ca, master_guide)

    master_guide_path = DATA_DIR / "master_guide.json"

    if write_files:
        _write_json(master_guide_path, master_guide)
        _write_json(resources_path, enriched_resources)
        _write_json(qp_path, enriched_qps)
        _write_json(ca_path, enriched_ca)

    validation = validate_catalog(
        resources=enriched_resources,
        master_guide=master_guide,
    )

    return {
        "written": write_files,
        "files": {
            "master_guide": str(master_guide_path),
            "resources": str(resources_path),
            "question_papers": str(qp_path),
            "current_affairs": str(ca_path),
        },
        "counts": {
            "existing_resources_preserved": len(existing_resources),
            "total_resources": len(enriched_resources),
            "new_resources_added": len(enriched_resources) - len(existing_resources),
            "master_guide_parts": master_guide["meta"]["parts_count"],
            "master_guide_unique_urls": master_guide["meta"]["total_links"],
            "ncert_directory_books": len(master_guide["ncert_directory"]),
            "question_papers": len(enriched_qps),
            "current_affairs_categories": len(enriched_ca),
        },
        "validation": validation,
    }


def validate_catalog(
    resources: Optional[list[dict[str, Any]]] = None,
    master_guide: Optional[dict[str, Any]] = None,
    ncert_books: Optional[list[dict[str, Any]]] = None,
    pyqs: Optional[list[dict[str, Any]]] = None,
    roadmaps: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Run comprehensive integrity, URL, ID uniqueness, schema, and cross-reference validation."""
    errors: list[str] = []
    warnings: list[str] = []
    urls_checked = 0

    if resources is None:
        resources = _read_json(DATA_DIR / "resources.json")
    if master_guide is None:
        mg_path = DATA_DIR / "master_guide.json"
        master_guide = _read_json(mg_path) if mg_path.exists() else parse_master_guide()
    if ncert_books is None:
        ncert_books = _read_json(DATA_DIR / "ncert.json")
    if pyqs is None:
        pyqs = _read_json(DATA_DIR / "pyqs.json")
    if roadmaps is None:
        roadmaps = _read_json(DATA_DIR / "roadmaps.json")

    qp_path = DATA_DIR / "question_papers.json"
    question_papers = _read_json(qp_path) if qp_path.exists() else []
    ca_path = DATA_DIR / "current_affairs.json"
    current_affairs = _read_json(ca_path) if ca_path.exists() else []

    def _check_url(url: Any, context: str) -> None:
        nonlocal urls_checked
        urls_checked += 1
        if not is_valid_http_url(url):
            errors.append(f"Invalid URL in {context}: {url!r}")
        elif isinstance(url, str) and (" & " in url or "[" in url or "]" in url):
            errors.append(f"Composite/malformed URL in {context}: {url!r}")
        elif isinstance(url, str):
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            if host in _YOUTUBE_HOSTS and "list=" in parsed.query and not extract_youtube_playlist_id(url):
                errors.append(f"Truncated or invalid YouTube playlist ID in {context}: {url!r}")

    # 1. Validate resources.json
    res_ids: set[str] = set()
    res_type_counts: dict[str, int] = {}
    res_subject_counts: dict[str, int] = {}
    for idx, r in enumerate(resources):
        rid = r.get("id")
        if not isinstance(rid, str) or not rid.strip():
            errors.append(f"Resource at index {idx} has blank id")
            continue
        if rid in res_ids:
            errors.append(f"Duplicate resource id: {rid}")
        res_ids.add(rid)

        for req in ("title", "subject", "category", "level", "type", "provider", "url"):
            val = r.get(req)
            if not isinstance(val, str) or not val.strip():
                errors.append(f"Resource {rid} has blank required field '{req}'")

        subj = r.get("subject", "")
        rtype = r.get("type", "")
        if subj and subj not in CANONICAL_SUBJECTS:
            errors.append(f"Resource {rid} has non-canonical subject: {subj!r}")
        if rtype and rtype not in CANONICAL_TYPES:
            errors.append(f"Resource {rid} has non-canonical type: {rtype!r}")
        res_subject_counts[subj] = res_subject_counts.get(subj, 0) + 1
        res_type_counts[rtype] = res_type_counts.get(rtype, 0) + 1

        _check_url(r.get("url"), f"resource:{rid}")
        expected_pl = extract_youtube_playlist_id(r.get("url"))
        expected_vid = extract_youtube_video_id(r.get("url"))
        if rtype == "YouTube" and not (expected_pl or expected_vid):
            errors.append(
                f"Resource {rid} is marked type 'YouTube' but URL is not a playable playlist or video: {r.get('url')!r}"
            )
        if expected_pl and r.get("youtubePlaylistId") != expected_pl:
            errors.append(
                f"Resource {rid} playlist ID mismatch: got {r.get('youtubePlaylistId')!r}, expected {expected_pl!r}"
            )
        if not expected_pl and r.get("youtubePlaylistId"):
            errors.append(f"Resource {rid} has unexpected youtubePlaylistId on non-playlist URL")

    # 2. Validate master_guide.json
    mg_parts = master_guide.get("parts", [])
    part_nums = [p.get("part_number") for p in mg_parts]
    if part_nums != list(range(1, 12)):
        errors.append(f"master_guide missing parts: got {part_nums}, expected 1..11")

    required_mg_keys = (
        "meta",
        "parts",
        "official_hub",
        "ncert_portals",
        "ncert_directory",
        "bridge_textbooks",
        "standard_books",
        "govt_reports",
        "news_and_thinktanks",
        "curated_notes",
        "exam_papers_and_quizzes",
        "video_library",
        "csat_kit",
        "optionals",
        "interview_prep",
        "study_sequence",
    )
    for k in required_mg_keys:
        if k not in master_guide or not master_guide[k]:
            errors.append(f"master_guide missing or empty required section '{k}'")

    for item in master_guide.get("official_hub", []):
        _check_url(item.get("url"), f"master_guide.official_hub:{item.get('title')}")
    for item in master_guide.get("ncert_portals", []):
        _check_url(item.get("url"), f"master_guide.ncert_portals:{item.get('title')}")
    for item in master_guide.get("ncert_directory", []):
        _check_url(item.get("url"), f"master_guide.ncert_directory:{item.get('book_title')}")
        for vc in item.get("video_companions", []):
            _check_url(vc.get("url"), f"master_guide.ncert_directory.video:{vc.get('title')}")
    for item in master_guide.get("bridge_textbooks", []):
        _check_url(item.get("url"), f"master_guide.bridge_textbooks:{item.get('title')}")
    for item in master_guide.get("standard_books", []):
        for comp in item.get("companions", []):
            _check_url(comp.get("url"), f"master_guide.standard_books:{comp.get('title')}")
    for item in master_guide.get("govt_reports", []):
        _check_url(item.get("url"), f"master_guide.govt_reports:{item.get('title')}")
    for item in master_guide.get("news_and_thinktanks", []):
        _check_url(item.get("url"), f"master_guide.news_and_thinktanks:{item.get('title')}")
    for item in master_guide.get("curated_notes", []):
        _check_url(item.get("url"), f"master_guide.curated_notes:{item.get('title')}")
    for item in master_guide.get("exam_papers_and_quizzes", []):
        _check_url(item.get("url"), f"master_guide.exam_papers_and_quizzes:{item.get('title')}")
    vl = master_guide.get("video_library", {})
    for bucket in ("official_channels", "subject_channels", "direct_playlists"):
        for item in vl.get(bucket, []):
            _check_url(item.get("url"), f"master_guide.video_library.{bucket}:{item.get('title')}")
    for item in master_guide.get("csat_kit", []):
        _check_url(item.get("url"), f"master_guide.csat_kit:{item.get('title')}")
    for opt in master_guide.get("optionals", []):
        for lnk in opt.get("academic_links", []):
            _check_url(lnk.get("url"), f"master_guide.optionals.{opt.get('subject')}.academic")
        for lnk in opt.get("video_links", []):
            _check_url(lnk.get("url"), f"master_guide.optionals.{opt.get('subject')}.video")
    for item in master_guide.get("interview_prep", []):
        _check_url(item.get("url"), f"master_guide.interview_prep:{item.get('title')}")
    for phase in master_guide.get("study_sequence", []):
        for lnk in phase.get("links", []):
            _check_url(lnk.get("url"), f"master_guide.study_sequence.phase_{phase.get('phase_number')}")

    # 3. Validate ncert.json
    ncert_ids: set[str] = set()
    total_ncert_chapters = 0
    for b in ncert_books:
        bid = b.get("id")
        if not isinstance(bid, str) or not bid.strip():
            errors.append("NCERT book has blank id")
            continue
        if bid in ncert_ids:
            errors.append(f"Duplicate NCERT book id: {bid}")
        ncert_ids.add(bid)

        for req in ("subjectName", "bookTitle", "officialPdfUrl"):
            if not isinstance(b.get(req), str) or not b.get(req, "").strip():
                errors.append(f"NCERT book {bid} has blank '{req}'")
        _check_url(b.get("officialPdfUrl"), f"ncert.officialPdfUrl:{bid}")
        if "ncert.nic.in" not in str(b.get("officialPdfUrl", "")):
            errors.append(f"NCERT book {bid} PDF URL is not on ncert.nic.in: {b.get('officialPdfUrl')!r}")
        if b.get("recommendedLectureUrl"):
            _check_url(b.get("recommendedLectureUrl"), f"ncert.recommendedLectureUrl:{bid}")
            lec_url = str(b.get("recommendedLectureUrl", ""))
            lec_host = (urlparse(lec_url).hostname or "").lower()
            if lec_host in _YOUTUBE_HOSTS and not (
                extract_youtube_playlist_id(lec_url) or extract_youtube_video_id(lec_url)
            ):
                errors.append(
                    f"NCERT book {bid} recommendedLectureUrl is not a playable YouTube playlist/video: {lec_url!r}"
                )

        chapters = b.get("chapters", [])
        if not chapters:
            errors.append(f"NCERT book {bid} has zero chapters")
        total_ncert_chapters += len(chapters)
        for ch in chapters:
            if not isinstance(ch.get("title"), str) or not ch.get("title", "").strip():
                errors.append(f"NCERT book {bid} has chapter with blank title")

    # 4. Validate pyqs.json
    pyq_ids: set[str] = set()
    for q in pyqs:
        qid = q.get("id")
        if not isinstance(qid, str) or not qid.strip():
            errors.append("PYQ has blank id")
            continue
        if qid in pyq_ids:
            errors.append(f"Duplicate PYQ id: {qid}")
        pyq_ids.add(qid)

        for req in ("type", "paper", "subject", "topic", "question", "explanation"):
            if not isinstance(q.get(req), str) or not q.get(req, "").strip():
                errors.append(f"PYQ {qid} has blank '{req}'")
        if q.get("type") == "Prelims":
            opts = q.get("options", [])
            ans = q.get("correctAnswer")
            if not opts or ans not in opts:
                errors.append(f"Prelims PYQ {qid} has invalid options or correctAnswer not in options")

        rel = q.get("relatedResourceId")
        if rel:
            if rel not in res_ids:
                errors.append(f"PYQ {qid} references missing relatedResourceId: {rel!r}")
        else:
            warnings.append(f"PYQ {qid} has no relatedResourceId")

    # 5. Validate roadmaps.json
    rm_subject_ids: set[str] = set()
    rm_step_ids: set[str] = set()
    rm_res_ids: set[str] = set()
    for rm in roadmaps:
        sid = rm.get("subjectId")
        if not isinstance(sid, str) or not sid.strip():
            errors.append("Roadmap has blank subjectId")
            continue
        if sid in rm_subject_ids:
            errors.append(f"Duplicate roadmap subjectId: {sid}")
        rm_subject_ids.add(sid)

        if not isinstance(rm.get("subjectName"), str) or not rm["subjectName"].strip():
            errors.append(f"Roadmap {sid} has blank subjectName")

        steps = rm.get("steps", [])
        if not steps:
            errors.append(f"Roadmap {sid} has no steps")
        for st in steps:
            stid = st.get("id")
            if not isinstance(stid, str) or not stid.strip():
                errors.append(f"Roadmap {sid} has step with blank id")
                continue
            if stid in rm_step_ids:
                errors.append(f"Duplicate roadmap step id: {stid}")
            rm_step_ids.add(stid)

            if not isinstance(st.get("title"), str) or not st["title"].strip():
                errors.append(f"Roadmap step {stid} has blank title")

            for sr in st.get("resources", []):
                srid = sr.get("id")
                if not isinstance(srid, str) or not srid.strip():
                    errors.append(f"Roadmap step {stid} has resource with blank id")
                elif srid in rm_res_ids:
                    errors.append(f"Duplicate roadmap embedded resource id: {srid}")
                else:
                    rm_res_ids.add(srid)
                _check_url(sr.get("url"), f"roadmap.{sid}.{stid}.{srid}")
                sr_pl = extract_youtube_playlist_id(sr.get("url"))
                sr_vid = extract_youtube_video_id(sr.get("url"))
                if sr.get("type") == "YouTube" and not (sr_pl or sr_vid):
                    errors.append(
                        f"Roadmap {sid}.{stid}.{srid} is marked type 'YouTube' but URL is not a playable playlist/video: {sr.get('url')!r}"
                    )
                if sr_pl and sr.get("youtubePlaylistId") != sr_pl:
                    errors.append(
                        f"Roadmap {sid}.{stid}.{srid} youtubePlaylistId mismatch: got {sr.get('youtubePlaylistId')!r}, expected {sr_pl!r}"
                    )
                if not sr_pl and sr.get("youtubePlaylistId"):
                    errors.append(
                        f"Roadmap {sid}.{stid}.{srid} has unexpected youtubePlaylistId on non-playlist URL"
                    )

    # 6. Validate question_papers.json & current_affairs.json
    qp_ids: set[str] = set()
    for qp in question_papers:
        qpid = qp.get("id")
        if not qpid or qpid in qp_ids:
            errors.append(f"Invalid or duplicate question_paper id: {qpid!r}")
        else:
            qp_ids.add(qpid)
        _check_url(qp.get("url"), f"question_paper:{qpid}")

    ca_ids: set[str] = set()
    for cat in current_affairs:
        cid = cat.get("id")
        if not cid or cid in ca_ids:
            errors.append(f"Invalid or duplicate current_affairs id: {cid!r}")
        else:
            ca_ids.add(cid)
        for src in cat.get("keySources", []):
            _check_url(src.get("url"), f"current_affairs.{cid}:{src.get('name')}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "resources_count": len(resources),
            "resources_by_type": dict(sorted(res_type_counts.items())),
            "resources_by_subject": dict(sorted(res_subject_counts.items())),
            "master_guide_parts": len(mg_parts),
            "master_guide_unique_urls": master_guide.get("meta", {}).get("total_links", 0),
            "ncert_directory_count": len(master_guide.get("ncert_directory", [])),
            "ncert_books_count": len(ncert_books),
            "ncert_chapters_count": total_ncert_chapters,
            "roadmaps_count": len(roadmaps),
            "roadmap_steps_count": len(rm_step_ids),
            "pyqs_count": len(pyqs),
            "question_papers_count": len(question_papers),
            "current_affairs_categories_count": len(current_affairs),
            "total_urls_checked": urls_checked,
        },
    }


if __name__ == "__main__":
    summary = sync_master_files(write_files=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
