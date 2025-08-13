from __future__ import annotations
import hashlib, time, json, re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup

try:
    import trafilatura  # optional: better article extraction
except Exception:  # pragma: no cover - optional dependency
    trafilatura = None

CACHE_DIR = Path('cache/web')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
UA = {'User-Agent': 'StudyCoach/1.0 (+no-bot; educational use)'}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _cache_read(key: str) -> Optional[dict]:
    f = CACHE_DIR / f"{key}.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding='utf-8'))
        except Exception:  # pragma: no cover - corrupted cache
            return None
    return None


def _cache_write(key: str, data: dict) -> None:
    f = CACHE_DIR / f"{key}.json"
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def ddg_search(query: str, max_results: int = 5, lang: str = 'fr-fr') -> List[Dict]:
    """Basic DuckDuckGo HTML search without API key."""
    key = _hash(f"ddg::{query}::{max_results}::{lang}")
    cached = _cache_read(key)
    if cached:
        return cached['results']

    url = 'https://duckduckgo.com/html/'
    r = requests.post(url, data={'q': query, 'kl': lang}, headers=UA, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    results: List[Dict] = []
    for res in soup.select('.result__body')[:max_results]:
        a = res.select_one('a.result__a')
        if not a or not a.get('href'):
            continue
        title = a.get_text(' ', strip=True)
        link = a['href']
        snippet = res.select_one('.result__snippet')
        desc = snippet.get_text(' ', strip=True) if snippet else ''
        results.append({'title': title, 'url': link, 'snippet': desc})
    _cache_write(key, {'results': results, 't': time.time()})
    return results


def fetch_clean_text(url: str) -> Tuple[str, str]:
    """Download a page and return (title, clean_text)."""
    key = _hash(f"page::{url}")
    cached = _cache_read(key)
    if cached:
        return cached.get('title', ''), cached.get('text', '')

    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    html = r.text

    if trafilatura:
        downloaded = trafilatura.fetch_url(url, no_ssl=True, user_agent=UA['User-Agent'])
        txt = trafilatura.extract(downloaded, include_links=False, include_comments=False) or ''
        if txt.strip():
            m = re.search(r'<title>(.*?)</title>', html, flags=re.IGNORECASE | re.DOTALL)
            title = (m.group(1).strip() if m else url)[:120]
            _cache_write(key, {'title': title, 'text': txt})
            return title, txt

    soup = BeautifulSoup(html, 'html.parser')
    t = soup.find('title')
    title = (t.get_text(' ', strip=True) if t else url)[:120]
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()
    text = re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))
    _cache_write(key, {'title': title, 'text': text})
    return title, text


def web_context_from_query(query: str, k_pages: int = 3, max_chars: int = 4000) -> List[Dict]:
    """Search and fetch k_pages results with cleaned excerpts."""
    hits = ddg_search(query, max_results=k_pages)
    out: List[Dict] = []
    for h in hits:
        try:
            title, txt = fetch_clean_text(h['url'])
            excerpt = txt[:max_chars]
            out.append({'title': title, 'url': h['url'], 'excerpt': excerpt})
        except Exception:
            continue
    return out
