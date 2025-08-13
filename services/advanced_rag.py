# services/advanced_rag.py
# -*- coding: utf-8 -*-
"""
Revolutionary RAG System with Advanced Features

This module implements next-generation RAG capabilities:
- Advanced document chunking with semantic boundaries
- Hierarchical embeddings (document → chapter → section → paragraph level)
- Multi-vector retrieval with re-ranking based on relevance and educational value
- Cross-document concept linking and knowledge graph construction
- Citation accuracy with precise source attribution and confidence scoring
"""

from __future__ import annotations

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

try:
    import numpy as np
except ImportError:
    np = None

try:
    import faiss
except ImportError:
    faiss = None

from .rag import RAGIndex


class ChunkType(Enum):
    """Different types of document chunks for hierarchical processing"""
    DOCUMENT = "document"
    CHAPTER = "chapter"  
    SECTION = "section"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"


class ContentType(Enum):
    """Educational content classification"""
    DEFINITION = "definition"
    EXAMPLE = "example"
    EXERCISE = "exercise" 
    THEORY = "theory"
    PROCEDURE = "procedure"
    FACT = "fact"


@dataclass
class SemanticChunk:
    """Represents a semantically coherent chunk of content"""
    id: str
    text: str
    chunk_type: ChunkType
    content_type: ContentType
    level: int  # Hierarchical level (0 = document, 1 = chapter, etc.)
    parent_id: Optional[str]
    children_ids: List[str]
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    confidence_score: float = 0.0


@dataclass
class RetrievalResult:
    """Enhanced retrieval result with educational context"""
    chunk: SemanticChunk
    relevance_score: float
    educational_value: float
    concept_coverage: List[str]
    citations: List[Dict[str, str]]
    confidence: float


class AdvancedRAG:
    """Revolutionary RAG system with educational intelligence"""
    
    def __init__(self):
        self.chunks: Dict[str, SemanticChunk] = {}
        self.hierarchical_index: Dict[ChunkType, RAGIndex] = {}
        self.concept_graph: Dict[str, Set[str]] = defaultdict(set)
        self.citation_index: Dict[str, List[str]] = defaultdict(list)
        
        # Initialize hierarchical indices
        for chunk_type in ChunkType:
            self.hierarchical_index[chunk_type] = RAGIndex()
    
    def process_document(self, text: str, source_metadata: Dict[str, str]) -> List[SemanticChunk]:
        """Process a document with advanced semantic chunking"""
        
        # Stage 1: Intelligent document segmentation
        document_chunks = self._segment_document(text, source_metadata)
        
        # Stage 2: Classify content types
        self._classify_content_types(document_chunks)
        
        # Stage 3: Build hierarchical structure
        self._build_hierarchy(document_chunks)
        
        # Stage 4: Generate embeddings for each level
        self._generate_hierarchical_embeddings(document_chunks)
        
        # Stage 5: Build concept graph
        self._update_concept_graph(document_chunks)
        
        # Stage 6: Index chunks at appropriate levels
        self._index_chunks(document_chunks)
        
        return document_chunks
    
    def _segment_document(self, text: str, source_metadata: Dict[str, str]) -> List[SemanticChunk]:
        """Advanced document segmentation with semantic boundaries"""
        
        chunks = []
        doc_id = hashlib.md5(text.encode()).hexdigest()[:12]
        
        # Document-level chunk
        doc_chunk = SemanticChunk(
            id=f"doc_{doc_id}",
            text=text,
            chunk_type=ChunkType.DOCUMENT,
            content_type=ContentType.THEORY,  # Default classification
            level=0,
            parent_id=None,
            children_ids=[],
            metadata=source_metadata.copy()
        )
        chunks.append(doc_chunk)
        
        # Chapter-level segmentation
        chapters = self._extract_chapters(text)
        for i, chapter in enumerate(chapters):
            chapter_id = f"chap_{doc_id}_{i}"
            chapter_chunk = SemanticChunk(
                id=chapter_id,
                text=chapter["text"],
                chunk_type=ChunkType.CHAPTER,
                content_type=ContentType.THEORY,
                level=1,
                parent_id=doc_chunk.id,
                children_ids=[],
                metadata={**source_metadata, "chapter_title": chapter["title"]}
            )
            chunks.append(chapter_chunk)
            doc_chunk.children_ids.append(chapter_id)
            
            # Section-level segmentation within chapters
            sections = self._extract_sections(chapter["text"])
            for j, section in enumerate(sections):
                section_id = f"sec_{doc_id}_{i}_{j}"
                section_chunk = SemanticChunk(
                    id=section_id,
                    text=section["text"],
                    chunk_type=ChunkType.SECTION,
                    content_type=ContentType.THEORY,
                    level=2,
                    parent_id=chapter_id,
                    children_ids=[],
                    metadata={
                        **source_metadata,
                        "chapter_title": chapter["title"],
                        "section_title": section["title"]
                    }
                )
                chunks.append(section_chunk)
                chapter_chunk.children_ids.append(section_id)
                
                # Paragraph-level segmentation
                paragraphs = self._extract_paragraphs(section["text"])
                for k, paragraph in enumerate(paragraphs):
                    para_id = f"para_{doc_id}_{i}_{j}_{k}"
                    para_chunk = SemanticChunk(
                        id=para_id,
                        text=paragraph,
                        chunk_type=ChunkType.PARAGRAPH,
                        content_type=ContentType.THEORY,
                        level=3,
                        parent_id=section_id,
                        children_ids=[],
                        metadata={
                            **source_metadata,
                            "chapter_title": chapter["title"],
                            "section_title": section["title"],
                            "paragraph_index": k
                        }
                    )
                    chunks.append(para_chunk)
                    section_chunk.children_ids.append(para_id)
        
        return chunks
    
    def _extract_chapters(self, text: str) -> List[Dict[str, str]]:
        """Extract chapters using advanced pattern recognition"""
        
        chapters = []
        
        # Pattern 1: Numbered chapters (Chapitre 1, Chapter 1, etc.)
        chapter_pattern = r'^(?:Chapitre|Chapter|Partie|Part)\s*(\d+)[:.]?\s*(.*)$'
        matches = list(re.finditer(chapter_pattern, text, re.MULTILINE | re.IGNORECASE))
        
        if matches:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                title = match.group(2).strip() or f"Chapitre {match.group(1)}"
                chapter_text = text[start:end].strip()
                
                chapters.append({
                    "title": title,
                    "text": chapter_text,
                    "number": match.group(1)
                })
        else:
            # Pattern 2: Header-based segmentation
            header_pattern = r'^(#{1,3})\s+(.+)$'
            matches = list(re.finditer(header_pattern, text, re.MULTILINE))
            
            if matches:
                # Only use level 1 headers for chapters
                chapter_matches = [m for m in matches if len(m.group(1)) == 1]
                
                for i, match in enumerate(chapter_matches):
                    start = match.start()
                    end = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
                    
                    title = match.group(2).strip()
                    chapter_text = text[start:end].strip()
                    
                    chapters.append({
                        "title": title,
                        "text": chapter_text,
                        "number": str(i + 1)
                    })
            else:
                # Fallback: Split by double newlines and length
                parts = text.split('\n\n')
                current_chapter = ""
                chapter_num = 1
                
                for part in parts:
                    current_chapter += part + '\n\n'
                    if len(current_chapter) > 2000:  # ~500 words
                        chapters.append({
                            "title": f"Section {chapter_num}",
                            "text": current_chapter.strip(),
                            "number": str(chapter_num)
                        })
                        current_chapter = ""
                        chapter_num += 1
                
                if current_chapter:
                    chapters.append({
                        "title": f"Section {chapter_num}",
                        "text": current_chapter.strip(),
                        "number": str(chapter_num)
                    })
        
        return chapters if chapters else [{"title": "Document complet", "text": text, "number": "1"}]
    
    def _extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract sections within a chapter"""
        
        sections = []
        
        # Pattern 1: Numbered sections (1.1, 1.2, etc.)
        section_pattern = r'^(\d+\.\d+)\s*[:.]?\s*(.*)$'
        matches = list(re.finditer(section_pattern, text, re.MULTILINE))
        
        if matches:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                title = match.group(2).strip() or f"Section {match.group(1)}"
                section_text = text[start:end].strip()
                
                sections.append({
                    "title": title,
                    "text": section_text,
                    "number": match.group(1)
                })
        else:
            # Pattern 2: Header-based (## or ###)
            header_pattern = r'^(#{2,3})\s+(.+)$'
            matches = list(re.finditer(header_pattern, text, re.MULTILINE))
            
            if matches:
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    
                    title = match.group(2).strip()
                    section_text = text[start:end].strip()
                    
                    sections.append({
                        "title": title,
                        "text": section_text,
                        "number": f"{i + 1}"
                    })
            else:
                # Fallback: Split by semantic breaks
                paragraphs = text.split('\n\n')
                current_section = ""
                section_num = 1
                
                for paragraph in paragraphs:
                    current_section += paragraph + '\n\n'
                    if len(current_section) > 800:  # ~200 words
                        sections.append({
                            "title": f"Partie {section_num}",
                            "text": current_section.strip(),
                            "number": str(section_num)
                        })
                        current_section = ""
                        section_num += 1
                
                if current_section:
                    sections.append({
                        "title": f"Partie {section_num}",
                        "text": current_section.strip(),
                        "number": str(section_num)
                    })
        
        return sections if sections else [{"title": "Section complète", "text": text, "number": "1"}]
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract meaningful paragraphs with semantic boundaries"""
        
        # Split by double newlines first
        raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Filter out very short paragraphs and merge if needed
        paragraphs = []
        current_para = ""
        
        for para in raw_paragraphs:
            # Skip headers and very short content
            if (len(para) < 50 or 
                re.match(r'^#{1,6}\s', para) or  # Markdown headers
                re.match(r'^\d+\.\s*$', para)):  # Just numbers
                continue
                
            current_para += para
            
            # If paragraph is long enough or ends with sentence-ending punctuation
            if (len(current_para) > 150 or 
                re.search(r'[.!?]\s*$', current_para)):
                paragraphs.append(current_para.strip())
                current_para = ""
            else:
                current_para += " "
        
        if current_para:
            paragraphs.append(current_para.strip())
        
        return paragraphs if paragraphs else [text]
    
    def _classify_content_types(self, chunks: List[SemanticChunk]) -> None:
        """Classify content types using pattern recognition"""
        
        for chunk in chunks:
            chunk.content_type = self._classify_chunk_content(chunk.text)
    
    def _classify_chunk_content(self, text: str) -> ContentType:
        """Classify a chunk based on its content patterns"""
        
        text_lower = text.lower()
        
        # Definition patterns
        if (re.search(r'\best\s+défini|se\s+définit|définition|est\s+un[e]?\s+\w+\s+qui', text_lower) or
            re.search(r':\s*[A-Z].*(?:est|sont|désigne|représente)', text)):
            return ContentType.DEFINITION
        
        # Example patterns  
        if (re.search(r'\bpar\s+exemple|exemple|illustration|prenons\s+le\s+cas', text_lower) or
            re.search(r'\bainsi|notamment|comme\s+dans', text_lower)):
            return ContentType.EXAMPLE
        
        # Exercise patterns
        if (re.search(r'\bexercice|question|problème|calculez|trouvez|déterminez', text_lower) or
            re.search(r'\brépondez|complétez|choisissez|quelle\s+est', text_lower)):
            return ContentType.EXERCISE
        
        # Procedure patterns
        if (re.search(r'\bétapes?|procédure|méthode|algorithme|protocole', text_lower) or
            re.search(r'\bd\'abord|ensuite|puis|enfin|premièrement', text_lower)):
            return ContentType.PROCEDURE
        
        # Fact patterns
        if (re.search(r'\ben\s+\d{4}|le\s+\d+|statistique|données?|résultat', text_lower) or
            re.search(r'\bselon|d\'après|étude\s+montre', text_lower)):
            return ContentType.FACT
        
        # Default to theory
        return ContentType.THEORY
    
    def _build_hierarchy(self, chunks: List[SemanticChunk]) -> None:
        """Build hierarchical relationships between chunks"""
        
        # Store chunks by ID for quick lookup
        chunk_map = {chunk.id: chunk for chunk in chunks}
        
        # Update chunk references
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            
            # Verify parent-child relationships
            for child_id in chunk.children_ids:
                if child_id in chunk_map:
                    child_chunk = chunk_map[child_id]
                    child_chunk.parent_id = chunk.id
    
    def _generate_hierarchical_embeddings(self, chunks: List[SemanticChunk]) -> None:
        """Generate embeddings for chunks at different hierarchical levels"""
        
        # Group chunks by type for batch processing
        chunks_by_type = defaultdict(list)
        for chunk in chunks:
            chunks_by_type[chunk.chunk_type].append(chunk)
        
        # Generate embeddings for each type
        for chunk_type, type_chunks in chunks_by_type.items():
            texts = [chunk.text for chunk in type_chunks]
            
            # Use the existing RAG index for embedding generation
            # This is a simplified approach - in practice, you'd want more sophisticated embedding
            try:
                if hasattr(self.hierarchical_index[chunk_type], 'model') and self.hierarchical_index[chunk_type].model:
                    embeddings = self.hierarchical_index[chunk_type].model.encode(texts)
                    for chunk, embedding in zip(type_chunks, embeddings):
                        chunk.embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                        chunk.confidence_score = 0.8  # Base confidence
                else:
                    # Fallback to simple text features
                    for chunk in type_chunks:
                        chunk.embedding = self._simple_text_features(chunk.text)
                        chunk.confidence_score = 0.6  # Lower confidence for fallback
            except Exception:
                # Ultimate fallback
                for chunk in type_chunks:
                    chunk.embedding = self._simple_text_features(chunk.text)
                    chunk.confidence_score = 0.4
    
    def _simple_text_features(self, text: str) -> List[float]:
        """Generate simple text features as embedding fallback"""
        
        features = []
        
        # Length features
        features.append(len(text) / 1000.0)  # Normalized length
        features.append(len(text.split()) / 100.0)  # Normalized word count
        
        # Character features
        features.append(text.count('?') / len(text))  # Question density
        features.append(text.count('!') / len(text))  # Exclamation density
        features.append(text.count('.') / len(text))  # Period density
        
        # Word features
        words = text.lower().split()
        if words:
            features.append(sum(len(w) for w in words) / len(words))  # Avg word length
            features.append(len(set(words)) / len(words))  # Lexical diversity
        else:
            features.extend([0.0, 0.0])
        
        # Pad to fixed size (16 dimensions)
        while len(features) < 16:
            features.append(0.0)
        
        return features[:16]
    
    def _update_concept_graph(self, chunks: List[SemanticChunk]) -> None:
        """Build cross-document concept linking"""
        
        for chunk in chunks:
            concepts = self._extract_concepts(chunk.text)
            
            # Add concepts to graph
            for concept in concepts:
                self.concept_graph[concept].add(chunk.id)
                
                # Link related concepts
                for other_concept in concepts:
                    if concept != other_concept:
                        self.concept_graph[concept].add(other_concept)
    
    def _extract_concepts(self, text: str) -> Set[str]:
        """Extract key concepts from text"""
        
        concepts = set()
        
        # Extract capitalized terms (likely proper nouns/concepts)
        capitalized = re.findall(r'\b[A-ZÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜ][a-záàâäéèêëíìîïóòôöúùûü]{2,}\b', text)
        concepts.update(capitalized)
        
        # Extract terms that appear in definitions
        definition_terms = re.findall(r'([A-Za-z]+)(?:\s+est\s+|:\s+)', text)
        concepts.update(definition_terms)
        
        # Extract terms that appear multiple times (likely important)
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        frequent_words = [word for word, count in word_counts.items() if count >= 2]
        concepts.update(frequent_words)
        
        return concepts
    
    def _index_chunks(self, chunks: List[SemanticChunk]) -> None:
        """Index chunks in the appropriate hierarchical levels"""
        
        for chunk in chunks:
            # Build passages for the existing RAG index
            self.hierarchical_index[chunk.chunk_type].build(chunk.text)
            
            # Update citation index
            source = chunk.metadata.get('source', 'unknown')
            self.citation_index[chunk.id] = [source]
    
    def multi_level_retrieval(self, query: str, top_k: int = 5, 
                            include_levels: Optional[List[ChunkType]] = None) -> List[RetrievalResult]:
        """Perform multi-level retrieval with educational value ranking"""
        
        if include_levels is None:
            include_levels = [ChunkType.PARAGRAPH, ChunkType.SECTION, ChunkType.CHAPTER]
        
        all_results = []
        
        # Search at each specified level
        for chunk_type in include_levels:
            if chunk_type in self.hierarchical_index:
                # Get raw search results
                passages = self.hierarchical_index[chunk_type].search(query, top_k * 2)
                
                # Convert to enhanced results
                for passage in passages:
                    chunk = self._find_chunk_by_text(passage, chunk_type)
                    if chunk:
                        result = RetrievalResult(
                            chunk=chunk,
                            relevance_score=self._calculate_relevance(query, chunk.text),
                            educational_value=self._calculate_educational_value(chunk),
                            concept_coverage=self._get_concept_coverage(query, chunk.text),
                            citations=self._get_citations(chunk),
                            confidence=chunk.confidence_score
                        )
                        all_results.append(result)
        
        # Re-rank by educational value and relevance
        all_results.sort(key=lambda r: (r.educational_value * 0.6 + r.relevance_score * 0.4), reverse=True)
        
        return all_results[:top_k]
    
    def _find_chunk_by_text(self, text: str, chunk_type: ChunkType) -> Optional[SemanticChunk]:
        """Find chunk by text content and type"""
        
        for chunk in self.chunks.values():
            if chunk.chunk_type == chunk_type and text in chunk.text:
                return chunk
        return None
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """Calculate relevance score between query and text"""
        
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(query_words.intersection(text_words))
        union = len(query_words.union(text_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_educational_value(self, chunk: SemanticChunk) -> float:
        """Calculate educational value score for a chunk"""
        
        score = 0.0
        
        # Content type weights
        type_weights = {
            ContentType.DEFINITION: 0.9,
            ContentType.EXAMPLE: 0.8,
            ContentType.EXERCISE: 0.7,
            ContentType.PROCEDURE: 0.8,
            ContentType.THEORY: 0.6,
            ContentType.FACT: 0.5
        }
        score += type_weights.get(chunk.content_type, 0.5)
        
        # Length bonus (not too short, not too long)
        text_length = len(chunk.text)
        if 100 <= text_length <= 500:
            score += 0.2
        elif 500 < text_length <= 1000:
            score += 0.1
        
        # Hierarchical level bonus
        level_weights = {0: 0.1, 1: 0.3, 2: 0.5, 3: 0.7}  # Prefer mid-level chunks
        score += level_weights.get(chunk.level, 0.3)
        
        return min(score, 1.0)
    
    def _get_concept_coverage(self, query: str, text: str) -> List[str]:
        """Get concepts covered by the text relevant to query"""
        
        query_concepts = self._extract_concepts(query)
        text_concepts = self._extract_concepts(text)
        
        return list(query_concepts.intersection(text_concepts))
    
    def _get_citations(self, chunk: SemanticChunk) -> List[Dict[str, str]]:
        """Get citation information for a chunk"""
        
        citations = []
        
        # Primary source
        source = chunk.metadata.get('source', 'Unknown source')
        citation = {
            "source": source,
            "chunk_id": chunk.id,
            "level": chunk.chunk_type.value,
            "confidence": str(chunk.confidence_score)
        }
        
        if 'chapter_title' in chunk.metadata:
            citation["chapter"] = chunk.metadata['chapter_title']
        if 'section_title' in chunk.metadata:
            citation["section"] = chunk.metadata['section_title']
        
        citations.append(citation)
        
        return citations
    
    def get_concept_network(self, concept: str, depth: int = 2) -> Dict[str, Any]:
        """Get the concept network for a given concept"""
        
        if concept not in self.concept_graph:
            return {"concept": concept, "related": [], "chunks": []}
        
        # Get directly related concepts
        direct_related = list(self.concept_graph[concept])
        
        # Get chunks containing this concept
        related_chunks = []
        for chunk_id in direct_related:
            if chunk_id in self.chunks:
                related_chunks.append({
                    "id": chunk_id,
                    "type": self.chunks[chunk_id].chunk_type.value,
                    "content_type": self.chunks[chunk_id].content_type.value,
                    "text_preview": self.chunks[chunk_id].text[:200] + "..."
                })
        
        # Get second-degree relations if depth > 1
        extended_related = set(direct_related)
        if depth > 1:
            for related_concept in direct_related[:10]:  # Limit to prevent explosion
                if related_concept in self.concept_graph:
                    extended_related.update(list(self.concept_graph[related_concept])[:5])
        
        return {
            "concept": concept,
            "direct_related": [c for c in direct_related if c in self.chunks],
            "extended_related": list(extended_related),
            "chunks": related_chunks,
            "network_size": len(self.concept_graph[concept])
        }


# Global instance for easy access
advanced_rag = AdvancedRAG()