#!/usr/bin/env python3
"""Scrape CRDP official-exam papers into data.js.

Uses curl.exe with a browser user-agent.  A real browser window triggers the
visible Cloudflare reCAPTCHA popup; plain curl with the same UA does not.
Progress is saved after every combination so a restart can resume.
"""
import json
import os
import re
import subprocess
import sys
import time

from bs4 import BeautifulSoup

from classify_fix import detect_subject

BASE = "https://www.crdp.org/official-exams-corrections-lebanon"
PROGRESS = "progress.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
HEADERS = [
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "-H", "Accept-Language: en-US,en;q=0.9",
]

# Values from #edit-term-node-tid-depth-shs-0-0 (first, visible select).
BRANCHES = {
    "brevet": "34",
    "se": "45",
    "sg": "59",
    "sv": "70",
    "sh": "82",
}

SPECIAL_RE = re.compile(r"احتياجات خاصة|مكفوفين|special needs|blind", re.I)
CORRECTION_RE = re.compile(r"أسس التصحيح|اسس التصحيح|الإجابة النموذجية|الاجابة النموذجية|"
                           r"corrig[ée]|answer key|marking", re.I)

# PDF filename prefix -> CRDP branch (some papers are shared by two branches).
PREFIX_LEVELS = {
    "BR": ["brevet"],
    "SE": ["se"],
    "SG": ["sg"],
    "SV": ["sv"],
    "LH": ["sh"],
    "SELH": ["se", "sh"],
    "SVSG": ["sv", "sg"],
}


def fetch(url):
    for attempt in range(6):
        p = subprocess.run(
            ["curl.exe", "-s", "-L", "--max-time", "45", "-A", UA] + HEADERS + [url],
            capture_output=True,
        )
        html = p.stdout.decode("utf-8", "replace")
        if p.returncode == 0 and "Just a moment" not in html and len(html) > 5000:
            return html
        time.sleep(0.8 + attempt * 0.8)
    raise RuntimeError(f"Fetch failed (Cloudflare?): {url}")


def parse_sessions(html):
    out = []
    for m in re.finditer(r'<option value="(\d+)"[^>]*>\s*(دورة[^<]+?)\s*</option>', html):
        out.append({"id": m.group(1), "label": m.group(2)})
    return out


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table.cols-2 tbody tr"):
        a = tr.select_one("td.views-field-title a")
        if not a:
            continue
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("/"):
            href = "https://www.crdp.org" + href
        rows.append({
            "title": " ".join(a.get_text(" ", strip=True).split()),
            "url": href,
        })
    pages = [int(x) for x in re.findall(r"page=(\d+)", html)]
    return rows, (max(pages) if pages else 0)


def scrape_all():
    done = {}
    if os.path.exists(PROGRESS):
        with open(PROGRESS, "r", encoding="utf-8") as f:
            for item in json.load(f):
                key = item["session"]["id"]
                done[("session|" if item["level"] == "__session__"
                      else item["level"] + "|") + key] = item

    root = fetch(BASE)
    sessions = parse_sessions(root)
    if not sessions:
        raise RuntimeError("Could not read the session <select> from the CRDP page")
    print(f"{len(sessions)} sessions found", flush=True)

    combos = [(level, tid, s) for level, tid in BRANCHES.items() for s in sessions]
    for i, (level, tid, s) in enumerate(combos, 1):
        key = level + "|" + s["id"]
        if key in done:
            print(f"[{i:3d}/{len(combos)}] {level:7s} {s['id']}: cached", flush=True)
            continue
        url = f"{BASE}?sessionurl={s['id']}&term_node_tid_depth={tid}"
        rows, last = parse_page(fetch(url))
        for pno in range(1, last + 1):
            more, _ = parse_page(fetch(url + f"&page={pno}"))
            rows.extend(more)
            time.sleep(0.15)
        done[key] = {"level": level, "session": s, "rows": rows}
        with open(PROGRESS, "w", encoding="utf-8") as f:
            json.dump(list(done.values()), f, ensure_ascii=False)
        print(f"[{i:3d}/{len(combos)}] {level:7s} {s['id']}: {len(rows)}",
              flush=True)
        time.sleep(0.2)

    # Newer sessions (2020+) are not tagged with the old branch taxonomy, so
    # scrape the session-only listing once and use the PDF filename prefix
    # (BR / SE / SG / SV / LH / SELH / SVSG) to assign the branch.
    for i, s in enumerate(sessions, 1):
        key = "session|" + s["id"]
        if key in done:
            print(f"[session {i:2d}/{len(sessions)}] {s['id']}: cached", flush=True)
            continue
        url = f"{BASE}?sessionurl={s['id']}"
        rows, last = parse_page(fetch(url))
        for pno in range(1, last + 1):
            more, _ = parse_page(fetch(url + f"&page={pno}"))
            rows.extend(more)
            time.sleep(0.15)
        done[key] = {"level": "__session__", "session": s, "rows": rows}
        with open(PROGRESS, "w", encoding="utf-8") as f:
            json.dump(list(done.values()), f, ensure_ascii=False)
        print(f"[session {i:2d}/{len(sessions)}] {s['id']}: {len(rows)}", flush=True)
        time.sleep(0.2)
    return {"sessions": sessions, "results": list(done.values())}


# --------------------------------------------------------------------------
# Classification / output
# --------------------------------------------------------------------------
def parse_session(label):
    year_m = re.search(r"(?:19|20)\d{2}", label)
    if not year_m:
        return None
    return {
        "year": int(year_m.group(0)),
        "type": "exceptional" if "استثنائية" in label else "normal",
        "label": label,
        "special": "الخاصة" in label,
    }


def levels_for_row(row, batch_level):
    if batch_level != "__session__":
        return [batch_level]
    prefix = row["url"].rsplit("/", 1)[-1].split("_")[0].upper()
    if prefix in PREFIX_LEVELS:
        return PREFIX_LEVELS[prefix]
    t = row["title"]
    if "الشهادة المتوسطة" in t:
        return ["brevet"]
    if "اجتماع واقتصاد" in t:
        return ["se"]
    if "آداب" in t or "انسانيات" in t:
        return ["sh"]
    if "علوم عامة" in t:
        return ["sg"]
    if "علوم الحياة" in t:
        return ["sv"]
    return []


def detect_language(title, subject):
    t = title.lower()
    if "لغة عربية" in t or "بالعربية" in t or "عربي" in t:
        return "ar"
    if ("لغة إنكليزية" in t or "لغة انكليزية" in t or "إنكليزي" in t
            or "انكليزي" in t or "english" in t or "anglais" in t):
        return "en"
    if ("لغة فرنسية" in t or "فرنسي" in t or "français" in t
            or "francais" in t):
        return "fr"
    if subject in ("arabic", "arabic_philosophy"):
        return "ar"
    if subject == "french":
        return "fr"
    if subject == "english":
        return "en"
    return "ar"


def main():
    scraped = scrape_all()
    sessions = []
    ids = {}
    for opt in scraped["sessions"]:
        info = parse_session(opt["label"])
        if not info:
            continue
        info["id"] = opt["id"]
        ids[opt["id"]] = info
        sessions.append(info)

    data = {level: {} for level in BRANCHES}
    for batch in scraped["results"]:
        s = ids.get(batch["session"]["id"])
        if not s:
            continue
        for row in batch["rows"]:
            subj = detect_subject(row["title"], row["url"])
            lang = detect_language(row["title"], subj)
            key = f"{s['year']}|{s['type']}"
            record = {
                "url": row["url"],
                "lang": lang,
                "special": bool(SPECIAL_RE.search(row["title"])),
                "correction": bool(CORRECTION_RE.search(row["title"])),
                "title": row["title"],
            }
            for level in levels_for_row(row, batch["level"]):
                bucket = (data[level].setdefault(subj, {})
                          .setdefault(key, {"normal": [], "exceptional": []}))
                bucket[s["type"]].append(record)

    for level_data in data.values():
        for years in level_data.values():
            for sess in years.values():
                for kind in ("normal", "exceptional"):
                    seen, uniq = set(), []
                    for row in sess[kind]:
                        if row["url"] in seen:
                            continue
                        seen.add(row["url"])
                        uniq.append(row)
                    sess[kind] = uniq

    payload = {"source": BASE, "sessions": sessions, "levels": data}
    with open("data.js", "w", encoding="utf-8") as f:
        f.write("// Generated by scrape.py from https://www.crdp.org — do not edit by hand\n")
        f.write("window.CRDP_DATA = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    total = 0
    for level, subjects in data.items():
        counts = {
            subj: sum(len(v["normal"]) + len(v["exceptional"])
                      for v in sessions.values())
            for subj, sessions in subjects.items()
        }
        total += sum(counts.values())
        print(f"{level:7s}: {sum(counts.values()):4d}  {counts}", flush=True)
    print(f"Wrote data.js with {total} documents", flush=True)


if __name__ == "__main__":
    sys.exit(main())
