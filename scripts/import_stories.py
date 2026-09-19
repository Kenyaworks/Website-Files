#!/usr/bin/env python3
"""
Import all blog posts from kenyaworks.org/blog into Hugo content/stories/.

Wix-specific extraction:
  - Title  : og:title meta → h1.H3vOVf → first h1/h2
  - Image  : og:image meta (skip if it resolves to the site logo)
  - Body   : div.HW6ttf (Wix post wrapper), header.PhCafd removed (title/date block)
             All Wix static images stripped from body (decorative/layout only)
  - Date   : sitemap <lastmod>
  - Tags   : auto-tagged by keyword match
"""

import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# ── paths ──────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
STORIES_DIR = REPO_ROOT / "content" / "stories"
IMAGES_DIR  = REPO_ROOT / "assets" / "images" / "stories"
SITEMAP_URL = "https://www.kenyaworks.org/blog-posts-sitemap.xml"
DELAY       = 0.6

# ── auto-tag keyword mapping ───────────────────────────────────────────────
TAG_KEYWORDS = {
    "mhh-works":       ["pad", "menstrual", "period", "makini", "hygiene", "mhh",
                        "menstruation", "reproductive"],
    "education-works": ["school", "education", "student", "teacher", "class",
                        "scholarship", "golden achievers", "golden eagle", "study",
                        "academic", "secondary", "primary", "university", "learning"],
    "shelter-works":   ["shelter", "home", "housing", "child protection", "miale",
                        "family reunification", "orphan", "vulnerable", "rescue",
                        "safe house", "street child"],
    "community-works": ["community", "advocate", "rights", "fgm",
                        "female genital", "circumcision", "human rights", "narok",
                        "gender", "violence", "gbv", "empowerment", "forum"],
}

# URL fragments that indicate the Wix site logo (not a post image)
LOGO_PATTERNS = ["no%20tagline", "no_tagline", "horizontal", "logo", "favicon"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36"
}


def fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def parse_sitemap() -> list[tuple[str, str]]:
    print(f"Fetching sitemap: {SITEMAP_URL}")
    xml_text = fetch(SITEMAP_URL)
    if not xml_text:
        raise SystemExit("Could not fetch sitemap.")
    root = ET.fromstring(xml_text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = []
    for url_el in root.findall("sm:url", ns):
        loc  = url_el.findtext("sm:loc",     namespaces=ns, default="").strip()
        date = url_el.findtext("sm:lastmod", namespaces=ns, default="2020-01-01").strip()[:10]
        if loc:
            entries.append((loc, date))
    print(f"Found {len(entries)} posts.")
    return entries


def slug_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


def extract_title(soup: BeautifulSoup) -> str:
    # 1. og:title meta (most reliable)
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        t = og["content"].strip()
        # Strip generic site suffix
        t = re.sub(r"\s*\|\s*Kenya Works$", "", t, flags=re.IGNORECASE).strip()
        if t and t.lower() not in ("post", "blog", ""):
            return t

    # 2. Wix post title h1
    for cls in ("H3vOVf",):
        el = soup.find("h1", class_=cls)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)

    # 3. Generic fallback
    for tag in ("h1", "h2"):
        el = soup.find(tag)
        if el:
            t = el.get_text(strip=True)
            if t and "kenya works" not in t.lower() and "good news" not in t.lower():
                return t
    return "Untitled"


def is_logo_url(url: str) -> bool:
    lower = url.lower()
    return any(p in lower for p in LOGO_PATTERNS)


def extract_featured_image(soup: BeautifulSoup) -> str | None:
    # og:image is the most reliable source for Wix
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        url = og["content"].split("?")[0]
        if not is_logo_url(url):
            return url
    return None


def extract_body_markdown(soup: BeautifulSoup) -> str:
    # Wix wraps post content in div.HW6ttf inside article.tgMH9T
    hw = soup.find("div", class_="HW6ttf")
    if not hw:
        # Fallback: try generic article
        hw = soup.find("article")
    if not hw:
        return ""

    # Remove the header block (contains title, date, reading-time)
    for header in hw.find_all("header", class_="PhCafd"):
        header.decompose()

    # Remove all Wix static images — they are decorative/layout, not editorial content.
    # The og:image is used as the hero image instead.
    for img in hw.find_all("img", src=True):
        if "wixstatic.com" in img.get("src", ""):
            img.decompose()

    # Remove scripts, styles, nav noise
    for el in hw.find_all(["script", "style", "noscript", "nav"]):
        el.decompose()

    text = md(str(hw), heading_style="ATX", bullets="-", strip=["a"])
    # Remove any leftover Wix image markdown (just in case)
    text = re.sub(r"!\[.*?\]\(https?://static\.wixstatic\.com[^\)]*\)", "", text)
    # Collapse 3+ blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def auto_tags(text: str) -> list[str]:
    lower = text.lower()
    return [tag for tag, kws in TAG_KEYWORDS.items() if any(kw in lower for kw in kws)]


def make_summary(text: str, max_len: int = 200) -> str:
    for line in text.splitlines():
        line = line.strip()
        # Skip headings, empty lines, markdown images
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        # Strip markdown bold/italic markers for cleaner summary
        line = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", line)
        if len(line) > max_len:
            return line[:max_len].rsplit(" ", 1)[0] + "…"
        return line
    return ""


def image_ext_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def download_image(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  WARN image download failed: {e}")
        return False


def yaml_escape(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_story(slug: str, date: str, title: str, tags: list[str],
                summary: str, image_path: str | None, body: str) -> None:
    tags_yaml = "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    lines = [
        "---",
        f"title: {yaml_escape(title)}",
        f"date: {date}",
        f"tags: {tags_yaml}",
        f"summary: {yaml_escape(summary)}",
    ]
    if image_path:
        lines.append(f'image: "{image_path}"')
    lines += ["---", "", body, ""]
    (STORIES_DIR / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    STORIES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    entries = parse_sitemap()
    total = len(entries)
    ok = skipped = errors = 0

    for i, (url, date) in enumerate(entries, 1):
        slug = slug_from_url(url)
        dest_md = STORIES_DIR / f"{slug}.md"

        print(f"[{i:3}/{total}] {slug}")

        if dest_md.exists():
            print("  already exists, skipping")
            skipped += 1
            time.sleep(0.1)
            continue

        html = fetch(url)
        if not html:
            errors += 1
            time.sleep(DELAY)
            continue

        soup     = BeautifulSoup(html, "html.parser")
        title    = extract_title(soup)
        img_url  = extract_featured_image(soup)
        body     = extract_body_markdown(soup)
        summary  = make_summary(body)
        tags     = auto_tags(title + " " + body)

        image_path = None
        if img_url:
            ext      = image_ext_from_url(img_url)
            dest_img = IMAGES_DIR / f"{slug}{ext}"
            if download_image(img_url, dest_img):
                image_path = f"images/stories/{slug}{ext}"
                print(f"  img  ✓  {dest_img.name}")

        write_story(slug, date, title, tags, summary, image_path, body)
        print(f"  md   ✓  tags={tags or '[]'}")
        ok += 1
        time.sleep(DELAY)

    print(f"\nDone. {ok} imported, {skipped} skipped, {errors} errors.")


if __name__ == "__main__":
    main()
