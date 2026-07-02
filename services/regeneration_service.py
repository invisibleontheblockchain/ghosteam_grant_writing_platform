
"""
Content regeneration service with user notes integration and history tracking.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RegenerationService:
    """
    Service for handling content regeneration with user notes and history tracking.
    """
    
    def __init__(self, db_path: str = "grant_platform.db"):
        self.db_path = db_path

    def regenerate_attachment_content(self, grant_id: int, attachment_id: str, 
                                    user_notes: Optional[str] = None,
                                    regeneration_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Regenerate content for an entire attachment.
        
        Args:
            grant_id: Grant ID
            attachment_id: Attachment ID to regenerate
            user_notes: Optional user guidance for regeneration
            regeneration_context: Additional context for AI generation
            
        Returns:
            Regeneration result with new content
        """
        try:
            # Get all sections for this attachment
            sections = self._get_attachment_sections(grant_id, attachment_id)
            
            if not sections:
                return {
                    'success': False,
                    'error': 'No sections found for attachment'
                }
            
            # Store regeneration request
            regen_id = self._log_regeneration_start(
                grant_id, 'attachment', attachment_id, user_notes
            )
            
            regenerated_sections = []
            failed_sections = []
            
            # Regenerate each section
            for section in sections:
                section_result = self.regenerate_section_content(
                    grant_id=grant_id,
                    section_id=section['section_id'],
                    user_notes=user_notes,
                    regeneration_context=regeneration_context,
                    skip_logging=True  # We'll log the overall attachment regeneration
                )
                
                if section_result['success']:
                    regenerated_sections.append(section_result)
                else:
                    failed_sections.append({
                        'section_id': section['section_id'],
                        'error': section_result['error']
                    })
            
            # Update regeneration log
            success = len(failed_sections) == 0
            self._log_regeneration_complete(
                regen_id, success, 
                error_message=f"Failed sections: {len(failed_sections)}" if failed_sections else None
            )
            
            logger.info(f"Regenerated attachment {attachment_id}: {len(regenerated_sections)} sections succeeded, {len(failed_sections)} failed")
            
            return {
                'success': success,
                'regeneration_id': regen_id,
                'grant_id': grant_id,
                'attachment_id': attachment_id,
                'regenerated_sections': len(regenerated_sections),
                'failed_sections': len(failed_sections),
                'section_results': regenerated_sections,
                'failures': failed_sections,
                'user_notes': user_notes,
                'regenerated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to regenerate attachment {attachment_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'grant_id': grant_id,
                'attachment_id': attachment_id
            }

    def regenerate_section_content(self, grant_id: int, section_id: int,
                                 user_notes: Optional[str] = None,
                                 regeneration_context: Optional[Dict[str, Any]] = None,
                                 skip_logging: bool = False) -> Dict[str, Any]:
        """
        Regenerate content for a specific section.
        
        Args:
            grant_id: Grant ID
            section_id: Section ID to regenerate
            user_notes: Optional user guidance for regeneration
            regeneration_context: Additional context for AI generation
            skip_logging: Skip logging (used when called from attachment regeneration)
            
        Returns:
            Regeneration result with new content
        """
        try:
            # Get current section data
            section_data = self._get_section_data(grant_id, section_id)
            
            if not section_data:
                return {
                    'success': False,
                    'error': 'Section not found'
                }
            
            # Store regeneration request
            regen_id = None
            if not skip_logging:
                regen_id = self._log_regeneration_start(
                    grant_id, 'section', str(section_id), user_notes,
                    previous_content=section_data.get('section_content', '')
                )
            
            # Generate new content using AI
            new_content = self._generate_section_content(
                section_data, user_notes, regeneration_context
            )
            
            if new_content is None:
                error_msg = "Failed to generate new content"
                if not skip_logging:
                    self._log_regeneration_complete(regen_id, False, error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Update section with new content
            update_result = self._update_section_content(grant_id, section_id, new_content)
            
            if not update_result:
                error_msg = "Failed to update section with new content"
                if not skip_logging:
                    self._log_regeneration_complete(regen_id, False, error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Log successful regeneration
            if not skip_logging:
                self._log_regeneration_complete(regen_id, True, new_content=new_content)
            
            logger.info(f"Successfully regenerated section {section_id}")
            
            return {
                'success': True,
                'regeneration_id': regen_id,
                'grant_id': grant_id,
                'section_id': section_id,
                'previous_content': section_data.get('section_content', ''),
                'new_content': new_content,
                'user_notes': user_notes,
                'regenerated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to regenerate section {section_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'grant_id': grant_id,
                'section_id': section_id
            }

    def get_regeneration_history(self, grant_id: int, target_type: Optional[str] = None,
                               target_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get regeneration history for a grant.
        
        Args:
            grant_id: Grant ID
            target_type: Optional filter by 'attachment' or 'section'
            target_id: Optional filter by specific target ID
            limit: Maximum number of records to return
            
        Returns:
            List of regeneration history records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        id, target_type, target_id, user_notes, previous_content,
                        new_content, regeneration_type, success, error_message, created_at
                    FROM regeneration_history 
                    WHERE grant_id = ?
                """
                params = [grant_id]
                
                if target_type:
                    query += " AND target_type = ?"
                    params.append(target_type)
                
                if target_id:
                    query += " AND target_id = ?"
                    params.append(target_id)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                history = []
                for row in cursor.fetchall():
                    record = {
                        'regeneration_id': row[0],
                        'target_type': row[1],
                        'target_id': row[2],
                        'user_notes': row[3],
                        'previous_content': row[4],
                        'new_content': row[5],
                        'regeneration_type': row[6],
                        'success': bool(row[7]),
                        'error_message': row[8],
                        'created_at': row[9]
                    }
                    history.append(record)
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get regeneration history for grant {grant_id}: {e}")
            return []

    def rollback_regeneration(self, grant_id: int, regeneration_id: int) -> Dict[str, Any]:
        """
        Rollback a regeneration by restoring previous content.
        
        Args:
            grant_id: Grant ID
            regeneration_id: Regeneration ID to rollback
            
        Returns:
            Rollback result
        """
        try:
            # Get regeneration record
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT target_type, target_id, previous_content, new_content
                    FROM regeneration_history 
                    WHERE id = ? AND grant_id = ?
                """, (regeneration_id, grant_id))
                
                record = cursor.fetchone()
                
                if not record:
                    return {
                        'success': False,
                        'error': 'Regeneration record not found'
                    }
                
                target_type, target_id, previous_content, new_content = record
                
                if target_type == 'section':
                    # Rollback section content
                    success = self._update_section_content(
                        grant_id, int(target_id), previous_content
                    )
                    
                    if success:
                        # Log the rollback
                        self._log_regeneration_start(
                            grant_id, 'section', target_id, 
                            f"Rollback of regeneration {regeneration_id}",
                            previous_content=new_content
                        )
                        
                        logger.info(f"Rolled back section {target_id} regeneration {regeneration_id}")
                        
                        return {
                            'success': True,
                            'grant_id': grant_id,
                            'regeneration_id': regeneration_id,
                            'target_type': target_type,
                            'target_id': target_id,
                            'restored_content': previous_content,
                            'rolled_back_at': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Failed to update section content'
                        }
                
                elif target_type == 'attachment':
                    # For attachment rollbacks, we'd need to rollback all sections
                    # This is more complex and might not be practical
                    return {
                        'success': False,
                        'error': 'Attachment rollback not implemented - rollback individual sections instead'
                    }
                
                else:
                    return {
                        'success': False,
                        'error': f'Unknown target type: {target_type}'
                    }
                
        except Exception as e:
            logger.error(f"Failed to rollback regeneration {regeneration_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_regeneration_statistics(self, grant_id: int) -> Dict[str, Any]:
        """Get statistics about regenerations for a grant."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Overall stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_regenerations,
                        COUNT(CASE WHEN success = 1 THEN 1 END) as successful_regenerations,
                        COUNT(CASE WHEN target_type = 'section' THEN 1 END) as section_regenerations,
                        COUNT(CASE WHEN target_type = 'attachment' THEN 1 END) as attachment_regenerations,
                        COUNT(CASE WHEN user_notes IS NOT NULL AND user_notes != '' THEN 1 END) as with_user_notes
                    FROM regeneration_history 
                    WHERE grant_id = ?
                """, (grant_id,))
                
                stats = cursor.fetchone()
                
                # Recent activity
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM regeneration_history 
                    WHERE grant_id = ? AND created_at >= datetime('now', '-7 days')
                """, (grant_id,))
                
                recent_count = cursor.fetchone()[0]
                
                return {
                    'grant_id': grant_id,
                    'total_regenerations': stats[0],
                    'successful_regenerations': stats[1],
                    'success_rate': stats[1] / stats[0] if stats[0] > 0 else 0,
                    'section_regenerations': stats[2],
                    'attachment_regenerations': stats[3],
                    'with_user_notes': stats[4],
                    'recent_activity_7_days': recent_count,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get regeneration statistics for grant {grant_id}: {e}")
            return {
                'error': str(e),
                'grant_id': grant_id
            }

    def _get_attachment_sections(self, grant_id: int, attachment_id: str) -> List[Dict[str, Any]]:
        """Get all sections for an attachment."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, section_title, section_content, question_text
                    FROM sections 
                    WHERE grant_id = ? AND attachment_id = ?
                    ORDER BY section_order
                """, (grant_id, attachment_id))
                
                sections = []
                for row in cursor.fetchall():
                    sections.append({
                        'section_id': row[0],
                        'section_title': row[1],
                        'section_content': row[2],
                        'question_text': row[3]
                    })
                
                return sections
                
        except Exception as e:
            logger.error(f"Failed to get sections for attachment {attachment_id}: {e}")
            return []

    def _get_section_data(self, grant_id: int, section_id: int) -> Optional[Dict[str, Any]]:
        """Get section data for regeneration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        attachment_id, attachment_type, section_title, section_content,
                        question_id, question_text, word_limit, format_requirements
                    FROM sections 
                    WHERE grant_id = ? AND id = ?
                """, (grant_id, section_id))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'attachment_id': row[0],
                        'attachment_type': row[1],
                        'section_title': row[2],
                        'section_content': row[3],
                        'question_id': row[4],
                        'question_text': row[5],
                        'word_limit': row[6],
                        'format_requirements': row[7]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get section data for {section_id}: {e}")
            return None

    def _generate_section_content(self, section_data: Dict[str, Any], 
                                user_notes: Optional[str],
                                regeneration_context: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Generate new content for a section using AI.
        This is a placeholder - actual implementation would integrate with the AI engine.
        """
        try:
            # TODO: Integrate with GrantWritingEngineV2 and vector database context
            
            # For now, return a placeholder that incorporates user notes
            question_text = section_data.get('question_text', '')
            section_title = section_data.get('section_title', '')
            word_limit = section_data.get('word_limit')
            
            # Build context for AI generation
            context_parts = [
                f"Question: {question_text}",
                f"Section: {section_title}"
            ]
            
            if user_notes:
                context_parts.append(f"User guidance: {user_notes}")
            
            if word_limit:
                context_parts.append(f"Word limit: {word_limit} words")
            
            # Placeholder content generation
            # In actual implementation, this would call the AI engine with:
            # - Vector database context from three tiers
            # - User notes for guidance
            # - Section requirements and constraints
            # - Previous content for comparison
            
            placeholder_content = f"""[AI-Generated Content for {section_title}]

This section addresses: {question_text}

{f'User guidance incorporated: {user_notes}' if user_notes else ''}

[Content would be generated here using the three-tier vector database context and AI engine]

Generated at: {datetime.now().isoformat()}
"""
            
            return placeholder_content
            
        except Exception as e:
            logger.error(f"Failed to generate section content: {e}")
            return None

    def _update_section_content(self, grant_id: int, section_id: int, new_content: str) -> bool:
        """Update section with new content."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE sections 
                    SET section_content = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE grant_id = ? AND id = ?
                """, (new_content, grant_id, section_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update section content: {e}")
            return False

    def _log_regeneration_start(self, grant_id: int, target_type: str, target_id: str,
                              user_notes: Optional[str], previous_content: Optional[str] = None) -> int:
        """Log the start of a regeneration process."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO regeneration_history (
                        grant_id, target_type, target_id, user_notes, previous_content,
                        regeneration_type, success
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    grant_id, target_type, target_id, user_notes, previous_content,
                    'user_guided' if user_notes else 'automatic', False  # Start as unsuccessful
                ))
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to log regeneration start: {e}")
            return 0

    def _log_regeneration_complete(self, regen_id: int, success: bool, 
                                 error_message: Optional[str] = None,
                                 new_content: Optional[str] = None) -> None:
        """Update regeneration log with completion status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE regeneration_history 
                    SET success = ?, error_message = ?, new_content = ?
                    WHERE id = ?
                """, (success, error_message, new_content, regen_id))
                
        except Exception as e:
            logger.error(f"Failed to log regeneration completion: {e}")

    def regenerate_content(self, grant_id: int, regeneration_type: str, target_id: Any, user_notes: str) -> Dict[str, Any]:
        """Compatibility wrapper to route regeneration requests to the appropriate method."""
        if regeneration_type == 'section':
            return self.regenerate_section_content(
                grant_id=grant_id,
                section_id=int(target_id),
                user_notes=user_notes
            )
        elif regeneration_type in ('tab', 'attachment'):
            return self.regenerate_attachment_content(
                grant_id=grant_id,
                attachment_id=str(target_id),
                user_notes=user_notes
            )
        else:
            return {
                'success': False,
                'error': f"Unsupported regeneration type: {regeneration_type}"
            }

