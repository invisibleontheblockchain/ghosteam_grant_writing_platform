"""
Fallback Vector Database Service for Testing
Simple implementation that works without ChromaDB dependencies
"""

import os
import uuid
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import re

class VectorDatabaseService:
    """
    Simplified fallback vector database service for testing
    Uses SQLite for storage without actual vector embeddings
    """
    
    def __init__(self, db_path: str = "vector_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize simple document storage
        self._init_fallback_db()
    
    def _init_fallback_db(self):
        """Initialize simple SQLite database for document storage"""
        db_file = self.db_path / "fallback_documents.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                document_type TEXT NOT NULL,
                grant_id INTEGER,
                content_text TEXT,
                file_size INTEGER,
                chunk_count INTEGER,
                processing_status TEXT DEFAULT 'processed',
                extracted_keywords TEXT,
                summary TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_type TEXT,
                keywords TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_document(self, file_path: str, document_type: str, 
                        grant_id: Optional[int] = None, 
                        original_filename: str = None) -> Dict:
        """
        Process a document using simple text extraction
        """
        document_id = str(uuid.uuid4())
        
        try:
            # Extract text content
            text_content = self._extract_text_simple(file_path)
            
            # Simple chunking
            chunks = self._chunk_text_simple(text_content, document_type)
            
            # Extract basic metadata
            metadata = self._extract_metadata_simple(text_content, document_type)
            
            # Store in database
            self._store_document_fallback(
                document_id, original_filename or Path(file_path).name,
                document_type, grant_id, text_content, len(chunks), metadata
            )
            
            # Store chunks
            self._store_chunks_fallback(document_id, chunks)
            
            return {
                'success': True,
                'document_id': document_id,
                'chunks_processed': len(chunks),
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"Document processing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
    
    def _extract_text_simple(self, file_path: str) -> str:
        """Simple text extraction"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.txt':
                return file_path.read_text(encoding='utf-8')
            elif extension == '.md':
                content = file_path.read_text(encoding='utf-8')
                # Remove markdown formatting
                content = re.sub(r'[#*`_]', '', content)
                return content
            else:
                # For other file types, just read as text for now
                try:
                    return file_path.read_text(encoding='utf-8')
                except:
                    return f"Binary file: {file_path.name} (content not extracted in fallback mode)"
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def _chunk_text_simple(self, text: str, document_type: str) -> List[Dict]:
        """Simple text chunking"""
        chunks = []
        
        # Split by paragraphs and sections
        paragraphs = text.split('\n\n')
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) > 50:  # Minimum chunk size
                chunks.append({
                    'text': para,
                    'type': self._classify_chunk_type(para, document_type),
                    'index': i,
                    'keywords': self._extract_keywords_simple(para)
                })
        
        return chunks
    
    def _classify_chunk_type(self, text: str, document_type: str) -> str:
        """Simple chunk type classification"""
        text_lower = text.lower()
        
        if document_type == 'grant_documents':
            if any(word in text_lower for word in ['requirement', 'deadline', 'submit', 'application']):
                return 'requirement'
            elif any(word in text_lower for word in ['budget', 'fund', 'amount', '$']):
                return 'budget'
            else:
                return 'general'
                
        elif document_type == 'organization_documents':
            if any(word in text_lower for word in ['impact', 'outcome', 'result', 'metric']):
                return 'impact'
            elif any(word in text_lower for word in ['program', 'service', 'activity']):
                return 'program'
            else:
                return 'organizational'
                
        elif document_type == 'application_outlines':
            if any(word in text_lower for word in ['objective', 'goal', 'aim']):
                return 'objective'
            elif any(word in text_lower for word in ['activity', 'task', 'deliverable']):
                return 'activity'
            elif any(word in text_lower for word in ['budget', 'cost', 'expense']):
                return 'budget'
            else:
                return 'specification'
        
        return 'general'
    
    def _extract_keywords_simple(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        # Basic keyword extraction
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        
        # Filter common words
        common_words = {'this', 'that', 'with', 'have', 'will', 'been', 'from', 'they', 'know', 'want', 'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'about', 'first', 'right', 'think', 'after', 'where', 'being', 'every', 'these', 'should', 'those', 'people', 'never', 'before', 'through', 'when', 'come', 'work', 'such', 'because', 'does', 'different', 'away', 'again', 'off', 'went', 'old', 'number', 'great', 'tell', 'men', 'say', 'small', 'every', 'found', 'still', 'between', 'name', 'should', 'home', 'big', 'give', 'air', 'line', 'set', 'own', 'under', 'read', 'last', 'never', 'us', 'left', 'end', 'why', 'called', 'didn', 'look', 'find', 'come', 'made', 'may', 'take', 'little', 'use', 'good', 'water', 'long', 'many', 'way', 'too', 'any', 'day', 'get', 'has', 'her', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        keywords = [word for word in words if word not in common_words and len(word) > 4]
        
        # Return top 10 most frequent
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]
    
    def _extract_metadata_simple(self, text: str, document_type: str) -> Dict:
        """Simple metadata extraction"""
        metadata = {}
        
        # Look for dollar amounts
        amounts = re.findall(r'\$([0-9,]+)', text)
        if amounts:
            metadata['amounts'] = amounts[:3]
        
        # Look for dates
        dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\w+ \d{1,2}, \d{4}\b', text)
        if dates:
            metadata['dates'] = dates[:3]
        
        # Look for numbers
        numbers = re.findall(r'\b\d+\b', text)
        if numbers:
            metadata['numbers'] = [n for n in numbers if len(n) <= 6][:5]
        
        return metadata
    
    def _store_document_fallback(self, document_id: str, filename: str, 
                                document_type: str, grant_id: Optional[int],
                                content: str, chunk_count: int, metadata: Dict):
        """Store document in fallback database"""
        db_file = self.db_path / "fallback_documents.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents 
            (id, original_filename, document_type, grant_id, content_text, chunk_count, 
             extracted_keywords, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            document_id, filename, document_type, grant_id, content[:5000], chunk_count,
            json.dumps(metadata), content[:500] + '...' if len(content) > 500 else content
        ))
        
        conn.commit()
        conn.close()
    
    def _store_chunks_fallback(self, document_id: str, chunks: List[Dict]):
        """Store chunks in fallback database"""
        db_file = self.db_path / "fallback_documents.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        for chunk in chunks:
            chunk_id = f"{document_id}_chunk_{chunk['index']}"
            cursor.execute('''
                INSERT INTO document_chunks 
                (id, document_id, chunk_index, chunk_text, chunk_type, keywords)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                chunk_id, document_id, chunk['index'], chunk['text'][:1000],
                chunk['type'], json.dumps(chunk['keywords'])
            ))
        
        conn.commit()
        conn.close()
    
    def search_documents(self, query: str, document_type: str, 
                        grant_id: Optional[int] = None, limit: int = 5) -> List[Dict]:
        """Simple search using keyword matching"""
        db_file = self.db_path / "fallback_documents.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Simple keyword search
        query_words = query.lower().split()
        
        sql = '''
            SELECT d.id, d.original_filename, d.document_type, c.chunk_text, c.chunk_type
            FROM documents d
            JOIN document_chunks c ON d.id = c.document_id
            WHERE d.document_type = ?
        '''
        params = [document_type]
        
        if grant_id:
            sql += ' AND d.grant_id = ?'
            params.append(grant_id)
        
        sql += ' ORDER BY d.upload_timestamp DESC LIMIT ?'
        params.append(limit * 3)  # Get more to filter
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        
        # Score results based on keyword matches
        scored_results = []
        for result in results:
            chunk_text = result[3].lower()
            score = sum(1 for word in query_words if word in chunk_text)
            
            if score > 0:
                scored_results.append({
                    'id': result[0],
                    'filename': result[1],
                    'document_type': result[2],
                    'text': result[3],
                    'chunk_type': result[4],
                    'relevance_score': score / len(query_words),
                    'metadata': {'search_type': 'keyword_match'}
                })
        
        # Sort by relevance and return top results
        scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_results[:limit]
    
    def get_document_summary(self, document_type: str, grant_id: Optional[int] = None) -> Dict:
        """Get document summary"""
        db_file = self.db_path / "fallback_documents.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        sql = '''
            SELECT COUNT(*) as doc_count, 
                   SUM(chunk_count) as total_chunks
            FROM documents 
            WHERE document_type = ?
        '''
        params = [document_type]
        
        if grant_id:
            sql += ' AND grant_id = ?'
            params.append(grant_id)
        
        cursor.execute(sql, params)
        result = cursor.fetchone()
        conn.close()
        
        return {
            'document_count': result[0] or 0,
            'total_chunks': result[1] or 0,
            'average_file_size': 0,  # Not tracked in fallback
            'document_type': document_type,
            'status': 'fallback_mode'
        }
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from fallback database"""
        try:
            db_file = self.db_path / "fallback_documents.db"
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM document_chunks WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False
