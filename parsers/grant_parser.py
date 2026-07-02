
"""
Comprehensive grant document parser with question extraction and attachment identification.
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
from dataclasses import dataclass, asdict

# Document processing imports
import PyPDF2
from docx import Document
import pdfplumber

logger = logging.getLogger(__name__)

@dataclass
class ExtractedQuestion:
    """Represents a question extracted from a grant document."""
    question_id: str
    question_text: str
    context: str
    attachment_type: str
    section_number: Optional[str] = None
    page_number: Optional[int] = None
    is_required: bool = True
    word_limit: Optional[int] = None
    format_requirements: Optional[str] = None

@dataclass
class AttachmentRequirement:
    """Represents an attachment requirement identified in the document."""
    attachment_id: str
    attachment_name: str
    attachment_type: str
    description: str
    is_required: bool = True
    format_requirements: Optional[str] = None
    questions: List[str] = None  # List of question IDs

    def __post_init__(self):
        if self.questions is None:
            self.questions = []

@dataclass
class DocumentAnalysis:
    """Complete analysis results from a grant document."""
    document_path: str
    document_type: str
    total_pages: int
    questions: List[ExtractedQuestion]
    attachments: List[AttachmentRequirement]
    sections: Dict[str, str]
    metadata: Dict[str, Any]

class GrantDocumentParser:
    """
    Comprehensive parser for grant documents that extracts questions,
    identifies attachments, and maps relationships between them.
    """
    
    def __init__(self):
        self.question_patterns = [
            # Common question patterns
            r'(?i)(?:question\s+)?(\d+)[\.\)]\s*(.+?)(?=\n\s*(?:question\s+)?\d+[\.\)]|\n\s*[A-Z][^a-z]*:|\Z)',
            r'(?i)([a-z][\.\)]\s*.+?)(?=\n\s*[a-z][\.\)]|\n\s*\d+[\.\)]|\Z)',
            r'(?i)(describe|explain|provide|list|identify|outline)\s+(.+?)(?=\n\s*(?:describe|explain|provide|list|identify|outline)|\n\s*\d+[\.\)]|\Z)',
        ]
        
        self.attachment_patterns = [
            r'(?i)attachment\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)appendix\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)exhibit\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)schedule\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)(budget|proposal|narrative|timeline|evaluation)(?:\s+(?:attachment|appendix|exhibit|schedule))?',
        ]
        
        self.word_limit_pattern = r'(?i)(?:maximum|max|limit|not\s+to\s+exceed)\s+(\d+)\s+words?'
        self.page_limit_pattern = r'(?i)(?:maximum|max|limit|not\s+to\s+exceed)\s+(\d+)\s+pages?'

    def parse_document(self, file_path: str) -> DocumentAnalysis:
        """
        Parse a grant document and extract all questions, attachments, and relationships.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            DocumentAnalysis object containing all extracted information
        """
        try:
            file_path = Path(file_path)
            
            # Extract text based on file type
            if file_path.suffix.lower() == '.pdf':
                text, total_pages = self._extract_pdf_text(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                text, total_pages = self._extract_docx_text(file_path)
            elif file_path.suffix.lower() in ['.txt', '.md']:
                text, total_pages = self._extract_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            # Perform comprehensive analysis
            questions = self._extract_questions(text)
            attachments = self._identify_attachments(text)
            sections = self._identify_sections(text)
            metadata = self._extract_metadata(text, file_path)
            
            # Map questions to attachments
            self._map_questions_to_attachments(questions, attachments, text)
            
            return DocumentAnalysis(
                document_path=str(file_path),
                document_type=self._classify_document_type(text, file_path),
                total_pages=total_pages,
                questions=questions,
                attachments=attachments,
                sections=sections,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {str(e)}")
            raise

    def _extract_pdf_text(self, file_path: Path) -> Tuple[str, int]:
        """Extract text from PDF using multiple methods for robustness."""
        text = ""
        total_pages = 0
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed for {file_path}, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e2:
                logger.error(f"Both PDF extraction methods failed for {file_path}: {e2}")
                raise
        
        return text, total_pages

    def _extract_docx_text(self, file_path: Path) -> Tuple[str, int]:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # Estimate pages (rough calculation)
            total_pages = max(1, len(text) // 3000)  # ~3000 chars per page
            
            return text, total_pages
        except Exception as e:
            logger.error(f"Error extracting DOCX text from {file_path}: {e}")
            raise

    def _extract_text_file(self, file_path: Path) -> Tuple[str, int]:
        """Extract text from plain text or markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # Estimate pages
            total_pages = max(1, len(text) // 3000)
            
            return text, total_pages
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise

    def _extract_questions(self, text: str) -> List[ExtractedQuestion]:
        """Extract questions from the document text."""
        questions = []
        question_id_counter = 1
        
        # Split text into lines for better processing
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Try each question pattern
            for pattern in self.question_patterns:
                matches = re.finditer(pattern, line, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    question_text = match.group(0).strip()
                    
                    # Skip if too short or doesn't look like a question
                    if len(question_text) < 10:
                        continue
                    
                    # Extract context (surrounding lines)
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    # Extract word/page limits
                    word_limit = self._extract_word_limit(question_text + context)
                    
                    # Determine attachment type
                    attachment_type = self._determine_attachment_type(question_text + context)
                    
                    question = ExtractedQuestion(
                        question_id=f"Q{question_id_counter:03d}",
                        question_text=question_text,
                        context=context,
                        attachment_type=attachment_type,
                        page_number=None,  # TODO: Calculate actual page number
                        word_limit=word_limit,
                        format_requirements=self._extract_format_requirements(context)
                    )
                    
                    questions.append(question)
                    question_id_counter += 1
        
        return questions

    def _identify_attachments(self, text: str) -> List[AttachmentRequirement]:
        """Identify required attachments from the document."""
        attachments = []
        attachment_id_counter = 1
        
        # Common attachment types to look for
        common_attachments = [
            ('budget', 'Budget', 'Financial information and cost breakdown'),
            ('proposal', 'Project Proposal', 'Main project narrative and description'),
            ('timeline', 'Project Timeline', 'Schedule and milestones'),
            ('evaluation', 'Evaluation Plan', 'Assessment and measurement strategy'),
            ('sustainability', 'Sustainability Plan', 'Long-term continuation strategy'),
            ('letters', 'Letters of Support', 'Endorsements and partnerships'),
            ('organizational', 'Organizational Information', 'Organization background and capacity'),
        ]
        
        # Search for explicit attachment mentions
        for pattern in self.attachment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                attachment_name = match.group(0).strip()
                description = self._extract_attachment_description(text, match.start(), match.end())
                
                attachment = AttachmentRequirement(
                    attachment_id=f"ATT{attachment_id_counter:03d}",
                    attachment_name=attachment_name,
                    attachment_type=self._classify_attachment_type(attachment_name),
                    description=description,
                    format_requirements=self._extract_format_requirements(description)
                )
                
                attachments.append(attachment)
                attachment_id_counter += 1
        
        # Add common attachments if mentioned in text
        for keyword, name, description in common_attachments:
            if re.search(rf'\b{keyword}\b', text, re.IGNORECASE):
                # Check if not already added
                if not any(keyword.lower() in att.attachment_name.lower() for att in attachments):
                    attachment = AttachmentRequirement(
                        attachment_id=f"ATT{attachment_id_counter:03d}",
                        attachment_name=name,
                        attachment_type=keyword,
                        description=description
                    )
                    attachments.append(attachment)
                    attachment_id_counter += 1
        
        return attachments

    def _identify_sections(self, text: str) -> Dict[str, str]:
        """Identify major sections in the document."""
        sections = {}
        
        # Common section patterns
        section_patterns = [
            r'(?i)^([IVX]+\.?\s+.+?)$',  # Roman numerals
            r'(?i)^(\d+\.?\s+.+?)$',     # Numbers
            r'(?i)^([A-Z][^a-z]*:)$',    # All caps with colon
        ]
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            is_section_header = False
            for pattern in section_patterns:
                if re.match(pattern, line):
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = line
                    current_content = []
                    is_section_header = True
                    break
            
            if not is_section_header and current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections

    def _extract_metadata(self, text: str, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from the document."""
        metadata = {
            'filename': file_path.name,
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'word_count': len(text.split()),
            'character_count': len(text),
        }
        
        # Extract dates
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        dates = re.findall(date_pattern, text)
        if dates:
            metadata['dates_found'] = dates
        
        # Extract dollar amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        amounts = re.findall(money_pattern, text)
        if amounts:
            metadata['dollar_amounts'] = amounts
        
        return metadata

    def _map_questions_to_attachments(self, questions: List[ExtractedQuestion], 
                                    attachments: List[AttachmentRequirement], 
                                    text: str) -> None:
        """Map questions to their appropriate attachments."""
        for question in questions:
            # Find the best matching attachment
            best_match = None
            best_score = 0
            
            for attachment in attachments:
                score = self._calculate_mapping_score(question, attachment, text)
                if score > best_score:
                    best_score = score
                    best_match = attachment
            
            if best_match and best_score > 0.3:  # Threshold for mapping
                best_match.questions.append(question.question_id)
                question.attachment_type = best_match.attachment_type

    def _calculate_mapping_score(self, question: ExtractedQuestion, 
                               attachment: AttachmentRequirement, text: str) -> float:
        """Calculate how well a question matches an attachment."""
        score = 0.0
        
        # Check for keyword overlap
        question_words = set(question.question_text.lower().split())
        attachment_words = set(attachment.attachment_name.lower().split())
        
        overlap = len(question_words.intersection(attachment_words))
        if overlap > 0:
            score += overlap * 0.3
        
        # Check context proximity in original text
        question_pos = text.lower().find(question.question_text.lower()[:50])
        attachment_pos = text.lower().find(attachment.attachment_name.lower())
        
        if question_pos != -1 and attachment_pos != -1:
            distance = abs(question_pos - attachment_pos)
            if distance < 1000:  # Within 1000 characters
                score += (1000 - distance) / 1000 * 0.4
        
        return min(score, 1.0)

    def _extract_word_limit(self, text: str) -> Optional[int]:
        """Extract word limit from text."""
        match = re.search(self.word_limit_pattern, text)
        if match:
            return int(match.group(1))
        return None

    def _extract_format_requirements(self, text: str) -> Optional[str]:
        """Extract format requirements from text."""
        format_indicators = [
            'single-spaced', 'double-spaced', 'times new roman', 'arial',
            '12-point', '11-point', 'font', 'margin', 'header', 'footer'
        ]
        
        requirements = []
        for indicator in format_indicators:
            if indicator in text.lower():
                # Extract the sentence containing the format requirement
                sentences = text.split('.')
                for sentence in sentences:
                    if indicator in sentence.lower():
                        requirements.append(sentence.strip())
                        break
        
        return '; '.join(requirements) if requirements else None

    def _determine_attachment_type(self, text: str) -> str:
        """Determine the attachment type based on question content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['budget', 'cost', 'financial', 'funding']):
            return 'budget'
        elif any(word in text_lower for word in ['timeline', 'schedule', 'milestone']):
            return 'timeline'
        elif any(word in text_lower for word in ['evaluation', 'assess', 'measure', 'outcome']):
            return 'evaluation'
        elif any(word in text_lower for word in ['letter', 'support', 'endorsement']):
            return 'letters'
        elif any(word in text_lower for word in ['organization', 'staff', 'capacity', 'experience']):
            return 'organizational'
        else:
            return 'proposal'

    def _classify_document_type(self, text: str, file_path: Path) -> str:
        """Classify the type of grant document."""
        text_lower = text.lower()
        filename_lower = file_path.name.lower()
        
        if any(term in text_lower or term in filename_lower for term in ['rfp', 'request for proposal']):
            return 'RFP'
        elif any(term in text_lower or term in filename_lower for term in ['application', 'guidelines']):
            return 'Application Guidelines'
        elif any(term in text_lower or term in filename_lower for term in ['outline', 'template']):
            return 'Application Outline'
        else:
            return 'Grant Document'

    def _classify_attachment_type(self, attachment_name: str) -> str:
        """Classify the type of attachment."""
        name_lower = attachment_name.lower()
        
        if 'budget' in name_lower:
            return 'budget'
        elif any(word in name_lower for word in ['proposal', 'narrative', 'description']):
            return 'proposal'
        elif any(word in name_lower for word in ['timeline', 'schedule']):
            return 'timeline'
        elif any(word in name_lower for word in ['evaluation', 'assessment']):
            return 'evaluation'
        elif any(word in name_lower for word in ['letter', 'support']):
            return 'letters'
        elif any(word in name_lower for word in ['organization', 'capacity']):
            return 'organizational'
        else:
            return 'other'

    def _extract_attachment_description(self, text: str, start_pos: int, end_pos: int) -> str:
        """Extract description for an attachment from surrounding context."""
        # Get context around the attachment mention
        context_start = max(0, start_pos - 200)
        context_end = min(len(text), end_pos + 200)
        context = text[context_start:context_end]
        
        # Find the most relevant sentence
        sentences = context.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 20:  # Meaningful sentence
                return sentence.strip()
        
        return "Attachment requirement identified in grant document"

    def to_dict(self, analysis: DocumentAnalysis) -> Dict[str, Any]:
        """Convert DocumentAnalysis to dictionary for JSON serialization."""
        return {
            'document_path': analysis.document_path,
            'document_type': analysis.document_type,
            'total_pages': analysis.total_pages,
            'questions': [asdict(q) for q in analysis.questions],
            'attachments': [asdict(a) for a in analysis.attachments],
            'sections': analysis.sections,
            'metadata': analysis.metadata
        }
