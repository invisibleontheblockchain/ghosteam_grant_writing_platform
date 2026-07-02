
"""
Document processing service that orchestrates parsing, classification, and vector storage.
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
from datetime import datetime

from parsers.grant_parser import GrantDocumentParser
from parsers.question_extractor import QuestionExtractor
from parsers.attachment_mapper import AttachmentMapper
from vector_store.three_tier_db import ThreeTierVectorDB

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Service for processing documents and managing the three-tier vector database.
    """
    
    def __init__(self, vector_db: Optional[ThreeTierVectorDB] = None):
        self.parser = GrantDocumentParser()
        self.question_extractor = QuestionExtractor()
        self.attachment_mapper = AttachmentMapper()
        self.vector_db = vector_db or ThreeTierVectorDB()
        
        # Document type classification mapping
        self.tier_mapping = {
            'RFP': 'grant_documents',
            'Application Guidelines': 'grant_documents',
            'Grant Document': 'grant_documents',
            'Organization Document': 'organization_documents',
            'Application Outline': 'application_outlines',
            'Project Outline': 'application_outlines',
            'Budget Outline': 'application_outlines'
        }

    def process_document(self, file_path: str, grant_id: int, 
                        document_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            grant_id: ID of the associated grant
            document_type: Optional override for document type classification
            
        Returns:
            Dictionary containing processing results
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Step 1: Parse the document
            analysis = self.parser.parse_document(file_path)
            
            # Step 2: Override document type if provided
            if document_type:
                analysis.document_type = document_type
            
            # Step 3: Enhanced question extraction
            enhanced_questions = self.question_extractor.extract_questions_with_context(
                self._read_file_content(file_path)
            )
            
            # Step 4: Enhanced attachment mapping
            attachment_mappings = self.attachment_mapper.identify_attachments(
                self._read_file_content(file_path), enhanced_questions
            )
            
            # Step 5: Store in appropriate vector database tier
            tier = self._determine_tier(analysis.document_type)
            vector_id = self._store_in_vector_db(file_path, analysis, tier, grant_id)
            
            # Step 6: Prepare comprehensive results
            results = {
                'success': True,
                'document_analysis': self.parser.to_dict(analysis),
                'enhanced_questions': enhanced_questions,
                'attachment_mappings': [
                    {
                        'attachment_id': am.attachment_id,
                        'attachment_name': am.attachment_name,
                        'attachment_type': am.attachment_type,
                        'questions': am.questions,
                        'confidence_score': am.confidence_score,
                        'context_clues': am.context_clues
                    }
                    for am in attachment_mappings
                ],
                'vector_storage': {
                    'tier': tier,
                    'vector_id': vector_id,
                    'success': vector_id is not None
                },
                'processing_metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'grant_id': grant_id,
                    'file_path': file_path,
                    'total_questions': len(enhanced_questions),
                    'total_attachments': len(attachment_mappings)
                }
            }
            
            logger.info(f"Successfully processed document {file_path}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'grant_id': grant_id
            }

    def classify_document_type(self, file_path: str, content: Optional[str] = None) -> str:
        """
        Classify document type based on content and filename.
        
        Args:
            file_path: Path to the document
            content: Optional document content (will read if not provided)
            
        Returns:
            Classified document type
        """
        try:
            if content is None:
                content = self._read_file_content(file_path)
            
            file_path_obj = Path(file_path)
            filename_lower = file_path_obj.name.lower()
            content_lower = content.lower()
            
            # Check for specific document types
            if any(term in content_lower or term in filename_lower 
                   for term in ['rfp', 'request for proposal', 'solicitation']):
                return 'RFP'
            
            elif any(term in content_lower or term in filename_lower 
                     for term in ['application', 'guidelines', 'instructions']):
                return 'Application Guidelines'
            
            elif any(term in content_lower or term in filename_lower 
                     for term in ['outline', 'template', 'framework']):
                if any(term in content_lower or term in filename_lower 
                       for term in ['project', 'program', 'proposal']):
                    return 'Application Outline'
                else:
                    return 'Grant Document'
            
            elif any(term in content_lower or term in filename_lower 
                     for term in ['organization', 'org', 'company', 'nonprofit']):
                return 'Organization Document'
            
            elif any(term in content_lower or term in filename_lower 
                     for term in ['budget', 'financial', 'cost']):
                if any(term in content_lower or term in filename_lower 
                       for term in ['outline', 'template', 'plan']):
                    return 'Budget Outline'
                else:
                    return 'Organization Document'
            
            else:
                # Default classification based on content analysis
                return self.parser._classify_document_type(content, file_path_obj)
                
        except Exception as e:
            logger.error(f"Failed to classify document {file_path}: {e}")
            return 'Grant Document'  # Default fallback

    def generate_dynamic_tabs(self, grant_id: int, processed_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate dynamic tabs based on processed documents.
        
        Args:
            grant_id: Grant ID
            processed_documents: List of processed document results
            
        Returns:
            Tab structure with sections and questions
        """
        try:
            tabs = {}
            all_attachments = {}
            
            # Collect all attachments from processed documents
            for doc_result in processed_documents:
                if not doc_result.get('success'):
                    continue
                
                for attachment in doc_result.get('attachment_mappings', []):
                    att_id = attachment['attachment_id']
                    att_type = attachment['attachment_type']
                    
                    if att_id not in all_attachments:
                        all_attachments[att_id] = {
                            'attachment_id': att_id,
                            'attachment_name': attachment['attachment_name'],
                            'attachment_type': att_type,
                            'questions': [],
                            'confidence_score': attachment['confidence_score'],
                            'context_clues': attachment['context_clues']
                        }
                    
                    # Add questions from this document
                    for question_id in attachment['questions']:
                        # Find the full question data
                        for question in doc_result.get('enhanced_questions', []):
                            if question.get('question_id') == question_id:
                                all_attachments[att_id]['questions'].append(question)
                                break
            
            # Create tabs from attachments
            tab_order = ['proposal', 'budget', 'timeline', 'evaluation', 'organizational', 'letters', 'sustainability', 'other']
            
            for attachment_id, attachment_data in all_attachments.items():
                att_type = attachment_data['attachment_type']
                
                # Determine tab order
                order = tab_order.index(att_type) if att_type in tab_order else len(tab_order)
                
                tabs[attachment_id] = {
                    'tab_id': attachment_id,
                    'tab_name': attachment_data['attachment_name'],
                    'tab_type': att_type,
                    'tab_order': order,
                    'is_required': attachment_data['confidence_score'] > 0.6,
                    'sections': self._create_sections_from_questions(
                        attachment_data['questions'], attachment_id
                    ),
                    'metadata': {
                        'confidence_score': attachment_data['confidence_score'],
                        'context_clues': attachment_data['context_clues'],
                        'question_count': len(attachment_data['questions'])
                    }
                }
            
            # Ensure we always have a proposal tab
            if not any(tab['tab_type'] == 'proposal' for tab in tabs.values()):
                tabs['proposal_default'] = {
                    'tab_id': 'proposal_default',
                    'tab_name': 'Project Proposal',
                    'tab_type': 'proposal',
                    'tab_order': 0,
                    'is_required': True,
                    'sections': [],
                    'metadata': {
                        'confidence_score': 1.0,
                        'context_clues': ['Default proposal tab'],
                        'question_count': 0
                    }
                }
            
            # Ensure we always have a budget tab
            if not any(tab['tab_type'] == 'budget' for tab in tabs.values()):
                tabs['budget_default'] = {
                    'tab_id': 'budget_default',
                    'tab_name': 'Project Budget',
                    'tab_type': 'budget',
                    'tab_order': 1,
                    'is_required': True,
                    'sections': [],
                    'metadata': {
                        'confidence_score': 1.0,
                        'context_clues': ['Default budget tab'],
                        'question_count': 0
                    }
                }
            
            return {
                'success': True,
                'grant_id': grant_id,
                'tabs': tabs,
                'tab_count': len(tabs),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate dynamic tabs for grant {grant_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'grant_id': grant_id
            }

    def _create_sections_from_questions(self, questions: List[Dict], attachment_id: str) -> List[Dict]:
        """Create sections from questions for a specific attachment."""
        sections = []
        
        for i, question in enumerate(questions):
            section = {
                'section_id': f"{attachment_id}_S{i+1:03d}",
                'section_title': self._generate_section_title(question),
                'section_content': '',  # Will be generated by AI
                'question_id': question.get('question_id', ''),
                'question_text': question.get('question_text', ''),
                'section_order': i,
                'requirements': question.get('requirements', {}),
                'is_required': True,
                'metadata': {
                    'question_type': question.get('question_type', ''),
                    'complexity_score': question.get('complexity_score', 0.5),
                    'confidence_score': question.get('confidence_score', 0.5)
                }
            }
            sections.append(section)
        
        return sections

    def _generate_section_title(self, question: Dict) -> str:
        """Generate a section title from a question."""
        question_text = question.get('question_text', '')
        
        # Extract key words for title
        if len(question_text) > 50:
            # Take first few words and add ellipsis
            words = question_text.split()[:8]
            title = ' '.join(words)
            if len(words) == 8:
                title += '...'
        else:
            title = question_text
        
        # Clean up title
        title = title.replace('\n', ' ').strip()
        if title.endswith('.'):
            title = title[:-1]
        
        return title

    def _determine_tier(self, document_type: str) -> str:
        """Determine which vector database tier to use."""
        return self.tier_mapping.get(document_type, 'grant_documents')

    def _store_in_vector_db(self, file_path: str, analysis, tier: str, grant_id: int) -> Optional[str]:
        """Store document in the appropriate vector database tier."""
        try:
            content = self._read_file_content(file_path)
            
            # Create unique document ID
            vector_id = f"grant_{grant_id}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata
            metadata = {
                'grant_id': grant_id,
                'file_path': file_path,
                'document_type': analysis.document_type,
                'total_pages': analysis.total_pages,
                'question_count': len(analysis.questions),
                'attachment_count': len(analysis.attachments),
                'processed_at': datetime.now().isoformat()
            }
            
            # Store in vector database
            success = self.vector_db.add_document(
                tier=tier,
                document_id=vector_id,
                content=content,
                metadata=metadata
            )
            
            return vector_id if success else None
            
        except Exception as e:
            logger.error(f"Failed to store document in vector DB: {e}")
            return None

    def _read_file_content(self, file_path: str) -> str:
        """Read content from file based on file type."""
        try:
            file_path_obj = Path(file_path)
            
            if file_path_obj.suffix.lower() == '.pdf':
                text, _ = self.parser._extract_pdf_text(file_path_obj)
                return text
            elif file_path_obj.suffix.lower() in ['.docx', '.doc']:
                text, _ = self.parser._extract_docx_text(file_path_obj)
                return text
            elif file_path_obj.suffix.lower() in ['.txt', '.md']:
                text, _ = self.parser._extract_text_file(file_path_obj)
                return text
            else:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Failed to read file content from {file_path}: {e}")
            return ""

    def query_context_for_generation(self, grant_id: int, query: str, 
                                   context_type: str = 'all') -> Dict[str, Any]:
        """
        Query the vector database for context to use in content generation.
        
        Args:
            grant_id: Grant ID to filter results
            query: Query string
            context_type: 'all', 'grant_documents', 'organization_documents', or 'application_outlines'
            
        Returns:
            Context results from appropriate tiers
        """
        try:
            filters = {'grant_id': grant_id}
            
            if context_type == 'all':
                results = self.vector_db.query_all_tiers(query, n_results_per_tier=3)
            else:
                results = {
                    context_type: self.vector_db.query_tier(context_type, query, n_results=5, filters=filters)
                }
            
            # Filter results by grant_id
            filtered_results = {}
            for tier, tier_results in results.items():
                filtered_results[tier] = [
                    result for result in tier_results 
                    if result.get('metadata', {}).get('grant_id') == grant_id
                ]
            
            return {
                'success': True,
                'query': query,
                'context_type': context_type,
                'results': filtered_results,
                'total_results': sum(len(tier_results) for tier_results in filtered_results.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to query context for grant {grant_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'context_type': context_type
            }

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about document processing and vector storage."""
        try:
            vector_stats = self.vector_db.get_all_stats()
            
            return {
                'vector_database': vector_stats,
                'processing_capabilities': {
                    'supported_formats': ['.pdf', '.docx', '.doc', '.txt', '.md'],
                    'question_extraction': True,
                    'attachment_mapping': True,
                    'three_tier_storage': True
                },
                'service_status': 'operational'
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {
                'service_status': 'error',
                'error': str(e)
            }
