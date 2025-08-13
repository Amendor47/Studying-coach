# services/local_ai.py
# -*- coding: utf-8 -*-
"""
LocalAI — LLM interne / offline + RAG léger pour Study Coach.

Fonctionne 100% hors-connexion :
- Embeddings: Ollama (si dispo) -> sinon sentence-transformers -> sinon bag-of-words TF-IDF light
- Index sémantique: FAISS (si dispo) -> sinon cosine maison via NumPy
- RAG: recherche des passages pertinents
- Analyse "sans IA": détection titres/sous-titres, concepts, résumés extractifs
- Génération de fiches: QA, QCM (4 options), Vrai/Faux, Cloze

Si Ollama est disponible (http://localhost:11434), propose aussi:
- chat(messages)
- complete(prompt)
- embed(texts) (embedding serveur)
"""

from __future__ import annotations

import os
import re
import json
import time
import math
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# ------- Dépendances optionnelles (gracieuses) -------
try:
    import requests  # pour Ollama
except Exception:
    requests = None  # type: ignore

try:
    import numpy as np
except Exception:
    np = None  # type: ignore

try:
    import faiss  # index vectoriel rapide
except Exception:
    faiss = None  # type: ignore

# Sentence-Transformers (optionnel)
_ST = None
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _ST = SentenceTransformer
except Exception:
    pass


# ----------------- Configuration -----------------
@dataclass
class LocalAISettings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("SC_LOCAL_MODEL", "llama3.2")  # ou mistral, phi, etc.
    ollama_embed_model: str = os.getenv("SC_EMBED_MODEL", "nomic-embed-text")
    max_passages: int = int(os.getenv("SC_RAG_TOP_K", "5"))
    use_ollama: bool = os.getenv("SC_USE_OLLAMA", "1") != "0"
    use_st: bool = os.getenv("SC_USE_SENTENCE_TRANSFORMERS", "1") != "0"
    st_model_name: str = os.getenv("SC_ST_MODEL", "all-MiniLM-L6-v2")


# ----------------- Utilitaires -----------------
_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "dans", "est", "sont",
    "pour", "avec", "sur", "par", "que", "qui", "plus", "moins", "au", "aux",
    "et", "ou", "où", "d'", "l'", "en", "à", "mon", "ma", "mes", "vos", "votre",
    "nos", "notre", "leur", "leurs", "ce", "cette", "ces", "il", "elle", "on"
}

def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip().lower()


def _sentences(text: str) -> List[str]:
    # coupure simple par ponctuation
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"\b\w{3,}\b", _normalize(text)) if t not in _STOPWORDS]


def _keyword_scores(text: str) -> Dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    from collections import Counter
    c = Counter(tokens)
    total = sum(c.values())
    return {w: c[w] / total for w in c}


def _top_keywords(text: str, k: int = 8) -> List[str]:
    scores = _keyword_scores(text)
    return [w for w, _ in sorted(scores.items(), key=lambda x: -x[1])[:k]]


def _title_like(line: str) -> bool:
    # heuristique: lignes courtes, capitalisées, numérotées ou markdown heading
    if re.match(r"^\s*(#+|\d+\.)\s+", line):
        return True
    if len(line) <= 80 and (line.isupper() or line[:1].isupper()):
        # évite les phrases longues
        return len(line.split()) <= 10
    return False


# ----------------- Embeddings -----------------
class LocalEmbedder:
    """Embeddings via Ollama -> ST -> TF-IDF léger."""

    def __init__(self, settings: LocalAISettings):
        self.s = settings
        self._st_model = None
        if _ST and self.s.use_st:
            try:
                self._st_model = _ST(self.s.st_model_name)
            except Exception:
                self._st_model = None

    def _ollama_embed_one(self, text: str) -> Optional[List[float]]:
        if not (self.s.use_ollama and requests):
            return None
        try:
            r = requests.post(
                f"{self.s.ollama_host}/api/embeddings",
                json={"model": self.s.ollama_embed_model, "prompt": text},
                timeout=30,
            )
            if r.status_code == 200:
                data = r.json()
                vec = data.get("embedding")
                if isinstance(vec, list):
                    return vec
        except Exception:
            return None
        return None

    def _st_embed_many(self, texts: List[str]) -> Optional[List[List[float]]]:
        if self._st_model is None:
            return None
        try:
            arr = self._st_model.encode(texts)
            return [v.tolist() for v in arr]
        except Exception:
            return None

    def _bow_embed_many(self, texts: List[str]) -> List[List[float]]:
        # TF-IDF light: vocab global sur le batch + log(1+tf) * idf
        vocab: Dict[str, int] = {}
        docs = []
        for t in texts:
            toks = _tokenize(t)
            docs.append(toks)
            for tok in toks:
                if tok not in vocab:
                    vocab[tok] = len(vocab)
        if not vocab:
            return [[0.0] for _ in texts]
        df = [0] * len(vocab)
        for toks in docs:
            for tok in set(toks):
                df[vocab[tok]] += 1
        n = len(texts)
        idf = [math.log((n + 1) / (dfi + 1)) + 1 for dfi in df]
        vecs = []
        for toks in docs:
            tf = [0] * len(vocab)
            for tok in toks:
                tf[vocab[tok]] += 1
            vec = [math.log(1 + tf[i]) * idf[i] for i in range(len(vocab))]
            vecs.append(vec)
        return vecs

    def embed(self, texts: List[str]) -> List[List[float]]:
        texts = [t if isinstance(t, str) else str(t) for t in texts]

        # 1) Ollama (un par un car API)
        if self.s.use_ollama and requests:
            out: List[Optional[List[float]]] = []
            ok = True
            for t in texts:
                v = self._ollama_embed_one(t)
                if v is None:
                    ok = False
                    break
                out.append(v)
            if ok and all(v is not None for v in out):
                return [v for v in out if v is not None]  # type: ignore

        # 2) SentenceTransformers (batch)
        st_vecs = self._st_embed_many(texts)
        if st_vecs is not None:
            return st_vecs

        # 3) Fallback bag-of-words
        return self._bow_embed_many(texts)


# ----------------- Index sémantique -----------------
class LocalIndex:
    """Index vectoriel avec FAISS si dispo, sinon cosine maison."""

    def __init__(self, dim: Optional[int] = None):
        self._use_faiss = faiss is not None
        self._dim = dim
        self._vecs: List[List[float]] = []
        self._texts: List[str] = []
        self._meta: List[Dict[str, Any]] = []
        self._faiss_index = None
        if self._use_faiss and dim:
            self._faiss_index = faiss.IndexFlatIP(dim)

    def add(self, vectors: List[List[float]], texts: List[str], metas: Optional[List[Dict[str, Any]]] = None):
        if self._dim is None and vectors:
            self._dim = len(vectors[0])
            if self._use_faiss:
                self._faiss_index = faiss.IndexFlatIP(self._dim)
        self._vecs.extend(vectors)
        self._texts.extend(texts)
        if metas:
            self._meta.extend(metas)
        else:
            self._meta.extend([{} for _ in texts])

        if self._use_faiss and self._faiss_index:
            import numpy as _np
            mat = _np.array(vectors, dtype="float32")
            # normalise pour produit scalaire ~ cosine
            norms = _np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
            mat = mat / norms
            self._faiss_index.add(mat)

    def search(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._vecs:
            return []
        if self._use_faiss and self._faiss_index is not None:
            import numpy as _np
            q = _np.array([query_vec], dtype="float32")
            q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-9)  # type: ignore
            D, I = self._faiss_index.search(q, min(top_k, len(self._vecs)))
            out = []
            for score, idx in zip(D[0], I[0]):
                out.append({"text": self._texts[idx], "meta": self._meta[idx], "score": float(score)})
            return out

        # Cosine maison
        if np is None:
            # Fallback sans numpy: produit scalaire normalisé
            def dot(a, b):
                return sum(x * y for x, y in zip(a, b))
            def norm(a):
                return math.sqrt(sum(x * x for x in a)) + 1e-9
            qn = norm(query_vec)
            scored = []
            for i, v in enumerate(self._vecs):
                s = dot(query_vec, v) / (qn * norm(v))
                scored.append((s, i))
            scored.sort(key=lambda x: -x[0])
            out = []
            for s, i in scored[:top_k]:
                out.append({"text": self._texts[i], "meta": self._meta[i], "score": float(s)})
            return out

        # Avec numpy
        mat = np.array(self._vecs, dtype=float)
        q = np.array(query_vec, dtype=float)
        mat = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
        q = q / (np.linalg.norm(q) + 1e-9)
        sims = (mat @ q)
        idxs = sims.argsort()[::-1][:top_k]
        return [{"text": self._texts[i], "meta": self._meta[i], "score": float(sims[i])} for i in idxs]


# ----------------- Ollama client (optionnel) -----------------
class OllamaClient:
    def __init__(self, settings: LocalAISettings):
        self.s = settings
        self.ok = bool(requests)

    def _post(self, path: str, payload: Dict[str, Any], timeout: int = 60) -> Optional[Dict[str, Any]]:
        if not requests:
            return None
        try:
            r = requests.post(f"{self.s.ollama_host}{path}", json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        data = self._post("/api/chat", {"model": self.s.ollama_model, "messages": messages, "options": {"temperature": temperature}})
        if not data:
            return None
        # flux = True → chunks; ici on s'attend à non-stream (si stream off côté ollama)
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        # si stream, concaténer
        if "done" in data and data["done"] is True and "response" in data:
            return data.get("response", "")
        return None

    def complete(self, prompt: str, temperature: float = 0.2) -> Optional[str]:
        data = self._post("/api/generate", {"model": self.s.ollama_model, "prompt": prompt, "options": {"temperature": temperature}})
        if not data:
            return None
        if "response" in data:
            return data["response"]
        return None

    def embed(self, text: str) -> Optional[List[float]]:
        data = self._post("/api/embeddings", {"model": self.s.ollama_embed_model, "prompt": text}, timeout=30)
        if not data:
            return None
        vec = data.get("embedding")
        if isinstance(vec, list):
            return vec
        return None


# ----------------- Analyse offline (sans LLM) -----------------
def split_sections(text: str) -> List[Tuple[str, str]]:
    """Retourne [(theme, paragraphe)] à partir des titres/sous-titres."""
    theme = "Général"
    buff: List[str] = []
    sections: List[Tuple[str, str]] = []
    for line in text.splitlines():
        line = line.rstrip()
        if _title_like(line):
            if buff:
                sections.append((theme, "\n".join(buff).strip()))
                buff = []
            theme = re.sub(r"^(#+|\d+\.)\s*", "", line).strip()
        else:
            buff.append(line)
    if buff:
        sections.append((theme, "\n".join(buff).strip()))
    # split encore par paragraphes
    final: List[Tuple[str, str]] = []
    for th, blk in sections:
        for para in re.split(r"\n\s*\n", blk):
            p = para.strip()
            if p:
                final.append((th, p))
    return final


def extract_pairs(text: str) -> List[Tuple[str, str, str]]:
    """Cherche 'Terme: définition' ou 'X est Y'."""
    pairs: List[Tuple[str, str, str]] = []
    for theme, para in split_sections(text):
        lines = [l.strip() for l in para.splitlines() if l.strip()]
        for line in lines:
            m = re.match(r"(.+?)[\s]*[:\-][\s]*(.+)", line)
            if not m:
                m = re.match(r"(.+?)\s+est\s+(.+)", line, re.IGNORECASE)
            if m:
                term, definition = m.groups()
                pairs.append((theme, term.strip(), definition.strip()))
    return pairs


def extractive_summary(text: str, max_sentences: int = 3) -> str:
    """Résumé extractif simple via scoring mots-clés + position."""
    sents = _sentences(text)
    if not sents:
        return text[:280]
    kw = _keyword_scores(text)
    scored = []
    for i, s in enumerate(sents):
        toks = _tokenize(s)
        score_kw = sum(kw.get(t, 0) for t in toks)
        score_pos = 1.0 / (1 + i)  # priorité aux premières phrases
        scored.append((score_kw + 0.5 * score_pos, s))
    scored.sort(key=lambda x: -x[0])
    picks = [s for _, s in scored[:max_sentences]]
    return " ".join(picks)


def build_items_from_pairs(pairs: List[Tuple[str, str, str]]) -> List[Dict[str, Any]]:
    """Génère QA, QCM, VF, Cloze pour chaque (theme, terme, def)."""
    items: List[Dict[str, Any]] = []
    defs = [p[2] for p in pairs]
    for idx, (theme, term, definition) in enumerate(pairs):
        # QA
        items.append({
            "id": f"qa{idx}",
            "kind": "card",
            "payload": {
                "type": "QA",
                "front": f"{term}",
                "back": definition[:420],
                "theme": theme,
                "keywords": _top_keywords(definition, 5),
            },
        })
        # QCM
        distractors = [d for d in defs if d != definition][:3]
        # complète si <3
        i = 0
        while len(distractors) < 3:
            candidate = f"option_{i}"
            if candidate not in distractors:
                distractors.append(candidate)
            i += 1
        options = distractors + [definition]
        import random
        random.shuffle(options)
        items.append({
            "id": f"mcq{idx}",
            "kind": "exercise",
            "payload": {
                "type": "QCM",
                "q": f"Quelle est la bonne définition de « {term} » ?",
                "options": options,
                "answer": definition,
                "theme": theme,
            },
        })
        # Vrai/Faux
        items.append({
            "id": f"vf{idx}",
            "kind": "card",
            "payload": {
                "type": "VF",
                "front": f"« {term} » correspond à « {definition[:100]} »",
                "answer": "Vrai",
                "theme": theme,
            },
        })
        # Cloze
        first_word = definition.split()[0] if definition.split() else ""
        items.append({
            "id": f"cl{idx}",
            "kind": "card",
            "payload": {
                "type": "CLOZE",
                "front": f"{term} est ____",
                "answer": _normalize(first_word),
                "theme": theme,
            },
        })
    return items


# ----------------- LocalAI haut-niveau -----------------
class LocalAI:
    """Façade unique pour l'IA interne: embeddings, index, RAG, analyse, (Ollama si dispo)."""

    def __init__(self, settings: Optional[LocalAISettings] = None):
        self.s = settings or LocalAISettings()
        self.ollama = OllamaClient(self.s) if self.s.use_ollama else None
        self.embedder = LocalEmbedder(self.s)
        self.index = LocalIndex()  # dim défini au premier add
        self._docs: List[Dict[str, Any]] = []

    # ------- Indexation / RAG -------
    def index_text(self, text: str, metadata: Optional[Dict[str, Any]] = None, split_paragraphs: bool = True):
        """Ajoute un texte (découpé) à l'index sémantique."""
        if not text or not text.strip():
            return
        parts = [p.strip() for p in (re.split(r"\n\s*\n", text) if split_paragraphs else [text]) if p.strip()]
        vecs = self.embedder.embed(parts)
        metas = [metadata or {} for _ in parts]
        if self.index._dim is None and vecs:
            self.index = LocalIndex(dim=len(vecs[0]))
        self.index.add(vecs, parts, metas)
        self._docs.append({"text": text, "meta": metadata or {}})

    def rag_search(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retourne les meilleurs passages pour une question."""
        k = k or self.s.max_passages
        qv = self.embedder.embed([query])[0]
        return self.index.search(qv, top_k=k)

    # ------- Génération offline contrôlée -------
    def analyze_offline(self, text: str) -> Dict[str, Any]:
        """Analyse sans LLM: structure + résumé + termes."""
        sections = split_sections(text)
        pairs = extract_pairs(text)
        summary = extractive_summary(text)
        return {
            "sections": [{"theme": th, "paragraph": p} for th, p in sections],
            "pairs": [{"theme": th, "term": t, "definition": d} for th, t, d in pairs],
            "summary": summary,
            "keywords": _top_keywords(text, 10),
        }

    def generate_items(self, text: str, include_rag: bool = True) -> List[Dict[str, Any]]:
        """Produit des fiches pertinentes à partir d'un texte (offline), option RAG pour enrichir."""
        analysis = self.analyze_offline(text)
        pairs = [(p["theme"], p["term"], p["definition"]) for p in analysis["pairs"]]
        items = build_items_from_pairs(pairs)

        # Enrichir QA avec extraits RAG (pour le verso) si demande
        if include_rag and pairs:
            for it in items:
                if it["kind"] == "card" and it["payload"]["type"] == "QA":
                    term = it["payload"]["front"]
                    ctx = self.rag_search(term, k=3)
                    best = " ".join([c["text"] for c in ctx])[:420] if ctx else ""
                    if best and len(best) > len(it["payload"]["back"]):
                        # Ne remplace que si le contexte est plus riche (et reste ancré au doc)
                        it["payload"]["back"] = best
        return items

    # ------- Fonctions LLM locales via Ollama (facultatif) -------
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        if not self.ollama:
            return None
        return self.ollama.chat(messages, temperature=temperature)

    def complete(self, prompt: str, temperature: float = 0.2) -> Optional[str]:
        if not self.ollama:
            return None
        return self.ollama.complete(prompt, temperature=temperature)

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.embed(texts)


# ----------------- Démo rapide -----------------
if __name__ == "__main__":
    demo_text = """
# Chapitre 1 : Photosynthèse
La photosynthèse est le processus par lequel les plantes transforment l'énergie lumineuse en énergie chimique.
Chlorophylle: pigment qui capte la lumière.
Glucose - principal produit énergétique issu de la photosynthèse.

## Étapes
1. Phase lumineuse: capture d'énergie solaire.
2. Phase sombre: fixation du carbone pour produire du glucose.

# Chapitre 2 : Respiration cellulaire
La respiration cellulaire est le processus d'extraction d'énergie à partir du glucose.
ATP: molécule énergétique universelle.
"""

    ai = LocalAI()
    # Indexation (pour RAG)
    ai.index_text(demo_text, metadata={"source": "demo"})

    print("=== Analyse offline ===")
    analysis = ai.analyze_offline(demo_text)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))

    print("\n=== Fiches générées ===")
    items = ai.generate_items(demo_text, include_rag=True)
    for it in items[:6]:
        print(json.dumps(it, ensure_ascii=False, indent=2))
