import chromadb
from chromadb.utils import embedding_functions
import os
import uuid
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreeTierVectorDatabase:
    """
    Enhanced vector database system supporting three-tier document management:
    - Tier 1: Grant Requirements & Context
    - Tier 2: Organization Documents & History  
    - Tier 3: Proposal Strategy & Outlines
    """
    
    def __init__(self, persist_directory: str = "chromadb_storage"):
        """Initialize the three-tier vector database system"""
        self.persist_directory = persist_directory
        
        # Ensure the directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Initialize collections for each tier
        self.tier1_collections = {}  # Grant requirements by application_id
        self.tier2_collections = {}  # Organization documents by application_id
        self.tier3_collections = {}  # Proposal strategy by application_id
        
        logger.info(f"ThreeTierVectorDatabase initialized with persistence at: {persist_directory}")
    
    def create_grant_application(self, application_id: str, application_name: str) -> Dict[str, str]:
        """
        Create a new grant application with all three tier collections
        
        Args:
            application_id: Unique identifier for the grant application
            application_name: Human-readable name for the application
            
        Returns:
            Dictionary with collection names for each tier
        """
        try:
            # Create collection names
            tier1_name = f"tier1_requirements_{application_id}"
            tier2_name = f"tier2_organization_{application_id}"
            tier3_name = f"tier3_proposal_{application_id}"
            
            # Create collections with metadata
            metadata = {
                "application_id": application_id,
                "application_name": application_name,
                "created_at": datetime.now().isoformat()
            }
            
            tier1_collection = self.client.create_collection(
                name=tier1_name,
                embedding_function=self.embedding_function,
                metadata={**metadata, "tier": "1", "type": "requirements"}
            )
            
            tier2_collection = self.client.create_collection(
                name=tier2_name,
                embedding_function=self.embedding_function,
                metadata={**metadata, "tier": "2", "type": "organization"}
            )
            
            tier3_collection = self.client.create_collection(
                name=tier3_name,
                embedding_function=self.embedding_function,
                metadata={**metadata, "tier": "3", "type": "proposal"}
            )
            
            # Store collections
            self.tier1_collections[application_id] = tier1_collection
            self.tier2_collections[application_id] = tier2_collection
            self.tier3_collections[application_id] = tier3_collection
            
            logger.info(f"Created grant application: {application_name} ({application_id})")
            
            return {
                "tier1_collection": tier1_name,
                "tier2_collection": tier2_name,
                "tier3_collection": tier3_name,
                "application_id": application_id,
                "application_name": application_name
            }
            
        except Exception as e:
            logger.error(f"Error creating grant application {application_id}: {str(e)}")
            raise
    
    def load_grant_application(self, application_id: str) -> bool:
        """
        Load an existing grant application's collections
        
        Args:
            application_id: Unique identifier for the grant application
            
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            tier1_name = f"tier1_requirements_{application_id}"
            tier2_name = f"tier2_organization_{application_id}"
            tier3_name = f"tier3_proposal_{application_id}"
            
            # Load collections
            self.tier1_collections[application_id] = self.client.get_collection(tier1_name)
            self.tier2_collections[application_id] = self.client.get_collection(tier2_name)
            self.tier3_collections[application_id] = self.client.get_collection(tier3_name)
            
            logger.info(f"Loaded grant application: {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading grant application {application_id}: {str(e)}")
            return False
    
    def add_document_to_tier(self, application_id: str, tier: int, document_content: str, 
                           document_metadata: Dict[str, Any]) -> str:
        """
        Add a document to a specific tier
        
        Args:
            application_id: Grant application identifier
            tier: Tier number (1, 2, or 3)
            document_content: Text content of the document
            document_metadata: Metadata about the document
            
        Returns:
            Document ID
        """
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Enhanced metadata
            enhanced_metadata = {
                **document_metadata,
                "application_id": application_id,
                "tier": str(tier),
                "uploaded_at": datetime.now().isoformat(),
                "document_id": doc_id
            }
            
            # Get the appropriate collection
            if tier == 1:
                if application_id not in self.tier1_collections:
                    self.load_grant_application(application_id)
                collection = self.tier1_collections[application_id]
            elif tier == 2:
                if application_id not in self.tier2_collections:
                    self.load_grant_application(application_id)
                collection = self.tier2_collections[application_id]
            elif tier == 3:
                if application_id not in self.tier3_collections:
                    self.load_grant_application(application_id)
                collection = self.tier3_collections[application_id]
            else:
                raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3")
            
            # Split content into chunks for better retrieval
            chunks = self._split_content(document_content)
            
            # Add all chunks with metadata
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                chunk_metadata = {
                    **enhanced_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_id": chunk_id
                }
                
                collection.add(
                    documents=[chunk],
                    metadatas=[chunk_metadata],
                    ids=[chunk_id]
                )
            
            logger.info(f"Added document to Tier {tier}: {doc_id} ({len(chunks)} chunks)")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document to tier {tier}: {str(e)}")
            raise
    
    def query_tier(self, application_id: str, tier: int, query: str, 
                   n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Query a specific tier for relevant content
        
        Args:
            application_id: Grant application identifier
            tier: Tier number (1, 2, or 3)
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            # Get the appropriate collection
            if tier == 1:
                if application_id not in self.tier1_collections:
                    self.load_grant_application(application_id)
                collection = self.tier1_collections[application_id]
            elif tier == 2:
                if application_id not in self.tier2_collections:
                    self.load_grant_application(application_id)
                collection = self.tier2_collections[application_id]
            elif tier == 3:
                if application_id not in self.tier3_collections:
                    self.load_grant_application(application_id)
                collection = self.tier3_collections[application_id]
            else:
                raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3")
            
            # Query the collection
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            logger.info(f"Tier {tier} query returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying tier {tier}: {str(e)}")
            return []
    
    def query_all_tiers(self, application_id: str, query: str, 
                       n_results_per_tier: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query all three tiers and return organized results
        
        Args:
            application_id: Grant application identifier
            query: Search query
            n_results_per_tier: Number of results per tier
            
        Returns:
            Dictionary with results from each tier
        """
        try:
            results = {
                'tier1_requirements': self.query_tier(application_id, 1, query, n_results_per_tier),
                'tier2_organization': self.query_tier(application_id, 2, query, n_results_per_tier),
                'tier3_proposal': self.query_tier(application_id, 3, query, n_results_per_tier)
            }
            
            logger.info(f"Cross-tier query completed for application {application_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error in cross-tier query: {str(e)}")
            return {'tier1_requirements': [], 'tier2_organization': [], 'tier3_proposal': []}
    
    def get_tier_summary(self, application_id: str, tier: int) -> Dict[str, Any]:
        """
        Get a summary of documents in a specific tier
        
        Args:
            application_id: Grant application identifier
            tier: Tier number (1, 2, or 3)
            
        Returns:
            Summary information about the tier
        """
        try:
            # Get the appropriate collection
            if tier == 1:
                if application_id not in self.tier1_collections:
                    self.load_grant_application(application_id)
                collection = self.tier1_collections[application_id]
            elif tier == 2:
                if application_id not in self.tier2_collections:
                    self.load_grant_application(application_id)
                collection = self.tier2_collections[application_id]
            elif tier == 3:
                if application_id not in self.tier3_collections:
                    self.load_grant_application(application_id)
                collection = self.tier3_collections[application_id]
            else:
                raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3")
            
            # Get collection count and metadata
            count = collection.count()
            
            # Get some sample documents to analyze types
            if count > 0:
                sample_results = collection.peek(limit=min(10, count))
                document_types = set()
                for metadata in sample_results['metadatas']:
                    if 'document_type' in metadata:
                        document_types.add(metadata['document_type'])
            else:
                document_types = set()
            
            return {
                'tier': tier,
                'document_count': count,
                'document_types': list(document_types),
                'collection_name': collection.name
            }
            
        except Exception as e:
            logger.error(f"Error getting tier {tier} summary: {str(e)}")
            return {'tier': tier, 'document_count': 0, 'document_types': [], 'collection_name': None}
    
    def get_application_summary(self, application_id: str) -> Dict[str, Any]:
        """
        Get a complete summary of all tiers for an application
        
        Args:
            application_id: Grant application identifier
            
        Returns:
            Complete summary of the application
        """
        try:
            summary = {
                'application_id': application_id,
                'tiers': {
                    'tier1_requirements': self.get_tier_summary(application_id, 1),
                    'tier2_organization': self.get_tier_summary(application_id, 2),
                    'tier3_proposal': self.get_tier_summary(application_id, 3)
                }
            }
            
            # Calculate totals
            total_documents = sum(tier['document_count'] for tier in summary['tiers'].values())
            summary['total_documents'] = total_documents
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting application summary: {str(e)}")
            return {'application_id': application_id, 'error': str(e)}
    
    def list_applications(self) -> List[Dict[str, str]]:
        """
        List all grant applications in the database
        
        Returns:
            List of application information
        """
        try:
            collections = self.client.list_collections()
            applications = {}
            
            for collection in collections:
                if collection.name.startswith('tier1_requirements_'):
                    app_id = collection.name.replace('tier1_requirements_', '')
                    metadata = collection.metadata or {}
                    applications[app_id] = {
                        'application_id': app_id,
                        'application_name': metadata.get('application_name', 'Unknown'),
                        'created_at': metadata.get('created_at', 'Unknown')
                    }
            
            return list(applications.values())
            
        except Exception as e:
            logger.error(f"Error listing applications: {str(e)}")
            return []
    
    def delete_application(self, application_id: str) -> bool:
        """
        Delete a grant application and all its tiers
        
        Args:
            application_id: Grant application identifier
            
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            tier1_name = f"tier1_requirements_{application_id}"
            tier2_name = f"tier2_organization_{application_id}"
            tier3_name = f"tier3_proposal_{application_id}"
            
            # Delete collections
            try:
                self.client.delete_collection(tier1_name)
            except:
                pass
            
            try:
                self.client.delete_collection(tier2_name)
            except:
                pass
            
            try:
                self.client.delete_collection(tier3_name)
            except:
                pass
            
            # Remove from memory
            if application_id in self.tier1_collections:
                del self.tier1_collections[application_id]
            if application_id in self.tier2_collections:
                del self.tier2_collections[application_id]
            if application_id in self.tier3_collections:
                del self.tier3_collections[application_id]
            
            logger.info(f"Deleted grant application: {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting application {application_id}: {str(e)}")
            return False
    
    def _split_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split content into overlapping chunks for better retrieval
        
        Args:
            content: Text content to split
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of content chunks
        """
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at a sentence boundary
            if end < len(content):
                # Look for sentence ending within the last 100 characters
                for i in range(end - 100, end):
                    if i > start and content[i] in '.!?':
                        end = i + 1
                        break
            
            chunks.append(content[start:end])
            start = end - overlap
            
            if start >= len(content):
                break
        
        return chunks

# Global instance
vector_db = ThreeTierVectorDatabase()
