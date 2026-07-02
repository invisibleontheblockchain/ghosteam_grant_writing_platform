
"""
Attachment identification and mapping system for grant documents.
"""

import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class AttachmentMapping:
    """Represents the mapping between questions and attachments."""
    attachment_id: str
    attachment_name: str
    attachment_type: str
    questions: List[str]
    confidence_score: float
    context_clues: List[str]

class AttachmentMapper:
    """
    System for identifying required attachments and mapping questions to them.
    """
    
    def __init__(self):
        # Comprehensive attachment type definitions
        self.attachment_types = {
            'proposal': {
                'keywords': ['proposal', 'narrative', 'description', 'project', 'program', 'initiative'],
                'patterns': [
                    r'(?i)project\s+(?:narrative|description|proposal)',
                    r'(?i)program\s+(?:narrative|description|proposal)',
                    r'(?i)(?:main|primary)\s+proposal',
                ],
                'common_names': ['Project Proposal', 'Program Narrative', 'Project Description']
            },
            'budget': {
                'keywords': ['budget', 'cost', 'financial', 'funding', 'expense', 'revenue'],
                'patterns': [
                    r'(?i)(?:project|program)?\s*budget',
                    r'(?i)cost\s+(?:breakdown|analysis|summary)',
                    r'(?i)financial\s+(?:plan|information|details)',
                ],
                'common_names': ['Project Budget', 'Budget Narrative', 'Cost Analysis']
            },
            'timeline': {
                'keywords': ['timeline', 'schedule', 'milestone', 'calendar', 'phases'],
                'patterns': [
                    r'(?i)project\s+timeline',
                    r'(?i)implementation\s+schedule',
                    r'(?i)work\s+plan',
                ],
                'common_names': ['Project Timeline', 'Implementation Schedule', 'Work Plan']
            },
            'evaluation': {
                'keywords': ['evaluation', 'assessment', 'measurement', 'outcome', 'impact', 'metrics'],
                'patterns': [
                    r'(?i)evaluation\s+plan',
                    r'(?i)assessment\s+(?:plan|strategy)',
                    r'(?i)outcome\s+measurement',
                ],
                'common_names': ['Evaluation Plan', 'Assessment Strategy', 'Outcome Measurement']
            },
            'organizational': {
                'keywords': ['organization', 'staff', 'capacity', 'experience', 'qualification', 'resume'],
                'patterns': [
                    r'(?i)organizational\s+(?:capacity|information|chart)',
                    r'(?i)staff\s+(?:qualifications|resumes|information)',
                    r'(?i)key\s+personnel',
                ],
                'common_names': ['Organizational Capacity', 'Staff Qualifications', 'Key Personnel']
            },
            'letters': {
                'keywords': ['letter', 'support', 'endorsement', 'recommendation', 'commitment'],
                'patterns': [
                    r'(?i)letters?\s+of\s+support',
                    r'(?i)letters?\s+of\s+(?:commitment|endorsement)',
                    r'(?i)support\s+letters?',
                ],
                'common_names': ['Letters of Support', 'Letters of Commitment', 'Endorsement Letters']
            },
            'sustainability': {
                'keywords': ['sustainability', 'continuation', 'long-term', 'future', 'ongoing'],
                'patterns': [
                    r'(?i)sustainability\s+plan',
                    r'(?i)continuation\s+(?:plan|strategy)',
                    r'(?i)long[- ]?term\s+(?:plan|strategy)',
                ],
                'common_names': ['Sustainability Plan', 'Continuation Strategy', 'Long-term Plan']
            },
            'appendix': {
                'keywords': ['appendix', 'appendices', 'additional', 'supplemental', 'supporting'],
                'patterns': [
                    r'(?i)appendix\s+[a-z0-9]+',
                    r'(?i)additional\s+(?:materials|documents|information)',
                    r'(?i)supplemental\s+(?:materials|documents|information)',
                ],
                'common_names': ['Appendix', 'Additional Materials', 'Supplemental Documents']
            }
        }
        
        # Patterns for explicit attachment mentions
        self.explicit_patterns = [
            r'(?i)attachment\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)appendix\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)exhibit\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)schedule\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
            r'(?i)section\s+([a-z0-9]+)[\:\-\s]*(.+?)(?=\n|$)',
        ]
        
        # Question-to-attachment mapping indicators
        self.mapping_indicators = {
            'direct_reference': [
                r'(?i)(?:in|on|within)\s+(?:attachment|appendix|exhibit|schedule)\s+([a-z0-9]+)',
                r'(?i)(?:see|refer\s+to|complete)\s+(?:attachment|appendix|exhibit|schedule)\s+([a-z0-9]+)',
            ],
            'contextual_clues': [
                r'(?i)(?:budget|financial)\s+(?:information|details|breakdown)',
                r'(?i)(?:timeline|schedule|milestones)',
                r'(?i)(?:evaluation|assessment|measurement)',
                r'(?i)(?:organizational|staff|personnel)',
                r'(?i)(?:letters?\s+of\s+support|endorsements?)',
            ]
        }

    def identify_attachments(self, text: str, questions: List[Dict]) -> List[AttachmentMapping]:
        """
        Identify all required attachments from the document text and questions.
        
        Args:
            text: Full document text
            questions: List of extracted questions
            
        Returns:
            List of AttachmentMapping objects
        """
        attachments = []
        
        # Step 1: Find explicitly mentioned attachments
        explicit_attachments = self._find_explicit_attachments(text)
        
        # Step 2: Identify implicit attachments based on content
        implicit_attachments = self._find_implicit_attachments(text, questions)
        
        # Step 3: Merge and deduplicate
        all_attachments = self._merge_attachments(explicit_attachments, implicit_attachments)
        
        # Step 4: Map questions to attachments
        for attachment in all_attachments:
            self._map_questions_to_attachment(attachment, questions, text)
        
        # Step 5: Validate and score attachments
        validated_attachments = self._validate_attachments(all_attachments, questions)
        
        return validated_attachments

    def _find_explicit_attachments(self, text: str) -> List[AttachmentMapping]:
        """Find attachments explicitly mentioned in the document."""
        attachments = []
        attachment_counter = 1
        
        for pattern in self.explicit_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            
            for match in matches:
                attachment_id = match.group(1) if len(match.groups()) > 0 else f"EXP{attachment_counter:03d}"
                attachment_name = match.group(0).strip()
                
                # Extract description if available
                description = ""
                if len(match.groups()) > 1:
                    description = match.group(2).strip()
                
                # Classify attachment type
                attachment_type = self._classify_attachment_by_text(attachment_name + " " + description)
                
                # Get context around the mention
                context_clues = self._extract_context_clues(text, match.start(), match.end())
                
                attachment = AttachmentMapping(
                    attachment_id=attachment_id,
                    attachment_name=attachment_name,
                    attachment_type=attachment_type,
                    questions=[],
                    confidence_score=0.8,  # High confidence for explicit mentions
                    context_clues=context_clues
                )
                
                attachments.append(attachment)
                attachment_counter += 1
        
        return attachments

    def _find_implicit_attachments(self, text: str, questions: List[Dict]) -> List[AttachmentMapping]:
        """Find attachments implied by content and questions."""
        attachments = []
        attachment_counter = 1
        
        # Analyze text for attachment type indicators
        for attachment_type, type_info in self.attachment_types.items():
            # Check for patterns
            found_patterns = []
            for pattern in type_info['patterns']:
                matches = list(re.finditer(pattern, text, re.MULTILINE))
                found_patterns.extend([match.group(0) for match in matches])
            
            # Check for keywords in context
            keyword_contexts = []
            for keyword in type_info['keywords']:
                if re.search(rf'\b{keyword}\b', text, re.IGNORECASE):
                    keyword_contexts.append(keyword)
            
            # If we found evidence of this attachment type
            if found_patterns or len(keyword_contexts) >= 2:
                # Choose the best name
                attachment_name = self._choose_best_name(type_info['common_names'], found_patterns)
                
                attachment = AttachmentMapping(
                    attachment_id=f"IMP{attachment_counter:03d}",
                    attachment_name=attachment_name,
                    attachment_type=attachment_type,
                    questions=[],
                    confidence_score=0.6 + (len(found_patterns) * 0.1) + (len(keyword_contexts) * 0.05),
                    context_clues=found_patterns + keyword_contexts
                )
                
                attachments.append(attachment)
                attachment_counter += 1
        
        return attachments

    def _merge_attachments(self, explicit: List[AttachmentMapping], 
                          implicit: List[AttachmentMapping]) -> List[AttachmentMapping]:
        """Merge explicit and implicit attachments, removing duplicates."""
        merged = explicit.copy()
        
        for implicit_att in implicit:
            # Check if this implicit attachment matches any explicit one
            is_duplicate = False
            
            for explicit_att in explicit:
                if self._are_attachments_similar(implicit_att, explicit_att):
                    # Merge information
                    explicit_att.context_clues.extend(implicit_att.context_clues)
                    explicit_att.confidence_score = max(explicit_att.confidence_score, 
                                                      implicit_att.confidence_score)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.append(implicit_att)
        
        return merged

    def _map_questions_to_attachment(self, attachment: AttachmentMapping, 
                                   questions: List[Dict], text: str) -> None:
        """Map questions to a specific attachment."""
        for question in questions:
            mapping_score = self._calculate_question_attachment_score(
                question, attachment, text
            )
            
            if mapping_score > 0.4:  # Threshold for mapping
                attachment.questions.append(question.get('question_id', ''))

    def _calculate_question_attachment_score(self, question: Dict, 
                                           attachment: AttachmentMapping, text: str) -> float:
        """Calculate how well a question maps to an attachment."""
        score = 0.0
        
        question_text = question.get('question_text', '').lower()
        attachment_name = attachment.attachment_name.lower()
        attachment_type = attachment.attachment_type.lower()
        
        # Direct reference check
        for pattern in self.mapping_indicators['direct_reference']:
            if re.search(pattern, question_text):
                match = re.search(pattern, question_text)
                if match and match.group(1).lower() in attachment_name.lower():
                    score += 0.8
                    break
        
        # Keyword overlap
        question_words = set(question_text.split())
        attachment_words = set(attachment_name.split())
        type_keywords = set(self.attachment_types.get(attachment_type, {}).get('keywords', []))
        
        # Check overlap with attachment name
        name_overlap = len(question_words.intersection(attachment_words))
        if name_overlap > 0:
            score += name_overlap * 0.2
        
        # Check overlap with type keywords
        keyword_overlap = len(question_words.intersection(type_keywords))
        if keyword_overlap > 0:
            score += keyword_overlap * 0.3
        
        # Context proximity in original text
        question_pos = text.lower().find(question_text[:50])
        attachment_mentions = []
        
        for clue in attachment.context_clues:
            pos = text.lower().find(clue.lower())
            if pos != -1:
                attachment_mentions.append(pos)
        
        if question_pos != -1 and attachment_mentions:
            min_distance = min(abs(question_pos - pos) for pos in attachment_mentions)
            if min_distance < 1000:  # Within 1000 characters
                score += (1000 - min_distance) / 1000 * 0.3
        
        # Question type alignment
        question_type = question.get('attachment_type', '')
        if question_type == attachment_type:
            score += 0.4
        
        return min(score, 1.0)

    def _classify_attachment_by_text(self, text: str) -> str:
        """Classify attachment type based on text content."""
        text_lower = text.lower()
        
        # Score each attachment type
        type_scores = {}
        
        for attachment_type, type_info in self.attachment_types.items():
            score = 0
            
            # Check keywords
            for keyword in type_info['keywords']:
                if keyword in text_lower:
                    score += 1
            
            # Check patterns
            for pattern in type_info['patterns']:
                if re.search(pattern, text_lower):
                    score += 2
            
            type_scores[attachment_type] = score
        
        # Return the type with the highest score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        else:
            return 'other'

    def _choose_best_name(self, common_names: List[str], found_patterns: List[str]) -> str:
        """Choose the best name for an attachment based on found patterns."""
        if found_patterns:
            # Use the first found pattern as it's likely most specific
            return found_patterns[0].title()
        elif common_names:
            # Use the first common name
            return common_names[0]
        else:
            return "Required Attachment"

    def _are_attachments_similar(self, att1: AttachmentMapping, att2: AttachmentMapping) -> bool:
        """Check if two attachments are similar enough to be considered duplicates."""
        # Same type
        if att1.attachment_type == att2.attachment_type:
            return True
        
        # Similar names
        name1_words = set(att1.attachment_name.lower().split())
        name2_words = set(att2.attachment_name.lower().split())
        
        if len(name1_words.intersection(name2_words)) >= 2:
            return True
        
        return False

    def _extract_context_clues(self, text: str, start_pos: int, end_pos: int) -> List[str]:
        """Extract context clues around an attachment mention."""
        # Get context around the mention
        context_start = max(0, start_pos - 200)
        context_end = min(len(text), end_pos + 200)
        context = text[context_start:context_end]
        
        clues = []
        
        # Look for requirement indicators
        requirement_patterns = [
            r'(?i)(required|mandatory|must\s+(?:include|provide|submit))',
            r'(?i)(optional|recommended|suggested)',
            r'(?i)(\d+\s+pages?|\d+\s+words?)',
            r'(?i)(single|double)[\s-]spaced?',
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, context)
            clues.extend(matches)
        
        return clues

    def _validate_attachments(self, attachments: List[AttachmentMapping], 
                            questions: List[Dict]) -> List[AttachmentMapping]:
        """Validate and filter attachments based on quality criteria."""
        validated = []
        
        for attachment in attachments:
            # Must have reasonable confidence score
            if attachment.confidence_score < 0.3:
                continue
            
            # Must have at least one question mapped (or be explicitly mentioned)
            if not attachment.questions and attachment.confidence_score < 0.7:
                continue
            
            # Must have meaningful context clues
            if not attachment.context_clues:
                continue
            
            validated.append(attachment)
        
        # Sort by confidence score
        validated.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return validated

    def create_attachment_structure(self, attachments: List[AttachmentMapping], 
                                  questions: List[Dict]) -> Dict[str, Dict]:
        """Create a structured representation of attachments and their questions."""
        structure = {}
        
        for attachment in attachments:
            # Get questions for this attachment
            attachment_questions = []
            for question in questions:
                question_id = question.get('question_id', '')
                if question_id in attachment.questions:
                    attachment_questions.append(question)
            
            structure[attachment.attachment_id] = {
                'name': attachment.attachment_name,
                'type': attachment.attachment_type,
                'confidence_score': attachment.confidence_score,
                'context_clues': attachment.context_clues,
                'questions': attachment_questions,
                'question_count': len(attachment_questions),
                'is_required': attachment.confidence_score > 0.6
            }
        
        return structure

    def generate_attachment_summary(self, attachments: List[AttachmentMapping]) -> Dict[str, any]:
        """Generate a summary of identified attachments."""
        summary = {
            'total_attachments': len(attachments),
            'by_type': {},
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'total_questions_mapped': 0
        }
        
        for attachment in attachments:
            # Count by type
            att_type = attachment.attachment_type
            if att_type not in summary['by_type']:
                summary['by_type'][att_type] = 0
            summary['by_type'][att_type] += 1
            
            # Count by confidence
            if attachment.confidence_score >= 0.7:
                summary['high_confidence'] += 1
            elif attachment.confidence_score >= 0.5:
                summary['medium_confidence'] += 1
            else:
                summary['low_confidence'] += 1
            
            # Count mapped questions
            summary['total_questions_mapped'] += len(attachment.questions)
        
        return summary
