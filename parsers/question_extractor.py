
"""
Advanced question extraction engine with context preservation and relationship mapping.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class QuestionContext:
    """Context information for an extracted question."""
    preceding_text: str
    following_text: str
    section_header: Optional[str] = None
    subsection: Optional[str] = None

class QuestionExtractor:
    """
    Advanced question extraction engine that identifies questions,
    preserves context, and maintains relationships.
    """
    
    def __init__(self):
        # Enhanced question patterns with more sophisticated matching
        self.question_patterns = [
            # Numbered questions (1., 2., etc.)
            r'(?i)(?:^|\n)\s*(\d+)[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\n\s*[A-Z][^a-z]*:|\Z)',
            
            # Lettered questions (a., b., etc.)
            r'(?i)(?:^|\n)\s*([a-z])[\.\)]\s*(.+?)(?=\n\s*[a-z][\.\)]|\n\s*\d+[\.\)]|\Z)',
            
            # Roman numeral questions
            r'(?i)(?:^|\n)\s*([ivx]+)[\.\)]\s*(.+?)(?=\n\s*[ivx]+[\.\)]|\n\s*\d+[\.\)]|\Z)',
            
            # Question words at start of line
            r'(?i)(?:^|\n)\s*((?:describe|explain|provide|list|identify|outline|discuss|analyze|evaluate|compare|contrast|define|summarize|detail|specify|indicate|state|name|give|show|demonstrate|illustrate|justify|argue|assess|review|examine|consider|address|respond|answer)\s+.+?)(?=\n\s*(?:describe|explain|provide|list|identify|outline|discuss|analyze|evaluate|compare|contrast|define|summarize|detail|specify|indicate|state|name|give|show|demonstrate|illustrate|justify|argue|assess|review|examine|consider|address|respond|answer)|\n\s*\d+[\.\)]|\n\s*[A-Z][^a-z]*:|\Z)',
            
            # Questions ending with question marks
            r'(?i)(.+?\?)\s*(?=\n|$)',
            
            # Instruction-style questions
            r'(?i)(?:^|\n)\s*(please\s+.+?)(?=\n\s*please|\n\s*\d+[\.\)]|\n\s*[A-Z][^a-z]*:|\Z)',
        ]
        
        # Patterns to identify section headers
        self.section_patterns = [
            r'(?i)^([IVX]+\.?\s+.+?)$',  # Roman numerals
            r'(?i)^(\d+\.?\s+.+?)$',     # Numbers
            r'(?i)^([A-Z][^a-z]*:?)$',   # All caps
            r'(?i)^(SECTION\s+[A-Z0-9]+.*)$',  # Section headers
            r'(?i)^(PART\s+[A-Z0-9]+.*)$',     # Part headers
        ]
        
        # Patterns for requirements and constraints
        self.requirement_patterns = [
            r'(?i)(maximum|max|limit|not\s+to\s+exceed)\s+(\d+)\s+(words?|pages?|characters?)',
            r'(?i)(minimum|min|at\s+least)\s+(\d+)\s+(words?|pages?|characters?)',
            r'(?i)(single|double)[\s-]spaced?',
            r'(?i)(\d+)[\s-]point\s+font',
            r'(?i)(times\s+new\s+roman|arial|calibri|helvetica)',
            r'(?i)(\d+(?:\.\d+)?)\s*inch\s+margins?',
        ]

    def extract_questions_with_context(self, text: str) -> List[Dict]:
        """
        Extract questions with full context preservation.
        
        Args:
            text: Document text to analyze
            
        Returns:
            List of dictionaries containing question data and context
        """
        questions = []
        lines = text.split('\n')
        
        # First pass: identify section structure
        sections = self._identify_section_structure(lines)
        
        # Second pass: extract questions with context
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Try each question pattern
            for pattern_idx, pattern in enumerate(self.question_patterns):
                matches = list(re.finditer(pattern, line, re.MULTILINE | re.DOTALL))
                
                for match in matches:
                    question_data = self._process_question_match(
                        match, line, lines, i, sections, pattern_idx
                    )
                    
                    if question_data and self._is_valid_question(question_data):
                        questions.append(question_data)
        
        # Post-process to remove duplicates and improve quality
        questions = self._deduplicate_questions(questions)
        questions = self._enhance_question_context(questions, text)
        
        return questions

    def _identify_section_structure(self, lines: List[str]) -> Dict[int, Dict]:
        """Identify the hierarchical structure of sections in the document."""
        sections = {}
        current_section = None
        current_subsection = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            for pattern in self.section_patterns:
                if re.match(pattern, line):
                    # Determine hierarchy level
                    if re.match(r'(?i)^([IVX]+\.?\s+.+?)$', line):
                        # Major section (Roman numerals)
                        current_section = line
                        current_subsection = None
                        sections[i] = {
                            'type': 'major_section',
                            'title': line,
                            'level': 1
                        }
                    elif re.match(r'(?i)^(\d+\.?\s+.+?)$', line):
                        # Subsection (numbers)
                        current_subsection = line
                        sections[i] = {
                            'type': 'subsection',
                            'title': line,
                            'level': 2,
                            'parent': current_section
                        }
                    else:
                        # Other section types
                        sections[i] = {
                            'type': 'section',
                            'title': line,
                            'level': 1
                        }
                    break
        
        return sections

    def _process_question_match(self, match, line: str, lines: List[str], 
                              line_idx: int, sections: Dict, pattern_idx: int) -> Optional[Dict]:
        """Process a regex match to extract question information."""
        try:
            question_text = match.group(0).strip()
            
            # Skip if too short or doesn't look like a question
            if len(question_text) < 10:
                return None
            
            # Find current section context
            current_section = self._find_current_section(line_idx, sections)
            
            # Extract context around the question
            context = self._extract_question_context(lines, line_idx)
            
            # Extract requirements and constraints
            requirements = self._extract_requirements(question_text + ' ' + context.preceding_text + ' ' + context.following_text)
            
            # Determine question type and attachment
            question_type = self._classify_question_type(question_text)
            attachment_type = self._determine_attachment_type(question_text, context)
            
            return {
                'question_text': question_text,
                'context': {
                    'preceding_text': context.preceding_text,
                    'following_text': context.following_text,
                    'section_header': context.section_header,
                    'subsection': context.subsection
                },
                'requirements': requirements,
                'question_type': question_type,
                'attachment_type': attachment_type,
                'line_number': line_idx + 1,
                'pattern_used': pattern_idx,
                'confidence_score': self._calculate_confidence_score(question_text, context, pattern_idx)
            }
            
        except Exception as e:
            logger.warning(f"Error processing question match: {e}")
            return None

    def _extract_question_context(self, lines: List[str], line_idx: int) -> QuestionContext:
        """Extract context around a question."""
        # Get preceding context (up to 3 lines before)
        start_idx = max(0, line_idx - 3)
        preceding_lines = lines[start_idx:line_idx]
        preceding_text = '\n'.join(line.strip() for line in preceding_lines if line.strip())
        
        # Get following context (up to 3 lines after)
        end_idx = min(len(lines), line_idx + 4)
        following_lines = lines[line_idx + 1:end_idx]
        following_text = '\n'.join(line.strip() for line in following_lines if line.strip())
        
        # Find section headers in preceding context
        section_header = None
        subsection = None
        
        for i in range(line_idx - 1, max(0, line_idx - 20), -1):
            line = lines[i].strip()
            if not line:
                continue
                
            for pattern in self.section_patterns:
                if re.match(pattern, line):
                    if not subsection and re.match(r'(?i)^(\d+\.?\s+.+?)$', line):
                        subsection = line
                    elif not section_header:
                        section_header = line
                        break
            
            if section_header and subsection:
                break
        
        return QuestionContext(
            preceding_text=preceding_text,
            following_text=following_text,
            section_header=section_header,
            subsection=subsection
        )

    def _find_current_section(self, line_idx: int, sections: Dict) -> Optional[Dict]:
        """Find the current section for a given line."""
        current_section = None
        
        for section_line_idx in sorted(sections.keys(), reverse=True):
            if section_line_idx <= line_idx:
                current_section = sections[section_line_idx]
                break
        
        return current_section

    def _extract_requirements(self, text: str) -> Dict[str, any]:
        """Extract requirements and constraints from text."""
        requirements = {}
        
        for pattern in self.requirement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                full_match = match.group(0).lower()
                
                if 'word' in full_match:
                    if 'maximum' in full_match or 'max' in full_match or 'limit' in full_match:
                        requirements['max_words'] = int(re.search(r'\d+', full_match).group())
                    elif 'minimum' in full_match or 'min' in full_match:
                        requirements['min_words'] = int(re.search(r'\d+', full_match).group())
                
                elif 'page' in full_match:
                    if 'maximum' in full_match or 'max' in full_match or 'limit' in full_match:
                        requirements['max_pages'] = int(re.search(r'\d+', full_match).group())
                    elif 'minimum' in full_match or 'min' in full_match:
                        requirements['min_pages'] = int(re.search(r'\d+', full_match).group())
                
                elif 'spaced' in full_match:
                    if 'single' in full_match:
                        requirements['spacing'] = 'single'
                    elif 'double' in full_match:
                        requirements['spacing'] = 'double'
                
                elif 'font' in full_match:
                    font_size = re.search(r'\d+', full_match)
                    if font_size:
                        requirements['font_size'] = int(font_size.group())
                
                elif any(font in full_match for font in ['times', 'arial', 'calibri', 'helvetica']):
                    requirements['font_family'] = match.group(0)
                
                elif 'margin' in full_match:
                    margin_size = re.search(r'\d+(?:\.\d+)?', full_match)
                    if margin_size:
                        requirements['margins'] = float(margin_size.group())
        
        return requirements

    def _classify_question_type(self, question_text: str) -> str:
        """Classify the type of question based on content."""
        text_lower = question_text.lower()
        
        if any(word in text_lower for word in ['describe', 'explain', 'discuss', 'detail']):
            return 'descriptive'
        elif any(word in text_lower for word in ['list', 'identify', 'name', 'specify']):
            return 'listing'
        elif any(word in text_lower for word in ['analyze', 'evaluate', 'assess', 'compare']):
            return 'analytical'
        elif any(word in text_lower for word in ['provide', 'submit', 'attach', 'include']):
            return 'submission'
        elif '?' in question_text:
            return 'interrogative'
        else:
            return 'instructional'

    def _determine_attachment_type(self, question_text: str, context: QuestionContext) -> str:
        """Determine which attachment this question belongs to."""
        combined_text = (question_text + ' ' + context.preceding_text + ' ' + 
                        context.following_text + ' ' + (context.section_header or '') + 
                        ' ' + (context.subsection or '')).lower()
        
        if any(word in combined_text for word in ['budget', 'cost', 'financial', 'funding', 'expense']):
            return 'budget'
        elif any(word in combined_text for word in ['timeline', 'schedule', 'milestone', 'calendar']):
            return 'timeline'
        elif any(word in combined_text for word in ['evaluation', 'assess', 'measure', 'outcome', 'impact']):
            return 'evaluation'
        elif any(word in combined_text for word in ['letter', 'support', 'endorsement', 'recommendation']):
            return 'letters'
        elif any(word in combined_text for word in ['organization', 'staff', 'capacity', 'experience', 'qualification']):
            return 'organizational'
        elif any(word in combined_text for word in ['sustainability', 'continuation', 'long-term']):
            return 'sustainability'
        else:
            return 'proposal'

    def _calculate_confidence_score(self, question_text: str, context: QuestionContext, pattern_idx: int) -> float:
        """Calculate confidence score for question extraction."""
        score = 0.5  # Base score
        
        # Pattern-based scoring
        if pattern_idx in [0, 1, 2]:  # Numbered/lettered patterns
            score += 0.3
        elif pattern_idx == 4:  # Question mark patterns
            score += 0.2
        
        # Length-based scoring
        if 20 <= len(question_text) <= 500:
            score += 0.1
        elif len(question_text) > 500:
            score -= 0.1
        
        # Context quality scoring
        if context.section_header:
            score += 0.1
        if context.subsection:
            score += 0.05
        
        # Question word scoring
        question_words = ['describe', 'explain', 'provide', 'list', 'identify', 'outline']
        if any(word in question_text.lower() for word in question_words):
            score += 0.1
        
        return min(score, 1.0)

    def _is_valid_question(self, question_data: Dict) -> bool:
        """Validate if extracted text is actually a question."""
        question_text = question_data['question_text']
        
        # Minimum length check
        if len(question_text) < 10:
            return False
        
        # Maximum length check (avoid extracting entire paragraphs)
        if len(question_text) > 1000:
            return False
        
        # Check for question indicators
        has_question_word = any(word in question_text.lower() for word in [
            'describe', 'explain', 'provide', 'list', 'identify', 'outline',
            'discuss', 'analyze', 'evaluate', 'what', 'how', 'why', 'when', 'where'
        ])
        
        has_question_mark = '?' in question_text
        has_instruction = any(word in question_text.lower() for word in [
            'please', 'submit', 'attach', 'include', 'complete'
        ])
        
        # Must have at least one question indicator
        if not (has_question_word or has_question_mark or has_instruction):
            return False
        
        # Confidence score check
        if question_data.get('confidence_score', 0) < 0.3:
            return False
        
        return True

    def _deduplicate_questions(self, questions: List[Dict]) -> List[Dict]:
        """Remove duplicate questions based on text similarity."""
        unique_questions = []
        
        for question in questions:
            is_duplicate = False
            question_text = question['question_text'].lower().strip()
            
            for existing in unique_questions:
                existing_text = existing['question_text'].lower().strip()
                
                # Check for exact match
                if question_text == existing_text:
                    is_duplicate = True
                    break
                
                # Check for substantial overlap (>80% similarity)
                similarity = self._calculate_text_similarity(question_text, existing_text)
                if similarity > 0.8:
                    # Keep the one with higher confidence
                    if question.get('confidence_score', 0) > existing.get('confidence_score', 0):
                        unique_questions.remove(existing)
                    else:
                        is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_questions.append(question)
        
        return unique_questions

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def _enhance_question_context(self, questions: List[Dict], full_text: str) -> List[Dict]:
        """Enhance question context with additional information."""
        for question in questions:
            # Add position information
            question_pos = full_text.find(question['question_text'])
            if question_pos != -1:
                question['position_in_document'] = question_pos / len(full_text)
            
            # Add word count
            question['word_count'] = len(question['question_text'].split())
            
            # Add complexity score
            question['complexity_score'] = self._calculate_complexity_score(question['question_text'])
        
        return questions

    def _calculate_complexity_score(self, question_text: str) -> float:
        """Calculate complexity score for a question."""
        score = 0.0
        
        # Length factor
        word_count = len(question_text.split())
        if word_count > 50:
            score += 0.3
        elif word_count > 20:
            score += 0.2
        else:
            score += 0.1
        
        # Complex words factor
        complex_words = ['analyze', 'evaluate', 'synthesize', 'compare', 'contrast', 'justify']
        if any(word in question_text.lower() for word in complex_words):
            score += 0.3
        
        # Multiple parts factor
        if any(connector in question_text.lower() for connector in ['and', 'or', 'including', 'such as']):
            score += 0.2
        
        # Question depth factor
        if any(phrase in question_text.lower() for phrase in ['in detail', 'comprehensive', 'thorough']):
            score += 0.2
        
        return min(score, 1.0)
