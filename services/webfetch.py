from __future__ import annotations
import hashlib, time, json, re, random
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup

try:
    import trafilatura  # optional
except Exception:
    trafilatura = None

CACHE_DIR = Path('cache/web')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
UA = {'User-Agent': 'StudyCoach/1.1 (+education; not a bot scraper)'}
TIMEOUT = (8, 20)  # connect, read

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _cache_read(key: str) -> Optional[dict]:
    f = CACHE_DIR / f"{key}.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            return None
    return None

def _cache_write(key: str, data: dict) -> None:
    f = CACHE_DIR / f"{key}.json"
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def _with_retries(fn, retries=2, backoff=0.6):
    last = None
    for i in range(retries + 1):
        try:
            return fn()
        except Exception as e:
            last = e
            time.sleep(backoff * (i + 1))
    if last:
        raise last

def ddg_search(query: str, max_results: int = 5, lang: str = 'fr-fr') -> List[Dict]:
    """DuckDuckGo HTML search (sans clé), robuste aux timeouts."""
    key = _hash(f"ddg::{query}::{max_results}::{lang}")
    cached = _cache_read(key)
    if cached:
        return cached.get('results', [])

    def _do():
        # Essaye GET puis POST si besoin
        url = 'https://duckduckgo.com/html/'
        r = requests.get(url, params={'q': query, 'kl': lang}, headers=UA, timeout=TIMEOUT)
        if r.status_code >= 400 or len(r.text) < 5000:
            r = requests.post(url, data={'q': query, 'kl': lang}, headers=UA, timeout=TIMEOUT)
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
        return results

    try:
        results = _with_retries(_do, retries=2)
    except Exception:
        results = []
    _cache_write(key, {'results': results, 't': time.time()})
    return results

def fetch_clean_text(url: str) -> Tuple[str, str]:
    """Télécharge une page et renvoie (titre, texte) avec fallback et réessais."""
    key = _hash(f"page::{url}")
    cached = _cache_read(key)
    if cached:
        return cached.get('title', ''), cached.get('text', '')

    def _do():
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        html = r.text
        if trafilatura:
            downloaded = trafilatura.fetch_url(url, no_ssl=True, user_agent=UA['User-Agent'])
            if downloaded:
                txt = trafilatura.extract(downloaded, include_links=False, include_comments=False) or ''
            else:
                txt = ''
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

    try:
        return _with_retries(_do, retries=2)
    except Exception:
        return url, ""

def web_context_from_query(query: str, k_pages: int = 3, max_chars: int = 4000) -> List[Dict]:
    hits = ddg_search(query, max_results=k_pages)
    out: List[Dict] = []
    for h in hits:
        title, txt = fetch_clean_text(h['url'])
        if not txt:
            continue
        excerpt = txt[:max_chars]
        out.append({'title': title, 'url': h['url'], 'excerpt': excerpt})
    return out
