
"""
Three-tier vector database implementation using ChromaDB.
Provides separate collections for Grant Documents, Organization Documents, and Application Outlines.
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available, using fallback implementation")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available, will use fallback embeddings/keywords")


logger = logging.getLogger(__name__)

class ThreeTierVectorDB:
    """
    Three-tier vector database system with separate collections for:
    1. Grant Documents (requirements and context)
    2. Organization Documents (history and impact)  
    3. Application Outlines (specific proposal details)
    """
    
    def __init__(self, db_path: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = Path(db_path)
        self.model_name = model_name
        self.embedding_model = None
        self.client = None
        self.collections = {}
        
        # Collection names for the three tiers
        self.tier_names = {
            'grant_documents': 'grant_documents',
            'organization_documents': 'organization_documents', 
            'application_outlines': 'application_outlines'
        }
        
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the ChromaDB client and collections."""
        try:
            if CHROMADB_AVAILABLE:
                # Initialize ChromaDB client
                self.client = chromadb.PersistentClient(
                    path=str(self.db_path),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                # Initialize collections for each tier
                for tier_key, collection_name in self.tier_names.items():
                    try:
                        collection = self.client.get_or_create_collection(
                            name=collection_name,
                            metadata={"tier": tier_key, "created_at": datetime.now().isoformat()}
                        )
                        self.collections[tier_key] = collection
                        logger.info(f"Initialized collection: {collection_name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize collection {collection_name}: {e}")
                        raise
                
                logger.info("ChromaDB three-tier system initialized successfully")
            else:
                # Fallback to in-memory storage
                self._initialize_fallback()
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self._initialize_fallback()

    def _initialize_fallback(self):
        """Initialize fallback in-memory storage when ChromaDB is not available."""
        logger.warning("Using fallback in-memory vector storage")
        self.collections = {
            'grant_documents': {'documents': [], 'embeddings': [], 'metadata': []},
            'organization_documents': {'documents': [], 'embeddings': [], 'metadata': []},
            'application_outlines': {'documents': [], 'embeddings': [], 'metadata': []}
        }
        self.client = None

    def _get_embedding_model(self):
        """Lazy load the embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return None
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self.embedding_model

    def add_document(self, tier: str, document_id: str, content: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a document to the specified tier.
        
        Args:
            tier: One of 'grant_documents', 'organization_documents', 'application_outlines'
            document_id: Unique identifier for the document
            content: Document content to embed
            metadata: Optional metadata dictionary
            
        Returns:
            bool: Success status
        """
        try:
            if tier not in self.tier_names:
                raise ValueError(f"Invalid tier: {tier}. Must be one of {list(self.tier_names.keys())}")
            
            if not content or not content.strip():
                logger.warning(f"Empty content for document {document_id}, skipping")
                return False
            
            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata.update({
                'tier': tier,
                'document_id': document_id,
                'added_at': datetime.now().isoformat(),
                'content_length': len(content)
            })
            
            if CHROMADB_AVAILABLE and self.client:
                # Use ChromaDB
                collection = self.collections[tier]
                collection.add(
                    documents=[content],
                    ids=[document_id],
                    metadatas=[doc_metadata]
                )
                logger.info(f"Added document {document_id} to {tier} collection")
            else:
                # Use fallback storage
                embedding = []
                model = self._get_embedding_model()
                if model is not None:
                    try:
                        embedding = model.encode([content])[0].tolist()
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding: {e}")
                
                self.collections[tier]['documents'].append(content)
                self.collections[tier]['embeddings'].append(embedding)
                self.collections[tier]['metadata'].append(doc_metadata)
                logger.info(f"Added document {document_id} to fallback {tier} storage")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document {document_id} to {tier}: {e}")
            return False

    def query_tier(self, tier: str, query: str, n_results: int = 5, 
                  filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query a specific tier for relevant documents.
        
        Args:
            tier: Tier to query
            query: Query string
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of matching documents with metadata and scores
        """
        try:
            if tier not in self.tier_names:
                raise ValueError(f"Invalid tier: {tier}")
            
            if CHROMADB_AVAILABLE and self.client:
                # Use ChromaDB
                collection = self.collections[tier]
                
                # Build where clause for filters
                where_clause = filters if filters else None
                
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause
                )
                
                # Format results
                formatted_results = []
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'document_id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'tier': tier
                    })
                
                return formatted_results
                
            else:
                # Use fallback storage
                return self._query_fallback(tier, query, n_results, filters)
                
        except Exception as e:
            logger.error(f"Failed to query {tier}: {e}")
            return []

    def _query_fallback(self, tier: str, query: str, n_results: int, 
                       filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Query fallback storage using cosine similarity or keyword matching."""
        try:
            tier_data = self.collections[tier]
            if not tier_data['documents']:
                return []

            model = self._get_embedding_model()
            if model is not None:
                try:
                    query_embedding = model.encode([query])[0]
                    
                    # Calculate similarities
                    similarities = []
                    for i, doc_embedding in enumerate(tier_data['embeddings']):
                        if not doc_embedding:
                            continue
                        # Simple cosine similarity
                        similarity = self._cosine_similarity(query_embedding, doc_embedding)
                        
                        # Apply filters if provided
                        if filters:
                            metadata = tier_data['metadata'][i]
                            if not self._matches_filters(metadata, filters):
                                continue
                        
                        similarities.append((similarity, i))
                    
                    # Sort by similarity and take top n_results
                    similarities.sort(reverse=True)
                    similarities = similarities[:n_results]
                    
                    # Format results
                    results = []
                    for similarity, idx in similarities:
                        results.append({
                            'document_id': tier_data['metadata'][idx].get('document_id', f'doc_{idx}'),
                            'content': tier_data['documents'][idx],
                            'metadata': tier_data['metadata'][idx],
                            'similarity': similarity,
                            'tier': tier
                        })
                    
                    return results
                except Exception as e:
                    logger.warning(f"Vector search failed, falling back to keyword search: {e}")

            # Keyword-based fallback search (no model needed)
            query_words = set(query.lower().split())
            matches = []
            for i, doc in enumerate(tier_data['documents']):
                doc_lower = doc.lower()
                # Count matching words as score
                score = sum(1 for word in query_words if word in doc_lower)
                
                # Apply filters
                if filters:
                    metadata = tier_data['metadata'][i]
                    if not self._matches_filters(metadata, filters):
                        continue
                
                if score > 0 or not query_words:
                    matches.append((score, i))
            
            matches.sort(reverse=True)
            matches = matches[:n_results]
            
            results = []
            for score, idx in matches:
                similarity = score / max(1, len(query_words))
                results.append({
                    'document_id': tier_data['metadata'][idx].get('document_id', f'doc_{idx}'),
                    'content': tier_data['documents'][idx],
                    'metadata': tier_data['metadata'][idx],
                    'similarity': similarity,
                    'tier': tier
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback query failed for {tier}: {e}")
            return []

    def query_all_tiers(self, query: str, n_results_per_tier: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query all three tiers and return results organized by tier.
        
        Args:
            query: Query string
            n_results_per_tier: Number of results per tier
            
        Returns:
            Dictionary with results from each tier
        """
        results = {}
        
        for tier in self.tier_names.keys():
            tier_results = self.query_tier(tier, query, n_results_per_tier)
            results[tier] = tier_results
            logger.info(f"Found {len(tier_results)} results in {tier}")
        
        return results

    def get_tier_stats(self, tier: str) -> Dict[str, Any]:
        """Get statistics for a specific tier."""
        try:
            if tier not in self.tier_names:
                raise ValueError(f"Invalid tier: {tier}")
            
            if CHROMADB_AVAILABLE and self.client:
                collection = self.collections[tier]
                count = collection.count()
                
                return {
                    'tier': tier,
                    'document_count': count,
                    'collection_name': self.tier_names[tier],
                    'storage_type': 'chromadb'
                }
            else:
                tier_data = self.collections[tier]
                return {
                    'tier': tier,
                    'document_count': len(tier_data['documents']),
                    'collection_name': self.tier_names[tier],
                    'storage_type': 'fallback'
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats for {tier}: {e}")
            return {'tier': tier, 'document_count': 0, 'error': str(e)}

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all tiers."""
        stats = {
            'total_documents': 0,
            'tiers': {},
            'storage_type': 'chromadb' if CHROMADB_AVAILABLE and self.client else 'fallback',
            'model_name': self.model_name
        }
        
        for tier in self.tier_names.keys():
            tier_stats = self.get_tier_stats(tier)
            stats['tiers'][tier] = tier_stats
            stats['total_documents'] += tier_stats.get('document_count', 0)
        
        return stats

    def delete_document(self, tier: str, document_id: str) -> bool:
        """Delete a document from the specified tier."""
        try:
            if tier not in self.tier_names:
                raise ValueError(f"Invalid tier: {tier}")
            
            if CHROMADB_AVAILABLE and self.client:
                collection = self.collections[tier]
                collection.delete(ids=[document_id])
                logger.info(f"Deleted document {document_id} from {tier}")
                return True
            else:
                # Fallback deletion
                tier_data = self.collections[tier]
                for i, metadata in enumerate(tier_data['metadata']):
                    if metadata.get('document_id') == document_id:
                        del tier_data['documents'][i]
                        del tier_data['embeddings'][i]
                        del tier_data['metadata'][i]
                        logger.info(f"Deleted document {document_id} from fallback {tier}")
                        return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from {tier}: {e}")
            return False

    def clear_tier(self, tier: str) -> bool:
        """Clear all documents from a specific tier."""
        try:
            if tier not in self.tier_names:
                raise ValueError(f"Invalid tier: {tier}")
            
            if CHROMADB_AVAILABLE and self.client:
                # Delete and recreate collection
                collection_name = self.tier_names[tier]
                self.client.delete_collection(collection_name)
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"tier": tier, "created_at": datetime.now().isoformat()}
                )
                self.collections[tier] = collection
                logger.info(f"Cleared {tier} collection")
                return True
            else:
                # Clear fallback storage
                self.collections[tier] = {'documents': [], 'embeddings': [], 'metadata': []}
                logger.info(f"Cleared fallback {tier} storage")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear {tier}: {e}")
            return False

    def reset_all_tiers(self) -> bool:
        """Reset all tiers (clear all data)."""
        try:
            success = True
            for tier in self.tier_names.keys():
                if not self.clear_tier(tier):
                    success = False
            
            if success:
                logger.info("Successfully reset all tiers")
            else:
                logger.warning("Some tiers failed to reset")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reset all tiers: {e}")
            return False

    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)

    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches the provided filters."""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def export_tier_data(self, tier: str, output_path: str) -> bool:
        """Export tier data to JSON file."""
        try:
            if tier not in self.tier_names:
                raise ValueError(f"Invalid tier: {tier}")
            
            export_data = {
                'tier': tier,
                'exported_at': datetime.now().isoformat(),
                'documents': []
            }
            
            if CHROMADB_AVAILABLE and self.client:
                collection = self.collections[tier]
                # Get all documents
                results = collection.get()
                
                for i in range(len(results['documents'])):
                    export_data['documents'].append({
                        'id': results['ids'][i],
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    })
            else:
                tier_data = self.collections[tier]
                for i, doc in enumerate(tier_data['documents']):
                    export_data['documents'].append({
                        'id': tier_data['metadata'][i].get('document_id', f'doc_{i}'),
                        'content': doc,
                        'metadata': tier_data['metadata'][i]
                    })
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {tier} data to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export {tier} data: {e}")
            return False

    def import_tier_data(self, tier: str, input_path: str) -> bool:
        """Import tier data from JSON file."""
        try:
            if tier not in self.tier_names:
                raise ValueError(f"Invalid tier: {tier}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if import_data.get('tier') != tier:
                logger.warning(f"Tier mismatch: expected {tier}, got {import_data.get('tier')}")
            
            success_count = 0
            for doc_data in import_data.get('documents', []):
                if self.add_document(
                    tier=tier,
                    document_id=doc_data['id'],
                    content=doc_data['content'],
                    metadata=doc_data.get('metadata', {})
                ):
                    success_count += 1
            
            logger.info(f"Imported {success_count} documents to {tier}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to import {tier} data: {e}")
            return False

    def process_document(self, file_path: str, document_type: str, metadata: Optional[Dict[str, Any]] = None, grant_id: Optional[str] = None, **kwargs) -> bool:
        """
        Process and add a document to the appropriate tier based on document_type.
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (grant_documents, organization_documents, application_outlines)
            metadata: Optional metadata dictionary
            grant_id: Optional grant ID for association
            **kwargs: Additional keyword arguments for compatibility
            
        Returns:
            bool: Success status
        """
        try:
            # Read file content
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Empty file: {file_path}")
                return False
            
            # Map document type to tier
            tier_mapping = {
                'grant_documents': 'grant_documents',
                'organization_documents': 'organization_documents', 
                'application_outlines': 'application_outlines'
            }
            
            tier = tier_mapping.get(document_type)
            if not tier:
                logger.error(f"Invalid document type: {document_type}")
                return False
            
            # Generate document ID from filename
            filename = os.path.basename(file_path)
            document_id = f"{tier}_{filename}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata.update({
                'filename': filename,
                'file_path': file_path,
                'document_type': document_type,
                'processed_at': datetime.now().isoformat()
            })
            
            # Add to appropriate tier
            success = self.add_document(tier, document_id, content, doc_metadata)
            
            if success:
                logger.info(f"Successfully processed document: {filename} -> {tier}")
            else:
                logger.error(f"Failed to process document: {filename}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return False

    def search_documents(self, query: str, tier: Optional[str] = None, limit: int = 5, document_type: Optional[str] = None, grant_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for documents across tiers or within a specific tier.
        
        Args:
            query: Search query string
            tier: Optional tier to search (if None, searches all tiers)
            limit: Maximum number of results to return
            document_type: Optional document type filter (used as tier if tier is None)
            grant_id: Optional grant ID filter
            **kwargs: Additional keyword arguments for compatibility
            
        Returns:
            List of matching documents with metadata and scores
        """
        try:
            if tier:
                # Search specific tier
                if tier not in self.tier_names:
                    logger.error(f"Invalid tier: {tier}")
                    return []
                
                results = self.query_tier(tier, query, limit)
                return results
            else:
                # Search all tiers
                all_results = []
                results_per_tier = max(1, limit // 3)  # Distribute results across tiers
                
                for tier_name in self.tier_names.keys():
                    tier_results = self.query_tier(tier_name, query, results_per_tier)
                    all_results.extend(tier_results)
                
                # Sort by relevance (distance/similarity) and limit
                if all_results:
                    # Sort by similarity score (higher is better) or distance (lower is better)
                    if 'similarity' in all_results[0]:
                        all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                    elif 'distance' in all_results[0]:
                        all_results.sort(key=lambda x: x.get('distance', float('inf')))
                
                return all_results[:limit]
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
