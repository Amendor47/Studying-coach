# services/advanced_document_analysis.py
# -*- coding: utf-8 -*-
"""
Revolutionary Document Analysis Pipeline

This module implements advanced document processing capabilities:
- Multi-format support: PDF, DOCX, TXT, images, handwritten notes (OCR)
- Intelligent content segmentation: chapters, sections, definitions, examples, exercises
- Mathematical formula recognition and LaTeX rendering
- Diagram and image analysis with educational context understanding
- Language detection and multilingual support
- Automatic content intelligence and smart content classification
"""

from __future__ import annotations

import re
import json
import base64
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Optional dependencies for advanced features
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import langdetect
except ImportError:
    langdetect = None

from .parsers import extract_text, EXTRACTORS
from .chunker import normalize_text


class DocumentType(Enum):
    """Different types of documents for specialized processing"""
    TEXT = "text"
    ACADEMIC_PAPER = "academic_paper"
    TEXTBOOK = "textbook"
    LECTURE_NOTES = "lecture_notes"
    HANDWRITTEN = "handwritten"
    MIXED_MEDIA = "mixed_media"
    TECHNICAL_MANUAL = "technical_manual"


class ContentSegmentType(Enum):
    """Types of content segments for intelligent classification"""
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    DEFINITION = "definition"
    THEOREM = "theorem"
    EXAMPLE = "example"
    EXERCISE = "exercise"
    FORMULA = "formula"
    FIGURE = "figure"
    TABLE = "table"
    LIST = "list"
    QUOTE = "quote"
    CODE = "code"


@dataclass
class DocumentMetadata:
    """Comprehensive document metadata"""
    filename: str
    file_type: str
    document_type: DocumentType
    language: str
    page_count: int
    word_count: int
    has_formulas: bool
    has_images: bool
    has_tables: bool
    complexity_score: float
    reading_level: str


@dataclass
class ContentSegment:
    """Represents a classified content segment"""
    id: str
    type: ContentSegmentType
    content: str
    raw_content: str
    start_position: int
    end_position: int
    confidence_score: float
    metadata: Dict[str, Any]
    
    # Mathematical content
    latex_formula: Optional[str] = None
    formula_type: Optional[str] = None
    
    # Visual content
    image_data: Optional[str] = None
    image_description: Optional[str] = None
    
    # Hierarchical information
    level: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []


@dataclass
class FormulaAnalysis:
    """Analysis of mathematical formulas"""
    original_text: str
    latex_representation: str
    formula_type: str  # "equation", "inequality", "expression", etc.
    variables: List[str]
    constants: List[str]
    operations: List[str]
    complexity_level: int  # 1-5
    subject_area: str  # "algebra", "calculus", "statistics", etc.


class AdvancedDocumentAnalyzer:
    """Revolutionary document analysis system"""
    
    def __init__(self):
        self.ocr_enabled = pytesseract is not None
        self.cv_enabled = cv2 is not None and np is not None
        self.pil_enabled = Image is not None
        self.lang_detection_enabled = langdetect is not None
        
        # Mathematical patterns for formula recognition
        self.math_patterns = [
            r'[A-Za-z]\s*[=≈≠<>≤≥]\s*[^.]*',  # Variable equations
            r'∫.*?d[A-Za-z]',  # Integrals
            r'∑.*?=.*?',  # Summations
            r'lim.*?→.*?',  # Limits
            r'∂.*?/∂.*?',  # Partial derivatives
            r'√\([^)]+\)',  # Square roots
            r'\b\w+\^\w+\b',  # Exponents
            r'[A-Za-z]+\([^)]+\)',  # Functions
            r'\|[^|]+\|',  # Absolute values
            r'[A-Za-z]+_\w+',  # Subscripts
        ]
        
        # Academic document patterns
        self.academic_patterns = {
            'definition': [
                r'Definition\s+\d*\.?\s*:?(.+)',
                r'Définition\s+\d*\.?\s*:?(.+)',
                r'(.+)\s+est\s+défini[e]?\s+par',
                r'(.+)\s+désigne',
                r'On\s+appelle\s+(.+)',
                r'(.+):\s*[A-Z].*(?:est|sont|désigne|représente)'
            ],
            'theorem': [
                r'Theorem\s+\d*\.?\s*:?(.+)',
                r'Théorème\s+\d*\.?\s*:?(.+)',
                r'Lemma\s+\d*\.?\s*:?(.+)',
                r'Lemme\s+\d*\.?\s*:?(.+)',
                r'Proposition\s+\d*\.?\s*:?(.+)',
                r'Corollary\s+\d*\.?\s*:?(.+)',
                r'Corollaire\s+\d*\.?\s*:?(.+)'
            ],
            'example': [
                r'Example\s+\d*\.?\s*:?(.+)',
                r'Exemple\s+\d*\.?\s*:?(.+)',
                r'Par\s+exemple[,:](.+)',
                r'Illustration\s*:?(.+)',
                r'Considérons(.+)',
                r'Prenons\s+le\s+cas(.+)'
            ],
            'exercise': [
                r'Exercise\s+\d*\.?\s*:?(.+)',
                r'Exercice\s+\d*\.?\s*:?(.+)',
                r'Problem\s+\d*\.?\s*:?(.+)',
                r'Problème\s+\d*\.?\s*:?(.+)',
                r'Question\s+\d*\.?\s*:?(.+)',
                r'Calculez(.+)',
                r'Déterminez(.+)',
                r'Trouvez(.+)',
                r'Montrez\s+que(.+)',
                r'Démontrez(.+)'
            ]
        }
    
    def analyze_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Comprehensive document analysis pipeline"""
        
        # Stage 1: Extract raw content
        if self._is_image_file(filename):
            raw_text = self._extract_text_from_image(file_path)
            document_type = DocumentType.HANDWRITTEN
        else:
            raw_text = extract_text(file_path, filename)
            document_type = self._classify_document_type(raw_text, filename)
        
        # Stage 2: Generate document metadata
        metadata = self._generate_metadata(raw_text, filename, document_type)
        
        # Stage 3: Intelligent content segmentation
        segments = self._segment_content(raw_text, document_type)
        
        # Stage 4: Mathematical formula analysis
        formulas = self._analyze_mathematical_content(raw_text)
        
        # Stage 5: Educational content classification
        classified_content = self._classify_educational_content(segments)
        
        # Stage 6: Generate learning objectives
        learning_objectives = self._generate_learning_objectives(segments, formulas)
        
        # Stage 7: Extract key concepts and relationships
        concept_map = self._build_concept_map(segments)
        
        return {
            "metadata": metadata,
            "segments": [self._serialize_segment(s) for s in segments],
            "formulas": formulas,
            "classified_content": classified_content,
            "learning_objectives": learning_objectives,
            "concept_map": concept_map,
            "educational_insights": self._generate_educational_insights(segments, formulas)
        }
    
    def _is_image_file(self, filename: str) -> bool:
        """Check if file is an image format"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
        return Path(filename).suffix.lower() in image_extensions
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from images using OCR"""
        if not self.ocr_enabled or not self.pil_enabled:
            return "OCR not available - install pytesseract and PIL"
        
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance image for better OCR
            image = self._enhance_image_for_ocr(image)
            
            # Extract text with multiple OCR engines/modes
            text_results = []
            
            # Standard OCR
            text_results.append(pytesseract.image_to_string(image, lang='eng+fra'))
            
            # OCR optimized for equations (if available)
            try:
                math_text = pytesseract.image_to_string(
                    image, 
                    config='--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-*/=()[]{}∑∫∂√π'
                )
                text_results.append(math_text)
            except:
                pass
            
            # Combine results and choose best
            best_text = max(text_results, key=len) if text_results else ""
            
            return normalize_text(best_text)
            
        except Exception as e:
            return f"OCR extraction failed: {str(e)}"
    
    def _enhance_image_for_ocr(self, image: Image) -> Image:
        """Enhance image quality for better OCR results"""
        if not self.pil_enabled:
            return image
        
        try:
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Increase sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Remove noise
            image = image.filter(ImageFilter.MedianFilter())
            
            # Resize if too small
            width, height = image.size
            if width < 800 or height < 600:
                scale_factor = max(800/width, 600/height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.LANCZOS)
            
            return image
            
        except Exception:
            return image
    
    def _classify_document_type(self, text: str, filename: str) -> DocumentType:
        """Classify document type based on content and filename"""
        
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Check filename patterns
        if any(term in filename_lower for term in ['lecture', 'cours', 'notes']):
            return DocumentType.LECTURE_NOTES
        elif any(term in filename_lower for term in ['manual', 'guide', 'handbook']):
            return DocumentType.TECHNICAL_MANUAL
        
        # Check content patterns
        academic_indicators = [
            'theorem', 'théorème', 'lemma', 'lemme', 'proposition', 'corollary',
            'proof', 'démonstration', 'definition', 'définition'
        ]
        if sum(text_lower.count(indicator) for indicator in academic_indicators) >= 3:
            return DocumentType.ACADEMIC_PAPER
        
        textbook_indicators = [
            'chapter', 'chapitre', 'exercise', 'exercice', 'example', 'exemple',
            'section', 'summary', 'résumé'
        ]
        if sum(text_lower.count(indicator) for indicator in textbook_indicators) >= 5:
            return DocumentType.TEXTBOOK
        
        # Check for mathematical content
        math_count = sum(1 for pattern in self.math_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
        if math_count >= 10:
            return DocumentType.TECHNICAL_MANUAL
        
        return DocumentType.TEXT
    
    def _generate_metadata(self, text: str, filename: str, doc_type: DocumentType) -> DocumentMetadata:
        """Generate comprehensive document metadata"""
        
        # Basic counts
        word_count = len(text.split())
        
        # Estimate page count (assuming ~250 words per page)
        page_count = max(1, word_count // 250)
        
        # Language detection
        language = "unknown"
        if self.lang_detection_enabled and text.strip():
            try:
                language = langdetect.detect(text)
            except:
                # Fallback to simple heuristics
                if any(word in text.lower() for word in ['the', 'and', 'is', 'are', 'this']):
                    language = "en"
                elif any(word in text.lower() for word in ['le', 'la', 'les', 'est', 'sont', 'cette']):
                    language = "fr"
        
        # Content analysis
        has_formulas = any(re.search(pattern, text, re.IGNORECASE) 
                          for pattern in self.math_patterns)
        has_images = 'figure' in text.lower() or 'image' in text.lower()
        has_tables = 'table' in text.lower() or '|' in text
        
        # Complexity assessment
        complexity_score = self._assess_complexity(text)
        reading_level = self._determine_reading_level(complexity_score)
        
        return DocumentMetadata(
            filename=filename,
            file_type=Path(filename).suffix.lower(),
            document_type=doc_type,
            language=language,
            page_count=page_count,
            word_count=word_count,
            has_formulas=has_formulas,
            has_images=has_images,
            has_tables=has_tables,
            complexity_score=complexity_score,
            reading_level=reading_level
        )
    
    def _assess_complexity(self, text: str) -> float:
        """Assess document complexity (0.0 to 1.0)"""
        score = 0.0
        
        # Word complexity
        words = text.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            score += min(0.3, avg_word_length / 15)  # Max 0.3 for word length
        
        # Sentence complexity
        sentences = re.split(r'[.!?]+', text)
        if sentences:
            avg_sentence_length = sum(len(sent.split()) for sent in sentences) / len(sentences)
            score += min(0.3, avg_sentence_length / 30)  # Max 0.3 for sentence length
        
        # Technical terminology
        technical_terms = len(re.findall(r'\b[A-Za-z]{8,}\b', text))
        score += min(0.2, technical_terms / len(words) * 10) if words else 0
        
        # Mathematical content
        math_count = sum(1 for pattern in self.math_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
        score += min(0.2, math_count / 100)
        
        return min(1.0, score)
    
    def _determine_reading_level(self, complexity: float) -> str:
        """Determine reading level based on complexity score"""
        if complexity < 0.2:
            return "Elementary"
        elif complexity < 0.4:
            return "Middle School"
        elif complexity < 0.6:
            return "High School"
        elif complexity < 0.8:
            return "College"
        else:
            return "Graduate"
    
    def _segment_content(self, text: str, doc_type: DocumentType) -> List[ContentSegment]:
        """Intelligent content segmentation"""
        
        segments = []
        current_pos = 0
        segment_id = 0
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            segment_type, confidence = self._classify_line_type(line)
            
            # Determine content extent for this segment
            content_lines = [line]
            end_pos = current_pos + len(line)
            
            # For paragraphs and some other types, include following lines
            if segment_type in [ContentSegmentType.PARAGRAPH, ContentSegmentType.DEFINITION, 
                              ContentSegmentType.EXAMPLE, ContentSegmentType.THEOREM]:
                j = i + 1
                while j < len(lines) and lines[j].strip():
                    next_line = lines[j].strip()
                    next_type, _ = self._classify_line_type(next_line)
                    
                    # Stop if we hit a new structural element
                    if next_type in [ContentSegmentType.TITLE, ContentSegmentType.HEADING]:
                        break
                    
                    content_lines.append(next_line)
                    end_pos += len(next_line) + 1  # +1 for newline
                    j += 1
                
                i = j - 1  # Adjust loop counter
            
            # Create segment
            full_content = '\n'.join(content_lines)
            
            segment = ContentSegment(
                id=f"seg_{segment_id}",
                type=segment_type,
                content=self._clean_content(full_content),
                raw_content=full_content,
                start_position=current_pos,
                end_position=end_pos,
                confidence_score=confidence,
                metadata=self._extract_segment_metadata(full_content, segment_type),
                level=self._determine_hierarchical_level(line)
            )
            
            # Special processing for formulas
            if segment_type == ContentSegmentType.FORMULA:
                segment.latex_formula = self._convert_to_latex(full_content)
                segment.formula_type = self._classify_formula_type(full_content)
            
            segments.append(segment)
            current_pos = end_pos + 2  # +2 for double newline
            segment_id += 1
            i += 1
        
        return segments
    
    def _classify_line_type(self, line: str) -> Tuple[ContentSegmentType, float]:
        """Classify a line of text and return confidence score"""
        
        line_stripped = line.strip()
        
        # Title patterns (high confidence indicators)
        if re.match(r'^[A-Z\s]{10,}$', line_stripped):  # All caps titles
            return ContentSegmentType.TITLE, 0.9
        
        # Heading patterns
        heading_patterns = [
            r'^\d+\.\s+[A-Z]',  # "1. Chapter Title"
            r'^[A-Z][a-z]+\s+\d+',  # "Chapter 1"
            r'^#{1,6}\s+',  # Markdown headers
            r'^[A-Z][^.]{10,50}$'  # Capitalized short lines
        ]
        for pattern in heading_patterns:
            if re.match(pattern, line_stripped):
                return ContentSegmentType.HEADING, 0.8
        
        # Definition patterns
        for pattern in self.academic_patterns['definition']:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return ContentSegmentType.DEFINITION, 0.9
        
        # Theorem patterns
        for pattern in self.academic_patterns['theorem']:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return ContentSegmentType.THEOREM, 0.9
        
        # Example patterns
        for pattern in self.academic_patterns['example']:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return ContentSegmentType.EXAMPLE, 0.8
        
        # Exercise patterns
        for pattern in self.academic_patterns['exercise']:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return ContentSegmentType.EXERCISE, 0.8
        
        # Formula patterns
        for pattern in self.math_patterns:
            if re.search(pattern, line_stripped):
                return ContentSegmentType.FORMULA, 0.7
        
        # List patterns
        if re.match(r'^\s*[-•*]\s+|^\s*\d+\.\s+', line_stripped):
            return ContentSegmentType.LIST, 0.8
        
        # Quote patterns
        if line_stripped.startswith('"') or line_stripped.startswith('«'):
            return ContentSegmentType.QUOTE, 0.7
        
        # Table patterns
        if '|' in line_stripped and line_stripped.count('|') >= 2:
            return ContentSegmentType.TABLE, 0.8
        
        # Code patterns
        if (line_stripped.startswith('```') or 
            re.match(r'^\s{4,}[a-zA-Z]', line_stripped) or
            any(keyword in line_stripped for keyword in ['def ', 'class ', 'function', 'var '])):
            return ContentSegmentType.CODE, 0.7
        
        # Default to paragraph
        return ContentSegmentType.PARAGRAPH, 0.6
    
    def _clean_content(self, content: str) -> str:
        """Clean content while preserving important formatting"""
        
        # Remove excessive whitespace while preserving structure
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove leading/trailing whitespace
            cleaned_line = line.strip()
            if cleaned_line:  # Only keep non-empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_segment_metadata(self, content: str, segment_type: ContentSegmentType) -> Dict[str, Any]:
        """Extract relevant metadata for a content segment"""
        
        metadata = {
            "word_count": len(content.split()),
            "char_count": len(content),
            "has_numbers": bool(re.search(r'\d+', content)),
            "has_formulas": any(re.search(pattern, content) for pattern in self.math_patterns),
            "complexity": self._assess_complexity(content)
        }
        
        # Type-specific metadata
        if segment_type == ContentSegmentType.DEFINITION:
            # Extract the term being defined
            for pattern in self.academic_patterns['definition']:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    metadata["defined_term"] = match.group(1).strip()
                    break
        
        elif segment_type == ContentSegmentType.EXERCISE:
            # Identify question type
            if '?' in content:
                metadata["has_questions"] = True
                metadata["question_count"] = content.count('?')
            
            if any(word in content.lower() for word in ['calculate', 'calculez', 'find', 'trouvez']):
                metadata["exercise_type"] = "calculation"
            elif any(word in content.lower() for word in ['prove', 'démontrez', 'show', 'montrez']):
                metadata["exercise_type"] = "proof"
            else:
                metadata["exercise_type"] = "general"
        
        elif segment_type == ContentSegmentType.FORMULA:
            # Formula-specific analysis
            metadata["variables"] = list(set(re.findall(r'\b[a-zA-Z]\b', content)))
            metadata["operators"] = list(set(re.findall(r'[+\-*/=<>≤≥≠≈]', content)))
        
        return metadata
    
    def _determine_hierarchical_level(self, line: str) -> int:
        """Determine hierarchical level of content (0=top level)"""
        
        # Markdown headers
        if line.startswith('#'):
            return line.count('#') - 1
        
        # Numbered sections
        match = re.match(r'^(\d+(?:\.\d+)*)', line.strip())
        if match:
            return match.group(1).count('.')
        
        # Default levels based on formatting
        if re.match(r'^[A-Z\s]{10,}$', line.strip()):  # All caps
            return 0
        elif re.match(r'^[A-Z][^.]{10,50}$', line.strip()):  # Title case
            return 1
        else:
            return 2
    
    def _analyze_mathematical_content(self, text: str) -> List[FormulaAnalysis]:
        """Comprehensive mathematical formula analysis"""
        
        formulas = []
        
        for i, pattern in enumerate(self.math_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                formula_text = match.group()
                
                analysis = FormulaAnalysis(
                    original_text=formula_text,
                    latex_representation=self._convert_to_latex(formula_text),
                    formula_type=self._classify_formula_type(formula_text),
                    variables=self._extract_variables(formula_text),
                    constants=self._extract_constants(formula_text),
                    operations=self._extract_operations(formula_text),
                    complexity_level=self._assess_formula_complexity(formula_text),
                    subject_area=self._classify_subject_area(formula_text)
                )
                
                formulas.append(analysis)
        
        # Remove duplicates
        unique_formulas = []
        seen_formulas = set()
        
        for formula in formulas:
            if formula.original_text not in seen_formulas:
                unique_formulas.append(formula)
                seen_formulas.add(formula.original_text)
        
        return unique_formulas
    
    def _convert_to_latex(self, formula_text: str) -> str:
        """Convert mathematical expression to LaTeX format"""
        
        latex = formula_text
        
        # Common conversions
        conversions = {
            '∫': r'\int',
            '∑': r'\sum',
            '∂': r'\partial',
            '√': r'\sqrt',
            '∞': r'\infty',
            'π': r'\pi',
            '≈': r'\approx',
            '≠': r'\neq',
            '≤': r'\leq',
            '≥': r'\geq',
            '→': r'\rightarrow',
            '←': r'\leftarrow',
            '↑': r'\uparrow',
            '↓': r'\downarrow'
        }
        
        for symbol, latex_cmd in conversions.items():
            latex = latex.replace(symbol, latex_cmd)
        
        # Handle superscripts and subscripts
        latex = re.sub(r'(\w+)\^(\w+)', r'\1^{\2}', latex)
        latex = re.sub(r'(\w+)_(\w+)', r'\1_{\2}', latex)
        
        # Handle fractions
        latex = re.sub(r'(\w+)/(\w+)', r'\\frac{\1}{\2}', latex)
        
        return latex
    
    def _classify_formula_type(self, formula: str) -> str:
        """Classify the type of mathematical formula"""
        
        if '=' in formula:
            if '<' in formula or '>' in formula or '≤' in formula or '≥' in formula:
                return "inequality"
            else:
                return "equation"
        elif '∫' in formula:
            return "integral"
        elif '∑' in formula:
            return "summation"
        elif 'lim' in formula.lower():
            return "limit"
        elif '∂' in formula:
            return "partial_derivative"
        elif any(op in formula for op in ['+', '-', '*', '/', '^']):
            return "expression"
        else:
            return "formula"
    
    def _extract_variables(self, formula: str) -> List[str]:
        """Extract variables from mathematical formula"""
        # Simple heuristic: single letters that aren't common constants
        common_constants = {'e', 'π', 'i'}
        variables = set(re.findall(r'\b[a-zA-Z]\b', formula))
        return list(variables - common_constants)
    
    def _extract_constants(self, formula: str) -> List[str]:
        """Extract constants from mathematical formula"""
        constants = []
        
        # Numeric constants
        constants.extend(re.findall(r'\b\d+(?:\.\d+)?\b', formula))
        
        # Mathematical constants
        math_constants = ['π', 'e', 'i', '∞']
        constants.extend([c for c in math_constants if c in formula])
        
        return constants
    
    def _extract_operations(self, formula: str) -> List[str]:
        """Extract mathematical operations"""
        operations = []
        
        operation_symbols = ['+', '-', '*', '/', '^', '=', '<', '>', '≤', '≥', '≠', '≈']
        operations.extend([op for op in operation_symbols if op in formula])
        
        # Function operations
        functions = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt']
        operations.extend([f for f in functions if f in formula.lower()])
        
        return operations
    
    def _assess_formula_complexity(self, formula: str) -> int:
        """Assess formula complexity on scale 1-5"""
        complexity = 1
        
        # Length factor
        if len(formula) > 20:
            complexity += 1
        if len(formula) > 50:
            complexity += 1
        
        # Operation complexity
        complex_ops = ['∫', '∑', '∂', 'lim']
        complexity += sum(1 for op in complex_ops if op in formula)
        
        # Nested operations
        if '(' in formula and ')' in formula:
            nesting_level = 0
            max_nesting = 0
            for char in formula:
                if char == '(':
                    nesting_level += 1
                    max_nesting = max(max_nesting, nesting_level)
                elif char == ')':
                    nesting_level -= 1
            complexity += max_nesting
        
        return min(5, complexity)
    
    def _classify_subject_area(self, formula: str) -> str:
        """Classify the mathematical subject area"""
        
        if any(op in formula for op in ['∫', '∂', 'lim']):
            return "calculus"
        elif '∑' in formula or 'Σ' in formula:
            return "discrete_mathematics"
        elif any(func in formula.lower() for func in ['sin', 'cos', 'tan']):
            return "trigonometry"
        elif any(op in formula for op in ['log', 'ln', 'exp']):
            return "logarithms"
        elif '^' in formula and any(char.isdigit() for char in formula):
            return "algebra"
        elif any(symbol in formula for symbol in ['σ', 'μ', 'P(', 'E[']):
            return "statistics"
        else:
            return "general_mathematics"
    
    def _classify_educational_content(self, segments: List[ContentSegment]) -> Dict[str, List[Dict[str, Any]]]:
        """Classify educational content for optimal learning"""
        
        classified = {
            "prerequisites": [],
            "core_concepts": [],
            "examples": [],
            "exercises": [],
            "advanced_topics": [],
            "summaries": []
        }
        
        for segment in segments:
            classification = self._classify_segment_for_learning(segment)
            
            segment_info = {
                "id": segment.id,
                "content": segment.content[:200] + "..." if len(segment.content) > 200 else segment.content,
                "type": segment.type.value,
                "confidence": segment.confidence_score,
                "complexity": segment.metadata.get("complexity", 0.5)
            }
            
            classified[classification].append(segment_info)
        
        return classified
    
    def _classify_segment_for_learning(self, segment: ContentSegment) -> str:
        """Classify segment based on its educational role"""
        
        if segment.type == ContentSegmentType.DEFINITION:
            return "core_concepts"
        elif segment.type == ContentSegmentType.EXAMPLE:
            return "examples"
        elif segment.type == ContentSegmentType.EXERCISE:
            return "exercises"
        elif segment.type == ContentSegmentType.THEOREM:
            if segment.metadata.get("complexity", 0.5) > 0.7:
                return "advanced_topics"
            else:
                return "core_concepts"
        elif segment.type == ContentSegmentType.HEADING and segment.level <= 1:
            return "summaries"
        elif segment.metadata.get("complexity", 0.5) < 0.3:
            return "prerequisites"
        elif segment.metadata.get("complexity", 0.5) > 0.7:
            return "advanced_topics"
        else:
            return "core_concepts"
    
    def _generate_learning_objectives(self, segments: List[ContentSegment], formulas: List[FormulaAnalysis]) -> List[str]:
        """Generate learning objectives based on content analysis"""
        
        objectives = []
        
        # Objectives from definitions
        definitions = [s for s in segments if s.type == ContentSegmentType.DEFINITION]
        for defn in definitions[:5]:  # Top 5 definitions
            term = defn.metadata.get("defined_term", "concept")
            objectives.append(f"Comprendre et définir le concept de {term}")
        
        # Objectives from theorems
        theorems = [s for s in segments if s.type == ContentSegmentType.THEOREM]
        for theorem in theorems[:3]:  # Top 3 theorems
            objectives.append("Maîtriser un théorème fondamental et ses applications")
        
        # Objectives from formulas
        formula_areas = set(f.subject_area for f in formulas)
        for area in formula_areas:
            area_name = area.replace("_", " ").title()
            objectives.append(f"Appliquer les formules de {area_name}")
        
        # Objectives from exercises
        exercises = [s for s in segments if s.type == ContentSegmentType.EXERCISE]
        if exercises:
            objectives.append("Résoudre des exercices d'application pratique")
        
        return objectives
    
    def _build_concept_map(self, segments: List[ContentSegment]) -> Dict[str, List[str]]:
        """Build a concept map from the document content"""
        
        concept_map = {}
        
        # Extract key terms from definitions
        definitions = [s for s in segments if s.type == ContentSegmentType.DEFINITION]
        defined_terms = []
        
        for defn in definitions:
            term = defn.metadata.get("defined_term")
            if term:
                defined_terms.append(term.lower())
                
                # Find related concepts in the same segment
                related = self._extract_related_concepts(defn.content, defined_terms)
                concept_map[term.lower()] = related
        
        # Add formula relationships
        formulas = [s for s in segments if s.type == ContentSegmentType.FORMULA]
        for formula in formulas:
            variables = formula.metadata.get("variables", [])
            if variables:
                main_var = variables[0].lower()
                concept_map[main_var] = variables[1:] + [v.lower() for v in variables]
        
        return concept_map
    
    def _extract_related_concepts(self, text: str, known_concepts: List[str]) -> List[str]:
        """Extract concepts related to the main concept in text"""
        
        related = []
        text_lower = text.lower()
        
        # Find known concepts mentioned in this text
        for concept in known_concepts:
            if concept in text_lower:
                related.append(concept)
        
        # Extract capitalized terms (likely concepts)
        capitalized = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
        related.extend([term.lower() for term in capitalized[:3]])  # Top 3
        
        return list(set(related))
    
    def _generate_educational_insights(self, segments: List[ContentSegment], formulas: List[FormulaAnalysis]) -> Dict[str, Any]:
        """Generate insights for educational optimization"""
        
        insights = {
            "content_distribution": {},
            "difficulty_progression": [],
            "learning_recommendations": [],
            "estimated_study_time": 0
        }
        
        # Content distribution
        type_counts = {}
        for segment in segments:
            type_name = segment.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        insights["content_distribution"] = type_counts
        
        # Difficulty progression
        complexities = [(s.metadata.get("complexity", 0.5), s.id) for s in segments]
        complexities.sort()
        insights["difficulty_progression"] = [{"segment_id": sid, "complexity": comp} 
                                           for comp, sid in complexities]
        
        # Learning recommendations
        if type_counts.get("definition", 0) > type_counts.get("example", 0):
            insights["learning_recommendations"].append(
                "Document is definition-heavy; consider finding additional examples"
            )
        
        if len(formulas) > 10:
            insights["learning_recommendations"].append(
                "High mathematical content; allocate extra time for formula practice"
            )
        
        if type_counts.get("exercise", 0) == 0:
            insights["learning_recommendations"].append(
                "No exercises found; create practice problems for active learning"
            )
        
        # Estimate study time (rough heuristic)
        word_count = sum(len(s.content.split()) for s in segments)
        base_time = word_count // 200  # Assuming 200 words per minute reading
        
        # Add complexity multiplier
        avg_complexity = sum(s.metadata.get("complexity", 0.5) for s in segments) / len(segments)
        complexity_multiplier = 1 + avg_complexity
        
        # Add formula time
        formula_time = len(formulas) * 2  # 2 minutes per formula
        
        insights["estimated_study_time"] = int(base_time * complexity_multiplier + formula_time)
        
        return insights
    
    def _serialize_segment(self, segment: ContentSegment) -> Dict[str, Any]:
        """Convert segment to JSON-serializable format"""
        return {
            "id": segment.id,
            "type": segment.type.value,
            "content": segment.content,
            "start_position": segment.start_position,
            "end_position": segment.end_position,
            "confidence_score": segment.confidence_score,
            "level": segment.level,
            "metadata": segment.metadata,
            "latex_formula": segment.latex_formula,
            "formula_type": segment.formula_type,
            "image_description": segment.image_description
        }


# Add image support to existing extractors
def extract_text_from_image(path: str) -> str:
    """Extract text from image using OCR"""
    analyzer = AdvancedDocumentAnalyzer()
    return analyzer._extract_text_from_image(path)


# Update the extractors dictionary to include image formats
EXTRACTORS.update({
    ".jpg": extract_text_from_image,
    ".jpeg": extract_text_from_image,
    ".png": extract_text_from_image,
    ".bmp": extract_text_from_image,
    ".tiff": extract_text_from_image,
    ".tif": extract_text_from_image,
    ".gif": extract_text_from_image,
})

# Global instance for easy access
advanced_document_analyzer = AdvancedDocumentAnalyzer()