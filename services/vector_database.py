"""
Vector Database Service for Three-Tier Document Management
Handles Grant Documents, Organization Documents, and Application Outlines
"""

import os
import uuid
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import PyPDF2
import pdfplumber
from docx import Document
import markdown

class VectorDatabaseService:
    """
    Manages three separate vector databases:
    1. Grant Documents (RFP requirements & funder guidelines)
    2. Organization Documents (past grants, impact data, leadership info)
    3. Application Outlines (project specifications & deliverables)
    """
    
    def __init__(self, db_path: str = "vector_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize sentence transformer for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create three separate collections
        self.collections = {
            'grant_documents': self._get_or_create_collection('grant_documents'),
            'organization_documents': self._get_or_create_collection('organization_documents'),
            'application_outlines': self._get_or_create_collection('application_outlines')
        }
        
        # Initialize document metadata database
        self._init_metadata_db()
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.chroma_client.get_collection(name)
        except:
            return self.chroma_client.create_collection(
                name=name,
                metadata={"description": f"Vector storage for {name.replace('_', ' ')}"}
            )
    
    def _init_metadata_db(self):
        """Initialize SQLite database for document metadata"""
        metadata_db = self.db_path / "document_metadata.db"
        conn = sqlite3.connect(metadata_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_metadata (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                document_type TEXT NOT NULL,
                grant_id INTEGER,
                content_type TEXT,
                file_size INTEGER,
                chunk_count INTEGER,
                processing_status TEXT DEFAULT 'pending',
                extracted_keywords TEXT,
                summary TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_type TEXT,
                metadata TEXT,
                FOREIGN KEY (document_id) REFERENCES document_metadata (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_document(self, file_path: str, document_type: str, 
                        grant_id: Optional[int] = None, 
                        original_filename: str = None) -> Dict:
        """
        Process a document and store in appropriate vector database
        
        Args:
            file_path: Path to the uploaded file
            document_type: 'grant_documents', 'organization_documents', or 'application_outlines'
            grant_id: Associated grant ID (optional)
            original_filename: Original filename for metadata
        
        Returns:
            Dict with processing results
        """
        if document_type not in self.collections:
            raise ValueError(f"Invalid document type: {document_type}")
        
        document_id = str(uuid.uuid4())
        
        try:
            # Extract text from document
            text_content = self._extract_text(file_path)
            
            # Chunk the document based on type
            chunks = self._chunk_document(text_content, document_type)
            
            # Generate embeddings and store in vector database
            self._store_chunks_in_vector_db(document_id, chunks, document_type)
            
            # Extract metadata based on document type
            metadata = self._extract_document_metadata(text_content, document_type)
            
            # Store metadata in SQLite
            self._store_document_metadata(
                document_id, original_filename or Path(file_path).name,
                document_type, grant_id, Path(file_path).stat().st_size,
                len(chunks), metadata
            )
            
            return {
                'success': True,
                'document_id': document_id,
                'chunks_processed': len(chunks),
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from various file formats"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif extension == '.md':
                return self._extract_from_markdown(file_path)
            elif extension == '.txt':
                return file_path.read_text(encoding='utf-8')
            else:
                raise ValueError(f"Unsupported file format: {extension}")
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        # Try pdfplumber first (better for structured documents)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except:
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                raise Exception(f"PDF extraction failed: {str(e)}")
        
        return text.strip()
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX files"""
        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
    
    def _extract_from_markdown(self, file_path: Path) -> str:
        """Extract text from Markdown files"""
        try:
            md_text = file_path.read_text(encoding='utf-8')
            # Convert markdown to plain text (removes formatting)
            html = markdown.markdown(md_text)
            # Simple HTML tag removal
            import re
            text = re.sub('<[^<]+?>', '', html)
            return text
        except Exception as e:
            raise Exception(f"Markdown extraction failed: {str(e)}")
    
    def _chunk_document(self, text: str, document_type: str) -> List[Dict]:
        """Chunk document based on type-specific strategies"""
        chunks = []
        
        if document_type == 'grant_documents':
            # For RFPs/Guidelines: chunk by sections and questions
            chunks = self._chunk_grant_document(text)
        elif document_type == 'organization_documents':
            # For org docs: chunk by topics and achievements
            chunks = self._chunk_organization_document(text)
        elif document_type == 'application_outlines':
            # For outlines: chunk by project components and specifications
            chunks = self._chunk_outline_document(text)
        
        return chunks
    
    def _chunk_grant_document(self, text: str) -> List[Dict]:
        """Chunk grant documents focusing on requirements and questions"""
        chunks = []
        
        # Split by common RFP sections
        section_patterns = [
            r'(?i)section\s+\d+',
            r'(?i)part\s+[A-Z]',
            r'(?i)question\s+\d+',
            r'(?i)requirement\s+\d+',
            r'(?i)attachment\s+[A-Z]',
            r'(?i)appendix\s+[A-Z]'
        ]
        
        # Find section breaks
        import re
        splits = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, text):
                splits.append((match.start(), match.group()))
        
        splits.sort()
        
        # Create chunks from sections
        if splits:
            for i, (start, section_title) in enumerate(splits):
                end = splits[i + 1][0] if i + 1 < len(splits) else len(text)
                chunk_text = text[start:end].strip()
                
                if len(chunk_text) > 100:  # Minimum chunk size
                    chunks.append({
                        'text': chunk_text,
                        'type': 'section',
                        'title': section_title,
                        'metadata': {'section_type': 'requirement'}
                    })
        else:
            # Fallback: chunk by paragraphs
            paragraphs = text.split('\n\n')
            for i, para in enumerate(paragraphs):
                if len(para.strip()) > 100:
                    chunks.append({
                        'text': para.strip(),
                        'type': 'paragraph',
                        'title': f'Paragraph {i+1}',
                        'metadata': {'content_type': 'general'}
                    })
        
        return chunks
    
    def _chunk_organization_document(self, text: str) -> List[Dict]:
        """Chunk organization documents focusing on impact and capabilities"""
        chunks = []
        
        # Look for impact metrics, achievements, and organizational info
        import re
        
        # Split by common org doc sections
        org_patterns = [
            r'(?i)(mission|vision|values)',
            r'(?i)(programs?|services?)',
            r'(?i)(impact|outcomes?|results?)',
            r'(?i)(staff|team|leadership)',
            r'(?i)(partnerships?|collaborations?)',
            r'(?i)(budget|financial|funding)',
            r'(?i)(geographic|service area)',
            r'(?i)(achievements?|awards?|recognition)'
        ]
        
        # Simple paragraph-based chunking with metadata
        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs):
            if len(para.strip()) > 50:
                # Determine content type based on keywords
                content_type = 'general'
                for pattern in org_patterns:
                    if re.search(pattern, para):
                        content_type = re.search(pattern, para).group(1).lower()
                        break
                
                chunks.append({
                    'text': para.strip(),
                    'type': 'organizational_info',
                    'title': f'Section {i+1}',
                    'metadata': {'content_type': content_type}
                })
        
        return chunks
    
    def _chunk_outline_document(self, text: str) -> List[Dict]:
        """Chunk application outlines focusing on project specifications"""
        chunks = []
        
        # Look for project components, budgets, timelines
        import re
        
        outline_patterns = [
            r'(?i)(objectives?|goals?)',
            r'(?i)(activities?|tasks?)',
            r'(?i)(timeline|schedule)',
            r'(?i)(budget|costs?|expenses?)',
            r'(?i)(deliverables?|outputs?)',
            r'(?i)(outcomes?|metrics?)',
            r'(?i)(partnerships?|collaborations?)',
            r'(?i)(evaluation|assessment)'
        ]
        
        # Split by bullet points and numbered items
        lines = text.split('\n')
        current_chunk = []
        current_type = 'general'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new section
            is_new_section = any(re.search(pattern, line) for pattern in outline_patterns)
            
            if is_new_section and current_chunk:
                # Save previous chunk
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text) > 50:
                    chunks.append({
                        'text': chunk_text,
                        'type': 'project_specification',
                        'title': current_type.title(),
                        'metadata': {'spec_type': current_type}
                    })
                current_chunk = []
            
            if is_new_section:
                for pattern in outline_patterns:
                    match = re.search(pattern, line)
                    if match:
                        current_type = match.group(1).lower()
                        break
            
            current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > 50:
                chunks.append({
                    'text': chunk_text,
                    'type': 'project_specification',
                    'title': current_type.title(),
                    'metadata': {'spec_type': current_type}
                })
        
        return chunks
    
    def _store_chunks_in_vector_db(self, document_id: str, chunks: List[Dict], document_type: str):
        """Store document chunks in the appropriate vector database"""
        collection = self.collections[document_type]
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            ids.append(chunk_id)
            
            # Generate embedding
            embedding = self.encoder.encode(chunk['text']).tolist()
            embeddings.append(embedding)
            
            documents.append(chunk['text'])
            
            # Prepare metadata
            metadata = {
                'document_id': document_id,
                'chunk_index': i,
                'chunk_type': chunk.get('type', 'general'),
                'title': chunk.get('title', ''),
                **chunk.get('metadata', {})
            }
            metadatas.append(metadata)
        
        # Store in ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        # Store chunk metadata in SQLite
        self._store_chunk_metadata(document_id, chunks)
    
    def _extract_document_metadata(self, text: str, document_type: str) -> Dict:
        """Extract document-specific metadata"""
        metadata = {}
        
        if document_type == 'grant_documents':
            metadata = self._extract_grant_metadata(text)
        elif document_type == 'organization_documents':
            metadata = self._extract_org_metadata(text)
        elif document_type == 'application_outlines':
            metadata = self._extract_outline_metadata(text)
        
        return metadata
    
    def _extract_grant_metadata(self, text: str) -> Dict:
        """Extract metadata from grant documents (RFPs, guidelines)"""
        import re
        metadata = {}
        
        # Look for deadlines
        deadline_patterns = [
            r'deadline[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
            r'due[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
            r'submit.*by[:\s]+([A-Za-z]+ \d{1,2}, \d{4})'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['deadline'] = match.group(1)
                break
        
        # Look for funding amounts
        amount_patterns = [
            r'\$([0-9,]+)',
            r'([0-9,]+) dollars',
            r'funding.*\$([0-9,]+)'
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        if amounts:
            metadata['funding_amounts'] = amounts[:3]  # Keep top 3
        
        # Look for requirements
        requirement_count = len(re.findall(r'(?i)require', text))
        metadata['requirement_density'] = requirement_count
        
        return metadata
    
    def _extract_org_metadata(self, text: str) -> Dict:
        """Extract metadata from organization documents"""
        import re
        metadata = {}
        
        # Look for metrics and numbers
        metrics = re.findall(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:%|percent|people|participants|dollars|\$)', text)
        if metrics:
            metadata['key_metrics'] = metrics[:5]  # Top 5 metrics
        
        # Look for geographic references
        geo_patterns = [
            r'(?i)(county|city|state|region|area):\s*([A-Za-z\s]+)',
            r'(?i)serving\s+([A-Za-z\s]+(?:county|city|area))',
            r'(?i)located\s+in\s+([A-Za-z\s]+)'
        ]
        
        locations = []
        for pattern in geo_patterns:
            matches = re.findall(pattern, text)
            locations.extend([match[1] if isinstance(match, tuple) else match for match in matches])
        
        if locations:
            metadata['service_areas'] = locations[:3]
        
        return metadata
    
    def _extract_outline_metadata(self, text: str) -> Dict:
        """Extract metadata from application outlines"""
        import re
        metadata = {}
        
        # Look for budget information
        budget_matches = re.findall(r'\$([0-9,]+)', text)
        if budget_matches:
            metadata['budget_items'] = budget_matches[:5]
        
        # Look for timeline information
        timeline_patterns = [
            r'(?i)(month|quarter|year)\s+(\d+)',
            r'(\d+)\s+(?i)(months?|quarters?|years?)',
            r'(?i)(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})'
        ]
        
        timeline_refs = []
        for pattern in timeline_patterns:
            matches = re.findall(pattern, text)
            timeline_refs.extend(matches)
        
        if timeline_refs:
            metadata['timeline_references'] = timeline_refs[:3]
        
        # Look for deliverables
        deliverable_count = len(re.findall(r'(?i)deliver|output|outcome|result', text))
        metadata['deliverable_density'] = deliverable_count
        
        return metadata
    
    def _store_document_metadata(self, document_id: str, filename: str, 
                                document_type: str, grant_id: Optional[int],
                                file_size: int, chunk_count: int, metadata: Dict):
        """Store document metadata in SQLite"""
        metadata_db = self.db_path / "document_metadata.db"
        conn = sqlite3.connect(metadata_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO document_metadata 
            (id, original_filename, document_type, grant_id, file_size, chunk_count, 
             processing_status, extracted_keywords, summary, processing_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            document_id, filename, document_type, grant_id, file_size, chunk_count,
            'processed', json.dumps(metadata.get('keywords', [])),
            metadata.get('summary', ''), datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def _store_chunk_metadata(self, document_id: str, chunks: List[Dict]):
        """Store chunk metadata in SQLite"""
        metadata_db = self.db_path / "document_metadata.db"
        conn = sqlite3.connect(metadata_db)
        cursor = conn.cursor()
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            cursor.execute('''
                INSERT INTO document_chunks 
                (id, document_id, chunk_index, chunk_text, chunk_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                chunk_id, document_id, i, chunk['text'][:1000],  # Truncate for storage
                chunk.get('type', 'general'), json.dumps(chunk.get('metadata', {}))
            ))
        
        conn.commit()
        conn.close()
    
    def search_documents(self, query: str, document_type: str, 
                        grant_id: Optional[int] = None, limit: int = 5) -> List[Dict]:
        """
        Search for relevant documents in the specified category
        
        Args:
            query: Search query
            document_type: Which document category to search
            grant_id: Filter by grant ID (optional)
            limit: Maximum number of results
        
        Returns:
            List of relevant document chunks with metadata
        """
        if document_type not in self.collections:
            raise ValueError(f"Invalid document type: {document_type}")
        
        collection = self.collections[document_type]
        
        # Generate query embedding
        query_embedding = self.encoder.encode(query).tolist()
        
        # Search vector database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'relevance_score': 1 - results['distances'][0][i],  # Convert distance to relevance
                'document_type': document_type
            })
        
        return formatted_results
    
    def get_document_summary(self, document_type: str, grant_id: Optional[int] = None) -> Dict:
        """Get summary of documents in a category"""
        metadata_db = self.db_path / "document_metadata.db"
        conn = sqlite3.connect(metadata_db)
        cursor = conn.cursor()
        
        query = '''
            SELECT COUNT(*) as doc_count, 
                   SUM(chunk_count) as total_chunks,
                   AVG(file_size) as avg_file_size
            FROM document_metadata 
            WHERE document_type = ?
        '''
        params = [document_type]
        
        if grant_id:
            query += ' AND grant_id = ?'
            params.append(grant_id)
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'document_count': result[0] or 0,
            'total_chunks': result[1] or 0,
            'average_file_size': result[2] or 0,
            'document_type': document_type
        }
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks from all databases"""
        try:
            # Remove from all vector collections
            for collection in self.collections.values():
                try:
                    # Get chunk IDs for this document
                    results = collection.get(
                        where={"document_id": document_id},
                        include=['ids']
                    )
                    if results['ids']:
                        collection.delete(ids=results['ids'])
                except:
                    pass  # Document may not exist in this collection
            
            # Remove from metadata database
            metadata_db = self.db_path / "document_metadata.db"
            conn = sqlite3.connect(metadata_db)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM document_chunks WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM document_metadata WHERE id = ?', (document_id,))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False
