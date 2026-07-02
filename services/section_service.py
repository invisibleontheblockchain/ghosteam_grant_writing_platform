
"""
Section management service for CRUD operations on tabs and sections.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SectionService:
    """
    Service for managing tabs and sections with full CRUD operations.
    """
    
    def __init__(self, db_path: str = "grant_platform.db"):
        self.db_path = db_path

    def create_attachment_tab(self, grant_id: int, attachment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new attachment tab.
        
        Args:
            grant_id: Grant ID
            attachment_data: Tab data including name, type, etc.
            
        Returns:
            Created tab information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert attachment record
                cursor.execute("""
                    INSERT INTO attachments (
                        grant_id, attachment_id, attachment_name, attachment_type,
                        description, is_required, attachment_order, confidence_score,
                        context_clues
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    grant_id,
                    attachment_data['attachment_id'],
                    attachment_data['attachment_name'],
                    attachment_data['attachment_type'],
                    attachment_data.get('description', ''),
                    attachment_data.get('is_required', True),
                    attachment_data.get('attachment_order', 0),
                    attachment_data.get('confidence_score', 1.0),
                    json.dumps(attachment_data.get('context_clues', []))
                ))
                
                attachment_id = cursor.lastrowid
                
                logger.info(f"Created attachment tab {attachment_data['attachment_id']} for grant {grant_id}")
                
                return {
                    'success': True,
                    'attachment_id': attachment_data['attachment_id'],
                    'db_id': attachment_id,
                    'grant_id': grant_id,
                    'created_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to create attachment tab: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_attachment_tabs(self, grant_id: int) -> List[Dict[str, Any]]:
        """Get all attachment tabs for a grant."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        id, attachment_id, attachment_name, attachment_type,
                        description, is_required, attachment_order, confidence_score,
                        context_clues, created_at, updated_at
                    FROM attachments 
                    WHERE grant_id = ?
                    ORDER BY attachment_order, attachment_name
                """, (grant_id,))
                
                tabs = []
                for row in cursor.fetchall():
                    tab = {
                        'db_id': row[0],
                        'attachment_id': row[1],
                        'attachment_name': row[2],
                        'attachment_type': row[3],
                        'description': row[4],
                        'is_required': bool(row[5]),
                        'attachment_order': row[6],
                        'confidence_score': row[7],
                        'context_clues': json.loads(row[8]) if row[8] else [],
                        'created_at': row[9],
                        'updated_at': row[10],
                        'sections': self.get_sections_for_attachment(grant_id, row[1])
                    }
                    tabs.append(tab)
                
                return tabs
                
        except Exception as e:
            logger.error(f"Failed to get attachment tabs for grant {grant_id}: {e}")
            return []

    def update_attachment_tab(self, grant_id: int, attachment_id: str, 
                            update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an attachment tab."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                update_values = []
                
                allowed_fields = [
                    'attachment_name', 'attachment_type', 'description',
                    'is_required', 'attachment_order', 'confidence_score'
                ]
                
                for field in allowed_fields:
                    if field in update_data:
                        update_fields.append(f"{field} = ?")
                        update_values.append(update_data[field])
                
                if 'context_clues' in update_data:
                    update_fields.append("context_clues = ?")
                    update_values.append(json.dumps(update_data['context_clues']))
                
                if not update_fields:
                    return {'success': False, 'error': 'No valid fields to update'}
                
                update_values.extend([grant_id, attachment_id])
                
                cursor.execute(f"""
                    UPDATE attachments 
                    SET {', '.join(update_fields)}
                    WHERE grant_id = ? AND attachment_id = ?
                """, update_values)
                
                if cursor.rowcount == 0:
                    return {'success': False, 'error': 'Attachment not found'}
                
                logger.info(f"Updated attachment {attachment_id} for grant {grant_id}")
                
                return {
                    'success': True,
                    'attachment_id': attachment_id,
                    'grant_id': grant_id,
                    'updated_fields': list(update_data.keys()),
                    'updated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to update attachment tab: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_attachment_tab(self, grant_id: int, attachment_id: str) -> Dict[str, Any]:
        """Delete an attachment tab and all its sections."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete sections first (foreign key constraint)
                cursor.execute("""
                    DELETE FROM sections 
                    WHERE grant_id = ? AND attachment_id = ?
                """, (grant_id, attachment_id))
                
                sections_deleted = cursor.rowcount
                
                # Delete attachment
                cursor.execute("""
                    DELETE FROM attachments 
                    WHERE grant_id = ? AND attachment_id = ?
                """, (grant_id, attachment_id))
                
                if cursor.rowcount == 0:
                    return {'success': False, 'error': 'Attachment not found'}
                
                logger.info(f"Deleted attachment {attachment_id} and {sections_deleted} sections for grant {grant_id}")
                
                return {
                    'success': True,
                    'attachment_id': attachment_id,
                    'grant_id': grant_id,
                    'sections_deleted': sections_deleted,
                    'deleted_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to delete attachment tab: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_section(self, grant_id: int, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new section within an attachment."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO sections (
                        grant_id, attachment_id, attachment_name, attachment_type,
                        section_title, section_content, question_id, question_text,
                        section_order, is_required, word_limit, format_requirements
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    grant_id,
                    section_data['attachment_id'],
                    section_data.get('attachment_name', ''),
                    section_data.get('attachment_type', ''),
                    section_data['section_title'],
                    section_data.get('section_content', ''),
                    section_data.get('question_id', ''),
                    section_data.get('question_text', ''),
                    section_data.get('section_order', 0),
                    section_data.get('is_required', True),
                    section_data.get('word_limit'),
                    section_data.get('format_requirements')
                ))
                
                section_id = cursor.lastrowid
                
                logger.info(f"Created section {section_id} for attachment {section_data['attachment_id']}")
                
                return {
                    'success': True,
                    'section_id': section_id,
                    'attachment_id': section_data['attachment_id'],
                    'grant_id': grant_id,
                    'created_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to create section: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_sections_for_attachment(self, grant_id: int, attachment_id: str) -> List[Dict[str, Any]]:
        """Get all sections for a specific attachment."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        id, attachment_id, attachment_name, attachment_type,
                        section_title, section_content, question_id, question_text,
                        section_order, is_required, word_limit, format_requirements,
                        created_at, updated_at
                    FROM sections 
                    WHERE grant_id = ? AND attachment_id = ?
                    ORDER BY section_order, section_title
                """, (grant_id, attachment_id))
                
                sections = []
                for row in cursor.fetchall():
                    section = {
                        'section_id': row[0],
                        'attachment_id': row[1],
                        'attachment_name': row[2],
                        'attachment_type': row[3],
                        'section_title': row[4],
                        'section_content': row[5],
                        'question_id': row[6],
                        'question_text': row[7],
                        'section_order': row[8],
                        'is_required': bool(row[9]),
                        'word_limit': row[10],
                        'format_requirements': row[11],
                        'created_at': row[12],
                        'updated_at': row[13]
                    }
                    sections.append(section)
                
                return sections
                
        except Exception as e:
            logger.error(f"Failed to get sections for attachment {attachment_id}: {e}")
            return []

    def update_section(self, grant_id: int, section_id: int, 
                      update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a section."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                update_values = []
                
                allowed_fields = [
                    'section_title', 'section_content', 'question_id', 'question_text',
                    'section_order', 'is_required', 'word_limit', 'format_requirements'
                ]
                
                for field in allowed_fields:
                    if field in update_data:
                        update_fields.append(f"{field} = ?")
                        update_values.append(update_data[field])
                
                if not update_fields:
                    return {'success': False, 'error': 'No valid fields to update'}
                
                update_values.extend([grant_id, section_id])
                
                cursor.execute(f"""
                    UPDATE sections 
                    SET {', '.join(update_fields)}
                    WHERE grant_id = ? AND id = ?
                """, update_values)
                
                if cursor.rowcount == 0:
                    return {'success': False, 'error': 'Section not found'}
                
                logger.info(f"Updated section {section_id} for grant {grant_id}")
                
                return {
                    'success': True,
                    'section_id': section_id,
                    'grant_id': grant_id,
                    'updated_fields': list(update_data.keys()),
                    'updated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to update section: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_section(self, grant_id: int, section_id: int) -> Dict[str, Any]:
        """Delete a section."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM sections 
                    WHERE grant_id = ? AND id = ?
                """, (grant_id, section_id))
                
                if cursor.rowcount == 0:
                    return {'success': False, 'error': 'Section not found'}
                
                logger.info(f"Deleted section {section_id} for grant {grant_id}")
                
                return {
                    'success': True,
                    'section_id': section_id,
                    'grant_id': grant_id,
                    'deleted_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to delete section: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def reorder_sections(self, grant_id: int, attachment_id: str, 
                        section_orders: List[Dict[str, int]]) -> Dict[str, Any]:
        """
        Reorder sections within an attachment.
        
        Args:
            grant_id: Grant ID
            attachment_id: Attachment ID
            section_orders: List of {'section_id': int, 'order': int}
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updated_count = 0
                for section_order in section_orders:
                    cursor.execute("""
                        UPDATE sections 
                        SET section_order = ?
                        WHERE grant_id = ? AND attachment_id = ? AND id = ?
                    """, (
                        section_order['order'],
                        grant_id,
                        attachment_id,
                        section_order['section_id']
                    ))
                    updated_count += cursor.rowcount
                
                logger.info(f"Reordered {updated_count} sections for attachment {attachment_id}")
                
                return {
                    'success': True,
                    'attachment_id': attachment_id,
                    'grant_id': grant_id,
                    'sections_reordered': updated_count,
                    'updated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to reorder sections: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_grant_structure(self, grant_id: int) -> Dict[str, Any]:
        """Get the complete structure of tabs and sections for a grant."""
        try:
            tabs = self.get_attachment_tabs(grant_id)
            
            return {
                'success': True,
                'grant_id': grant_id,
                'tabs': tabs,
                'tab_count': len(tabs),
                'total_sections': sum(len(tab['sections']) for tab in tabs),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get grant structure for {grant_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'grant_id': grant_id
            }

    def bulk_create_sections(self, grant_id: int, attachment_id: str, 
                           sections_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple sections at once."""
        try:
            created_sections = []
            failed_sections = []
            
            for section_data in sections_data:
                section_data['attachment_id'] = attachment_id
                result = self.create_section(grant_id, section_data)
                
                if result['success']:
                    created_sections.append(result)
                else:
                    failed_sections.append({
                        'section_data': section_data,
                        'error': result['error']
                    })
            
            return {
                'success': len(failed_sections) == 0,
                'grant_id': grant_id,
                'attachment_id': attachment_id,
                'created_count': len(created_sections),
                'failed_count': len(failed_sections),
                'created_sections': created_sections,
                'failed_sections': failed_sections,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to bulk create sections: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_section_statistics(self, grant_id: int) -> Dict[str, Any]:
        """Get statistics about sections for a grant."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get overall stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_sections,
                        COUNT(DISTINCT attachment_id) as total_attachments,
                        AVG(CASE WHEN word_limit IS NOT NULL THEN word_limit END) as avg_word_limit,
                        COUNT(CASE WHEN section_content IS NOT NULL AND section_content != '' THEN 1 END) as sections_with_content
                    FROM sections 
                    WHERE grant_id = ?
                """, (grant_id,))
                
                stats = cursor.fetchone()
                
                # Get stats by attachment type
                cursor.execute("""
                    SELECT 
                        attachment_type,
                        COUNT(*) as section_count,
                        COUNT(CASE WHEN section_content IS NOT NULL AND section_content != '' THEN 1 END) as completed_sections
                    FROM sections 
                    WHERE grant_id = ?
                    GROUP BY attachment_type
                """, (grant_id,))
                
                by_type = {}
                for row in cursor.fetchall():
                    by_type[row[0]] = {
                        'section_count': row[1],
                        'completed_sections': row[2],
                        'completion_rate': row[2] / row[1] if row[1] > 0 else 0
                    }
                
                return {
                    'grant_id': grant_id,
                    'total_sections': stats[0],
                    'total_attachments': stats[1],
                    'avg_word_limit': stats[2],
                    'sections_with_content': stats[3],
                    'completion_rate': stats[3] / stats[0] if stats[0] > 0 else 0,
                    'by_attachment_type': by_type,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get section statistics for grant {grant_id}: {e}")
            return {
                'error': str(e),
                'grant_id': grant_id
            }

    def create_tab(self, grant_id: int, tab_name: str, tab_type: str = 'other') -> Dict[str, Any]:
        """Compatibility wrapper for create_attachment_tab."""
        import re
        attachment_id = re.sub(r'[^a-zA-Z0-9_]', '_', tab_name.lower().replace(' ', '_'))
        attachment_data = {
            'attachment_id': attachment_id,
            'attachment_name': tab_name,
            'attachment_type': tab_type,
            'description': '',
            'is_required': True,
            'attachment_order': 0,
            'confidence_score': 1.0,
            'context_clues': []
        }
        return self.create_attachment_tab(grant_id, attachment_data)

    def update_tab(self, grant_id: int, tab_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility wrapper for update_attachment_tab."""
        mapped_updates = {}
        for k, v in updates.items():
            if k == 'tab_name':
                mapped_updates['attachment_name'] = v
            elif k == 'tab_type':
                mapped_updates['attachment_type'] = v
            else:
                mapped_updates[k] = v
        return self.update_attachment_tab(grant_id, tab_id, mapped_updates)

    def delete_tab(self, grant_id: int, tab_id: str) -> Dict[str, Any]:
        """Compatibility wrapper for delete_attachment_tab."""
        return self.delete_attachment_tab(grant_id, tab_id)

