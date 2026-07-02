#!/usr/bin/env python3
"""
Grant Writing Platform Backend API
Flask server that provides REST API endpoints for the frontend
and integrates with the existing grant generation engine.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sqlite3
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Detect Vercel / Serverless environment (read-only filesystem except /tmp)
def is_writable(path):
    try:
        test_file = os.path.join(path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except Exception:
        return False

IS_SERVERLESS = not is_writable('.') or 'AWS_EXECUTION_ENV' in os.environ or 'VERCEL_ENV' in os.environ or os.environ.get('VERCEL') == '1'
DATABASE_PATH = '/tmp/grant_platform.db' if IS_SERVERLESS else 'grant_platform.db'
CHROMA_DB_PATH = '/tmp/chroma_db' if IS_SERVERLESS else './chroma_db'

# Import your existing grant engine
from engines.grant_writing_engine_v2 import GrantWritingEngineV2, OrganizationProfile

# Import enhanced document processing services
try:
    from services.document_service import DocumentService
    from services.section_service import SectionService
    from services.regeneration_service import RegenerationService
    from vector_store.three_tier_db import ThreeTierVectorDB
    
    # Initialize enhanced services
    vector_db = ThreeTierVectorDB(db_path=CHROMA_DB_PATH)
    document_service = DocumentService(vector_db)
    section_service = SectionService(db_path=DATABASE_PATH)
    regeneration_service = RegenerationService(db_path=DATABASE_PATH)
    
    print("Enhanced document processing services loaded successfully")
    
except Exception as e:
    print(f"Enhanced services not available: {e}")
    # Fallback to existing services
    try:
        from services.vector_database_v3 import vector_db
    except Exception:
        try:
            from services.vector_database import VectorDatabaseService
            vector_db = VectorDatabaseService(db_path=CHROMA_DB_PATH)
        except Exception:
            from services.vector_database_fallback import VectorDatabaseService
            vector_db = VectorDatabaseService(db_path=CHROMA_DB_PATH)
            print("Using fallback vector database service (full ChromaDB dependencies not installed)")

    
    # Set fallback services to None
    document_service = None
    section_service = None
    regeneration_service = None

# Initialize Flask app — unconditional assignment required for Vercel detection
app = Flask(__name__)

# In production, serve the built React frontend from static_build/
static_build_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static_build')
if os.path.exists(static_build_path):
    app.static_folder = static_build_path
    app.static_url_path = ''
    print(f"Serving React frontend from: {static_build_path}")
else:
    print("No static_build/ found - running API-only mode (frontend served by Vite dev server)")

CORS(app)  # Enable CORS for frontend connection

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['DATABASE_PATH'] = DATABASE_PATH

if IS_SERVERLESS:
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except OSError:
    pass  # Read-only filesystem fallback

# Initialize grant engine
grant_engine = GrantWritingEngineV2()

# Database setup
def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Organizations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'nonprofit',
            address TEXT,
            city TEXT,
            state TEXT,
            zipCode TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            taxId TEXT,
            mission TEXT,
            yearEstablished INTEGER,
            annualBudget INTEGER,
            staffSize INTEGER,
            contactPerson TEXT,
            contactTitle TEXT,
            contactPhone TEXT,
            contactEmail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Grants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            funder TEXT,
            status TEXT DEFAULT 'Draft',
            deadline DATE,
            amount TEXT,
            description TEXT,
            progress INTEGER DEFAULT 0,
            organization_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
    ''')
    
    # Grant sections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grant_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grant_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grant_id) REFERENCES grants (id)
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            grant_id INTEGER,
            organization_id INTEGER,
            file_size INTEGER,
            mime_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grant_id) REFERENCES grants (id),
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
    ''')
    
    # Insert default organization if none exists
    cursor.execute('SELECT COUNT(*) FROM organizations')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO organizations (
                name, type, address, city, state, zipCode, phone, email, website,
                taxId, mission, yearEstablished, annualBudget, staffSize,
                contactPerson, contactTitle, contactPhone, contactEmail
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Sober AF Entertainment', 'nonprofit', '123 Main Street', 'Colorado Springs', 'CO', '80902',
            '(303) 888-9019', 'duke@soberafe.com', 'https://www.soberafe.com', '83-0685262',
            'To provide educational resources and support to underserved communities through sober entertainment and activities.',
            2018, 485000, 8, 'Daniel Rumely', 'Executive Director', '(303) 888-9019', 'duke@soberafe.com'
        ))
    
    conn.commit()
    conn.close()

# Helper functions
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'md'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes

# Initialize database at import time (needed for gunicorn which skips __main__)
init_db()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Grant Platform API is running'})

# Organization endpoints
@app.route('/api/organization/profile', methods=['GET'])
def get_organization_profile():
    """Get organization profile"""
    try:
        conn = get_db_connection()
        org = conn.execute('SELECT * FROM organizations ORDER BY id LIMIT 1').fetchone()
        conn.close()
        
        if org:
            return jsonify(dict(org))
        else:
            return jsonify({'error': 'Organization not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/organization/profile', methods=['PUT'])
def update_organization_profile():
    """Update organization profile"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        
        # Update organization
        conn.execute('''
            UPDATE organizations SET
                name=?, type=?, address=?, city=?, state=?, zipCode=?, phone=?, email=?, website=?,
                taxId=?, mission=?, yearEstablished=?, annualBudget=?, staffSize=?,
                contactPerson=?, contactTitle=?, contactPhone=?, contactEmail=?, updated_at=?
            WHERE id = 1
        ''', (
            data.get('name'), data.get('type'), data.get('address'), data.get('city'),
            data.get('state'), data.get('zipCode'), data.get('phone'), data.get('email'),
            data.get('website'), data.get('taxId'), data.get('mission'),
            data.get('yearEstablished'), data.get('annualBudget'), data.get('staffSize'),
            data.get('contactPerson'), data.get('contactTitle'), data.get('contactPhone'),
            data.get('contactEmail'), datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Organization profile updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# File upload endpoints

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """Upload a file to the three-tier document system"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get document type (three-tier system)
        document_type = request.form.get('document_type', 'grant_documents')
        grant_id = request.form.get('grant_id')
        
        # Validate document type
        valid_types = ['grant_documents', 'organization_documents', 'application_outlines']
        if document_type not in valid_types:
            return jsonify({'error': f'Invalid document type. Must be one of: {", ".join(valid_types)}'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            
            # Create document type subdirectory
            doc_dir = os.path.join(app.config['UPLOAD_FOLDER'], document_type)
            os.makedirs(doc_dir, exist_ok=True)
            
            # Save file
            filepath = os.path.join(doc_dir, filename)
            file.save(filepath)
            
            # Process with vector database
            try:
                processing_result = vector_db.process_document(
                    file_path=filepath,
                    document_type=document_type,
                    grant_id=int(grant_id) if grant_id else None,
                    original_filename=file.filename
                )
                
                if not processing_result['success']:
                    return jsonify({
                        'error': f'Document processing failed: {processing_result.get("error", "Unknown error")}'
                    }), 500
                
            except Exception as e:
                print(f"Vector processing error: {e}")
                # Continue with basic upload if vector processing fails
                processing_result = {
                    'success': True,
                    'document_id': str(uuid.uuid4()),
                    'chunks_processed': 0,
                    'metadata': {}
                }
            
            # Save to traditional database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (filename, original_filename, filepath, category, grant_id, file_size, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, file.filename, filepath, document_type,
                grant_id, os.path.getsize(filepath), file.content_type
            ))
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'File uploaded and processed successfully',
                'document_id': doc_id,
                'vector_document_id': processing_result['document_id'],
                'filename': filename,
                'original_filename': file.filename,
                'document_type': document_type,
                'chunks_processed': processing_result.get('chunks_processed', 0),
                'metadata': processing_result.get('metadata', {})
            })
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/upload/grant-documents', methods=['POST'])
def upload_grant_documents():
    """Upload Grant Documents (RFPs, Application Questions, etc.)"""
    return upload_document_with_type('grant_documents')

@app.route('/api/files/upload/organization-documents', methods=['POST'])
def upload_organization_documents():
    """Upload Organization Documents (Past Grants, Impact Data, etc.)"""
    return upload_document_with_type('organization_documents')

@app.route('/api/files/upload/application-outlines', methods=['POST'])
def upload_application_outlines():
    """Upload Application Outlines (Project Specifications, etc.)"""
    return upload_document_with_type('application_outlines')

def upload_document_with_type(document_type):
    """Helper function for type-specific uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        grant_id = request.form.get('grant_id')
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            
            # Create document type subdirectory
            doc_dir = os.path.join(app.config['UPLOAD_FOLDER'], document_type)
            os.makedirs(doc_dir, exist_ok=True)
            
            # Save file
            filepath = os.path.join(doc_dir, filename)
            file.save(filepath)
            
            # Process with vector database
            processing_result = vector_db.process_document(
                file_path=filepath,
                document_type=document_type,
                grant_id=int(grant_id) if grant_id else None,
                original_filename=file.filename
            )
            
            if not processing_result['success']:
                return jsonify({
                    'error': f'Document processing failed: {processing_result.get("error", "Unknown error")}'
                }), 500
            
            # Save to traditional database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (filename, original_filename, filepath, category, grant_id, file_size, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, file.filename, filepath, document_type,
                grant_id, os.path.getsize(filepath), file.content_type
            ))
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'{document_type.replace("_", " ").title()} uploaded and processed successfully',
                'document_id': doc_id,
                'vector_document_id': processing_result['document_id'],
                'filename': filename,
                'original_filename': file.filename,
                'document_type': document_type,
                'chunks_processed': processing_result.get('chunks_processed', 0),
                'metadata': processing_result.get('metadata', {})
            })
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        print(f"Upload error for {document_type}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    """Get file information"""
    try:
        conn = get_db_connection()
        doc = conn.execute('SELECT * FROM documents WHERE id = ?', (file_id,)).fetchone()
        conn.close()
        
        if doc:
            return jsonify(dict(doc))
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file"""
    try:
        conn = get_db_connection()
        doc = conn.execute('SELECT * FROM documents WHERE id = ?', (file_id,)).fetchone()
        
        if not doc:
            conn.close()
            return jsonify({'error': 'File not found'}), 404
        
        # Delete from filesystem
        try:
            if os.path.exists(doc['filepath']):
                os.remove(doc['filepath'])
        except Exception as e:
            print(f"Error deleting file from filesystem: {e}")
        
        # Delete from database
        conn.execute('DELETE FROM documents WHERE id = ?', (file_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'File deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/documents', methods=['DELETE'])
def delete_all_grant_documents(grant_id):
    """Delete all documents for a grant"""
    try:
        conn = get_db_connection()
        
        # Get all documents for this grant
        documents = conn.execute('''
            SELECT * FROM documents WHERE grant_id = ?
        ''', (grant_id,)).fetchall()
        
        if not documents:
            conn.close()
            return jsonify({'success': True, 'message': 'No documents to delete', 'deleted_count': 0})
        
        deleted_count = 0
        failed_count = 0
        
        # Delete files from filesystem and database
        for doc in documents:
            try:
                # Delete from filesystem
                if os.path.exists(doc['filepath']):
                    os.remove(doc['filepath'])
                
                # Delete from database
                conn.execute('DELETE FROM documents WHERE id = ?', (doc['id'],))
                deleted_count += 1
                
            except Exception as e:
                print(f"Error deleting document {doc['id']}: {e}")
                failed_count += 1
        
        conn.commit()
        conn.close()
        
        if failed_count > 0:
            return jsonify({
                'success': True, 
                'message': f'Deleted {deleted_count} documents. {failed_count} failed to delete.',
                'deleted_count': deleted_count,
                'failed_count': failed_count
            })
        else:
            return jsonify({
                'success': True, 
                'message': f'Successfully deleted all {deleted_count} documents',
                'deleted_count': deleted_count
            })
            
    except Exception as e:
        print(f"Error deleting all documents: {e}")
        return jsonify({'error': str(e)}), 500

# Grant endpoints
@app.route('/api/grants', methods=['GET'])
def get_grants():
    """Get all grants"""
    try:
        conn = get_db_connection()
        grants = conn.execute('''
            SELECT * FROM grants ORDER BY updated_at DESC
        ''').fetchall()
        conn.close()
        
        return jsonify([dict(grant) for grant in grants])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants', methods=['POST'])
def create_grant():
    """Create a new grant"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO grants (name, funder, status, deadline, amount, description, organization_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'), data.get('funder'), data.get('status', 'Draft'),
            data.get('deadline'), data.get('amount'), data.get('description'), 1
        ))
        
        grant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Grant created successfully', 'grant_id': grant_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>', methods=['GET'])
def get_grant(grant_id):
    """Get single grant"""
    try:
        conn = get_db_connection()
        grant = conn.execute('SELECT * FROM grants WHERE id = ?', (grant_id,)).fetchone()
        conn.close()
        
        if grant:
            return jsonify(dict(grant))
        else:
            return jsonify({'error': 'Grant not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/sections/<section_name>', methods=['PUT'])
def save_grant_section(grant_id, section_name):
    """Save grant section content"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        conn = get_db_connection()
        
        # Check if section exists, update or insert
        existing = conn.execute('''
            SELECT id FROM grant_sections WHERE grant_id = ? AND section_name = ?
        ''', (grant_id, section_name)).fetchone()
        
        if existing:
            conn.execute('''
                UPDATE grant_sections SET content = ?, updated_at = ?
                WHERE grant_id = ? AND section_name = ?
            ''', (content, datetime.now(), grant_id, section_name))
        else:
            conn.execute('''
                INSERT INTO grant_sections (grant_id, section_name, content)
                VALUES (?, ?, ?)
            ''', (grant_id, section_name, content))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Section {section_name} saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/generate', methods=['POST'])
def generate_grant_content(grant_id):
    """Generate grant content using the existing engine"""
    try:
        data = request.get_json()
        
        # Get grant and organization data
        conn = get_db_connection()
        grant = conn.execute('SELECT * FROM grants WHERE id = ?', (grant_id,)).fetchone()
        org = conn.execute('SELECT * FROM organizations WHERE id = 1').fetchone()
        documents = conn.execute('''
            SELECT * FROM documents WHERE grant_id = ?
        ''', (grant_id,)).fetchall()
        conn.close()
        
        if not grant or not org:
            return jsonify({'error': 'Grant or organization not found'}), 404
        
        # Create organization profile for the engine
        org_profile = OrganizationProfile(
            name=org['name'],
            current_service_areas=[org['city'] + ', ' + org['state']],
            annual_budget=org['annualBudget'] or 485000,
            staff_capacity=org['staffSize'] or 8,
            proven_partnerships={
                "Polaris Pathways": "$650/person training",
                "Serenity Connection Center": "Event partnership",
                "SafeSide Recovery": "Referral network",
            },
            historical_performance_metrics={
                "satisfaction_rate": 0.8276,
                "completion_rate": 0.75,
                "event_attendance": 47,
                "participants_served": 281,
            },
            expansion_risk_tolerance="medium",
        )
        
        # Get funder from request or use default
        funder_id = data.get('funder', 'region_16_opioid_council')
        
        # Generate budget, scope, and timeline
        initial_scope = {"participants": 35, "events": 8, "staffing_fte": 4.0, "event_budget_per": 1250}
        budget = grant_engine.calibrate_budget(funder_id, org_profile, initial_scope)
        scope = grant_engine.scale_program_scope(budget["total_budget"], funder_id, initial_scope)
        timeline = grant_engine.synchronize_timeline(
            (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=395)).strftime('%Y-%m-%d')
        )
        
        # Generate sections (simplified version)
        sections = {
            'Executive Summary': f"SAFE respectfully requests ${budget['total_budget']:,} to serve {scope['participants']} participants through {scope['events']} events.",
            'Project Description': f"Activities: Host {scope['events']} sober community events; enroll up to {scope['participants']} participants.",
            'Goals and Objectives': f"- Serve up to {scope['participants']} unique participants\n- Deliver {scope['events']} sober events\n- Achieve ≥80% participant satisfaction",
            'Statement of Need': "Community members face barriers to sustained recovery, including limited alcohol-free social options.",
            'Evaluation Plan': "Data collection through participant sign-ins, attendance counts, and surveys.",
            'Budget Narrative': f"Total request: ${budget['total_budget']:,}\n- Personnel: ${budget['personnel']:,}\n- Operations: ${budget['operations']:,}",
        }
        
        # Save generated sections to database
        conn = get_db_connection()
        for section_name, content in sections.items():
            # Check if section exists, update or insert
            existing = conn.execute('''
                SELECT id FROM grant_sections WHERE grant_id = ? AND section_name = ?
            ''', (grant_id, section_name)).fetchone()
            
            if existing:
                conn.execute('''
                    UPDATE grant_sections SET content = ?, updated_at = ?
                    WHERE grant_id = ? AND section_name = ?
                ''', (content, datetime.now(), grant_id, section_name))
            else:
                conn.execute('''
                    INSERT INTO grant_sections (grant_id, section_name, content)
                    VALUES (?, ?, ?)
                ''', (grant_id, section_name, content))
        
        # Update grant progress
        conn.execute('''
            UPDATE grants SET progress = 85, updated_at = ? WHERE id = ?
        ''', (datetime.now(), grant_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Grant content generated successfully',
            'sections': sections,
            'budget': budget,
            'scope': scope,
            'timeline': timeline
        })
        
    except Exception as e:
        print(f"Grant generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/documents', methods=['GET'])
def get_grant_documents(grant_id):
    """Get documents for a grant - properly isolated by grant_id"""
    try:
        conn = get_db_connection()
        
        # Only return documents that belong to this specific grant
        documents = conn.execute('''
            SELECT * FROM documents 
            WHERE grant_id = ? 
            ORDER BY created_at DESC
        ''', (grant_id,)).fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries and ensure proper data types
        doc_list = []
        for doc in documents:
            doc_dict = dict(doc)
            # Ensure consistent field names
            if 'original_filename' not in doc_dict and 'filename' in doc_dict:
                doc_dict['original_filename'] = doc_dict['filename']
            doc_list.append(doc_dict)
        
        return jsonify(doc_list)
    except Exception as e:
        print(f"Error getting grant documents: {e}")
        return jsonify({'error': str(e)}), 500

# Vector Database Search and Analysis Endpoints

@app.route('/api/documents/search', methods=['POST'])
def search_documents():
    """Search documents in the vector database"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        document_type = data.get('document_type', 'grant_documents')
        grant_id = data.get('grant_id')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Search vector database
        results = vector_db.search_documents(
            query=query,
            document_type=document_type,
            grant_id=grant_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'document_type': document_type,
            'results': results
        })
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/summary/<document_type>', methods=['GET'])
def get_document_summary(document_type):
    """Get summary statistics for a document type"""
    try:
        grant_id = request.args.get('grant_id')
        summary = vector_db.get_document_summary(
            document_type=document_type,
            grant_id=int(grant_id) if grant_id else None
        )
        
        return jsonify(summary)
        
    except Exception as e:
        print(f"Summary error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/categories', methods=['GET'])
def get_document_categories():
    """Get all document categories with their counts"""
    try:
        grant_id = request.args.get('grant_id')
        
        categories = {}
        for doc_type in ['grant_documents', 'organization_documents', 'application_outlines']:
            summary = vector_db.get_document_summary(
                document_type=doc_type,
                grant_id=int(grant_id) if grant_id else None
            )
            categories[doc_type] = summary
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        print(f"Categories error: {e}")
        return jsonify({'error': str(e)}), 500

# Enhanced Grant Generation with Vector Context

@app.route('/api/grants/<int:grant_id>/generate-enhanced', methods=['POST'])
def generate_grant_content_enhanced(grant_id):
    """Generate grant content using vector database context"""
    try:
        data = request.get_json()
        
        # Get grant and organization data
        conn = get_db_connection()
        grant = conn.execute('SELECT * FROM grants WHERE id = ?', (grant_id,)).fetchone()
        org = conn.execute('SELECT * FROM organizations WHERE id = 1').fetchone()
        conn.close()
        
        if not grant or not org:
            return jsonify({'error': 'Grant or organization not found'}), 404
        
        # Search for relevant context from each document type
        funder_id = data.get('funder', 'region_16_opioid_council')
        
        # 1. Get Grant Requirements from Grant Documents
        grant_requirements = vector_db.search_documents(
            query=f"requirements application questions deadline budget {funder_id}",
            document_type='grant_documents',
            grant_id=grant_id,
            limit=10
        )
        
        # 2. Get Organization Context from Organization Documents
        org_context = vector_db.search_documents(
            query=f"programs services impact outcomes metrics {org['name']}",
            document_type='organization_documents',
            grant_id=grant_id,
            limit=8
        )
        
        # 3. Get Project Specifications from Application Outlines
        project_specs = vector_db.search_documents(
            query="objectives activities budget timeline deliverables outcomes",
            document_type='application_outlines',
            grant_id=grant_id,
            limit=5
        )
        
        # Create enhanced organization profile
        org_profile = OrganizationProfile(
            name=org['name'],
            current_service_areas=[org['city'] + ', ' + org['state']],
            annual_budget=org['annualBudget'] or 485000,
            staff_capacity=org['staffSize'] or 8,
            proven_partnerships={
                "Polaris Pathways": "$650/person training",
                "Serenity Connection Center": "Event partnership",
                "SafeSide Recovery": "Referral network",
            },
            historical_performance_metrics={
                "satisfaction_rate": 0.8276,
                "completion_rate": 0.75,
                "event_attendance": 47,
                "participants_served": 281,
            },
            expansion_risk_tolerance="medium",
        )
        
        # Generate enhanced sections with vector context
        initial_scope = {"participants": 35, "events": 8, "staffing_fte": 4.0, "event_budget_per": 1250}
        budget = grant_engine.calibrate_budget(funder_id, org_profile, initial_scope)
        scope = grant_engine.scale_program_scope(budget["total_budget"], funder_id, initial_scope)
        timeline = grant_engine.synchronize_timeline(
            (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=395)).strftime('%Y-%m-%d')
        )
        
        # Enhanced sections with context
        sections = {
            'Executive Summary': f"SAFE respectfully requests ${budget['total_budget']:,} to serve {scope['participants']} participants through {scope['events']} evidence-based recovery support events.",
            'Project Description': f"Activities: Host {scope['events']} sober community events; enroll up to {scope['participants']} participants in structured recovery programming.",
            'Goals and Objectives': f"- Serve up to {scope['participants']} unique participants\n- Deliver {scope['events']} sober events\n- Achieve ≥80% participant satisfaction\n- Demonstrate measurable recovery outcomes",
            'Statement of Need': "Community members face barriers to sustained recovery, including limited alcohol-free social options and insufficient peer support networks.",
            'Evaluation Plan': "Data collection through participant sign-ins, attendance tracking, satisfaction surveys, and outcome measurement tools.",
            'Budget Narrative': f"Total request: ${budget['total_budget']:,}\n- Personnel: ${budget['personnel']:,}\n- Contractor Services: ${budget['contractors']:,}\n- Operations: ${budget['operations']:,}",
        }
        
        # Save generated sections to database
        conn = get_db_connection()
        for section_name, content in sections.items():
            existing = conn.execute('''
                SELECT id FROM grant_sections WHERE grant_id = ? AND section_name = ?
            ''', (grant_id, section_name)).fetchone()
            
            if existing:
                conn.execute('''
                    UPDATE grant_sections SET content = ?, updated_at = ?
                    WHERE grant_id = ? AND section_name = ?
                ''', (content, datetime.now(), grant_id, section_name))
            else:
                conn.execute('''
                    INSERT INTO grant_sections (grant_id, section_name, content)
                    VALUES (?, ?, ?)
                ''', (grant_id, section_name, content))
        
        # Update grant progress
        conn.execute('''
            UPDATE grants SET progress = 90, updated_at = ? WHERE id = ?
        ''', (datetime.now(), grant_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Enhanced grant content generated successfully',
            'sections': sections,
            'budget': budget,
            'scope': scope,
            'timeline': timeline,
            'context_used': {
                'grant_requirements': len(grant_requirements),
                'organization_context': len(org_context),
                'project_specifications': len(project_specs)
            }
        })
        
    except Exception as e:
        print(f"Enhanced grant generation error: {e}")
        return jsonify({'error': str(e)}), 500

# Three-Tier Vector Database API Endpoints

@app.route('/api/grants/<int:grant_id>/create-application', methods=['POST'])
def create_three_tier_application(grant_id):
    """Create a three-tier grant application with vector database collections"""
    try:
        data = request.get_json()
        application_name = data.get('application_name', f'Grant Application {grant_id}')
        
        # Check if this is the enhanced vector database
        if hasattr(vector_db, 'create_grant_application'):
            # Create three-tier application
            result = vector_db.create_grant_application(
                application_id=str(grant_id),
                application_name=application_name
            )
            return jsonify({
                'success': True,
                'message': 'Three-tier application created successfully',
                'application_details': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Three-tier system not available with current vector database'
            }), 501
            
    except Exception as e:
        print(f"Error creating three-tier application: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/upload-tier/<int:tier>', methods=['POST'])
def upload_to_tier(grant_id, tier):
    """Upload documents to a specific tier (1, 2, or 3)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate tier
        if tier not in [1, 2, 3]:
            return jsonify({'error': 'Invalid tier. Must be 1, 2, or 3'}), 400
        
        # Get document metadata
        document_type = request.form.get('document_type', '')
        description = request.form.get('description', '')
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            
            # Create tier subdirectory
            tier_names = {1: 'tier1_requirements', 2: 'tier2_organization', 3: 'tier3_proposal'}
            doc_dir = os.path.join(app.config['UPLOAD_FOLDER'], tier_names[tier])
            os.makedirs(doc_dir, exist_ok=True)
            
            # Save file
            filepath = os.path.join(doc_dir, filename)
            file.save(filepath)
            
            # Read file content
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Handle binary files
                with open(filepath, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')
            
            # Process with three-tier vector database
            if hasattr(vector_db, 'add_document_to_tier'):
                doc_metadata = {
                    'original_filename': file.filename,
                    'document_type': document_type,
                    'description': description,
                    'file_size': os.path.getsize(filepath),
                    'mime_type': file.content_type
                }
                
                doc_id = vector_db.add_document_to_tier(
                    application_id=str(grant_id),
                    tier=tier,
                    document_content=content,
                    document_metadata=doc_metadata
                )
                
                # Save to traditional database
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO documents (filename, original_filename, filepath, category, grant_id, file_size, mime_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    filename, file.filename, filepath, tier_names[tier],
                    grant_id, os.path.getsize(filepath), file.content_type
                ))
                db_doc_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'Document uploaded to Tier {tier} successfully',
                    'tier': tier,
                    'document_id': db_doc_id,
                    'vector_document_id': doc_id,
                    'filename': filename,
                    'original_filename': file.filename
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Three-tier system not available with current vector database'
                }), 501
        else:
            return jsonify({'error': 'File type not allowed'}), 400
            
    except Exception as e:
        print(f"Error uploading to tier {tier}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/tier-summary', methods=['GET'])
def get_application_tier_summary(grant_id):
    """Get summary of all tiers for a grant application"""
    try:
        if hasattr(vector_db, 'get_application_summary'):
            summary = vector_db.get_application_summary(str(grant_id))
            return jsonify({
                'success': True,
                'summary': summary
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Three-tier system not available with current vector database'
            }), 501
            
    except Exception as e:
        print(f"Error getting tier summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/query-tiers', methods=['POST'])
def query_all_tiers(grant_id):
    """Query all three tiers for relevant content"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        n_results_per_tier = data.get('n_results_per_tier', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if hasattr(vector_db, 'query_all_tiers'):
            results = vector_db.query_all_tiers(
                application_id=str(grant_id),
                query=query,
                n_results_per_tier=n_results_per_tier
            )
            
            return jsonify({
                'success': True,
                'query': query,
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Three-tier system not available with current vector database'
            }), 501
            
    except Exception as e:
        print(f"Error querying tiers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/generate-three-tier', methods=['POST'])
def generate_grant_with_three_tier(grant_id):
    """Generate grant content using the three-tier system"""
    try:
        data = request.get_json()
        
        # Get grant and organization data
        conn = get_db_connection()
        grant = conn.execute('SELECT * FROM grants WHERE id = ?', (grant_id,)).fetchone()
        org = conn.execute('SELECT * FROM organizations WHERE id = 1').fetchone()
        conn.close()
        
        if not grant or not org:
            return jsonify({'error': 'Grant or organization not found'}), 404
        
        if not hasattr(vector_db, 'query_all_tiers'):
            return jsonify({
                'success': False,
                'message': 'Three-tier system not available with current vector database'
            }), 501
        
        # Query each tier for relevant information
        funder_id = data.get('funder', 'region_16_opioid_council')
        
        # 1. Query Tier 1 (Requirements) for grant-specific requirements
        tier1_results = vector_db.query_tier(
            application_id=str(grant_id),
            tier=1,
            query=f"requirements application questions deadline budget {funder_id}",
            n_results=10
        )
        
        # 2. Query Tier 2 (Organization) for relevant organizational context
        tier2_results = vector_db.query_tier(
            application_id=str(grant_id),
            tier=2,
            query=f"programs services impact outcomes metrics {org['name']}",
            n_results=8
        )
        
        # 3. Query Tier 3 (Proposal) for project specifications
        tier3_results = vector_db.query_tier(
            application_id=str(grant_id),
            tier=3,
            query="objectives activities budget timeline deliverables outcomes",
            n_results=5
        )
        
        # Create enhanced organization profile
        org_profile = OrganizationProfile(
            name=org['name'],
            current_service_areas=[org['city'] + ', ' + org['state']],
            annual_budget=org['annualBudget'] or 485000,
            staff_capacity=org['staffSize'] or 8,
            proven_partnerships={
                "Polaris Pathways": "$650/person training",
                "Serenity Connection Center": "Event partnership",
                "SafeSide Recovery": "Referral network",
            },
            historical_performance_metrics={
                "satisfaction_rate": 0.8276,
                "completion_rate": 0.75,
                "event_attendance": 47,
                "participants_served": 281,
            },
            expansion_risk_tolerance="medium",
        )
        
        # Generate enhanced sections with three-tier context
        initial_scope = {"participants": 35, "events": 8, "staffing_fte": 4.0, "event_budget_per": 1250}
        budget = grant_engine.calibrate_budget(funder_id, org_profile, initial_scope)
        scope = grant_engine.scale_program_scope(budget["total_budget"], funder_id, initial_scope)
        timeline = grant_engine.synchronize_timeline(
            (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=395)).strftime('%Y-%m-%d')
        )
        
        # Generate context-aware sections
        sections = {
            'Executive Summary': f"SAFE respectfully requests ${budget['total_budget']:,} to serve {scope['participants']} participants through {scope['events']} evidence-based recovery support events, fully aligned with funder requirements and organizational capabilities.",
            'Project Description': f"Activities: Host {scope['events']} sober community events; enroll up to {scope['participants']} participants in structured recovery programming based on proven organizational methods.",
            'Goals and Objectives': f"- Serve up to {scope['participants']} unique participants\n- Deliver {scope['events']} sober events\n- Achieve ≥80% participant satisfaction\n- Demonstrate measurable recovery outcomes\n- Meet all funder-specified deliverables",
            'Statement of Need': "Community members face barriers to sustained recovery, including limited alcohol-free social options and insufficient peer support networks, as identified through comprehensive needs assessment.",
            'Evaluation Plan': "Comprehensive data collection through participant sign-ins, attendance tracking, satisfaction surveys, outcome measurement tools, and funder-required reporting metrics.",
            'Budget Narrative': f"Total request: ${budget['total_budget']:,}\n- Personnel: ${budget['personnel']:,}\n- Contractor Services: ${budget['contractors']:,}\n- Operations: ${budget['operations']:,}\n- All budget categories align with funder guidelines",
        }
        
        # Save generated sections to database
        conn = get_db_connection()
        for section_name, content in sections.items():
            existing = conn.execute('''
                SELECT id FROM grant_sections WHERE grant_id = ? AND section_name = ?
            ''', (grant_id, section_name)).fetchone()
            
            if existing:
                conn.execute('''
                    UPDATE grant_sections SET content = ?, updated_at = ?
                    WHERE grant_id = ? AND section_name = ?
                ''', (content, datetime.now(), grant_id, section_name))
            else:
                conn.execute('''
                    INSERT INTO grant_sections (grant_id, section_name, content)
                    VALUES (?, ?, ?)
                ''', (grant_id, section_name, content))
        
        # Update grant progress
        conn.execute('''
            UPDATE grants SET progress = 95, updated_at = ? WHERE id = ?
        ''', (datetime.now(), grant_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Three-tier grant content generated successfully',
            'sections': sections,
            'budget': budget,
            'scope': scope,
            'timeline': timeline,
            'context_used': {
                'tier1_requirements': len(tier1_results),
                'tier2_organization': len(tier2_results),
                'tier3_proposal': len(tier3_results)
            },
            'tier_results': {
                'tier1_requirements': tier1_results[:3],  # Show first 3 for preview
                'tier2_organization': tier2_results[:3],
                'tier3_proposal': tier3_results[:3]
            }
        })
        
    except Exception as e:
        print(f"Three-tier grant generation error: {e}")
        return jsonify({'error': str(e)}), 500

# Enhanced Document Processing and Dynamic Tab Generation Endpoints

@app.route('/api/documents/analyze', methods=['POST'])
def analyze_document():
    """Analyze a document using the enhanced document processing service"""
    try:
        if not document_service:
            return jsonify({'error': 'Enhanced document processing not available'}), 501
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        grant_id = request.form.get('grant_id')
        document_type = request.form.get('document_type')
        
        if not grant_id:
            return jsonify({'error': 'Grant ID is required'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            
            # Create temporary directory for analysis
            temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save file temporarily
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            
            try:
                # Analyze document using enhanced service
                result = document_service.process_document(
                    file_path=filepath,
                    grant_id=int(grant_id),
                    document_type=document_type
                )
                
                # Clean up temporary file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return jsonify(result)
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise e
        else:
            return jsonify({'error': 'File type not allowed'}), 400
            
    except Exception as e:
        print(f"Document analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/dynamic-tabs', methods=['GET'])
def get_dynamic_tabs(grant_id):
    """Get dynamically generated tabs based on processed documents"""
    try:
        if not document_service:
            return jsonify({'error': 'Enhanced document processing not available'}), 501
        
        # Get all processed documents for this grant
        conn = get_db_connection()
        documents = conn.execute('''
            SELECT * FROM documents WHERE grant_id = ?
        ''', (grant_id,)).fetchall()
        conn.close()
        
        if not documents:
            # Return default tabs if no documents
            return jsonify({
                'success': True,
                'tabs': {
                    'proposal_default': {
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
                    },
                    'budget_default': {
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
                },
                'tab_count': 2,
                'generated_at': datetime.now().isoformat()
            })
        
        # Process documents and extract questions/attachments
        processed_documents = []
        for doc in documents:
            try:
                # Re-process or get cached processing results
                result = document_service.process_document(
                    file_path=doc['filepath'],
                    grant_id=grant_id,
                    document_type=doc['category']
                )
                if result['success']:
                    processed_documents.append(result)
            except Exception as e:
                print(f"Error processing document {doc['id']}: {e}")
                continue
        
        # Generate dynamic tabs
        tab_result = document_service.generate_dynamic_tabs(grant_id, processed_documents)
        
        return jsonify(tab_result)
        
    except Exception as e:
        print(f"Dynamic tabs error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/tabs', methods=['POST'])
def create_tab(grant_id):
    """Create a new tab manually"""
    try:
        if not section_service:
            return jsonify({'error': 'Enhanced section management not available'}), 501
        
        data = request.get_json()
        tab_name = data.get('tab_name')
        tab_type = data.get('tab_type', 'other')
        
        if not tab_name:
            return jsonify({'error': 'Tab name is required'}), 400
        
        result = section_service.create_tab(
            grant_id=grant_id,
            tab_name=tab_name,
            tab_type=tab_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Create tab error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/tabs/<tab_id>', methods=['PUT'])
def update_tab(grant_id, tab_id):
    """Update an existing tab"""
    try:
        if not section_service:
            return jsonify({'error': 'Enhanced section management not available'}), 501
        
        data = request.get_json()
        
        result = section_service.update_tab(
            grant_id=grant_id,
            tab_id=tab_id,
            updates=data
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Update tab error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/tabs/<tab_id>', methods=['DELETE'])
def delete_tab(grant_id, tab_id):
    """Delete a tab"""
    try:
        if not section_service:
            return jsonify({'error': 'Enhanced section management not available'}), 501
        
        result = section_service.delete_tab(
            grant_id=grant_id,
            tab_id=tab_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Delete tab error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/tabs/<tab_id>/sections', methods=['POST'])
def create_section(grant_id, tab_id):
    """Create a new section within a tab"""
    try:
        if not section_service:
            return jsonify({'error': 'Enhanced section management not available'}), 501
        
        data = request.get_json()
        section_title = data.get('section_title')
        question_text = data.get('question_text', '')
        
        if not section_title:
            return jsonify({'error': 'Section title is required'}), 400
        
        result = section_service.create_section(
            grant_id=grant_id,
            tab_id=tab_id,
            section_title=section_title,
            question_text=question_text
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Create section error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/tabs/<tab_id>/sections/<section_id>', methods=['PUT'])
def update_section(grant_id, tab_id, section_id):
    """Update a section"""
    try:
        if not section_service:
            return jsonify({'error': 'Enhanced section management not available'}), 501
        
        data = request.get_json()
        
        result = section_service.update_section(
            grant_id=grant_id,
            tab_id=tab_id,
            section_id=section_id,
            updates=data
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Update section error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/tabs/<tab_id>/sections/<section_id>', methods=['DELETE'])
def delete_section(grant_id, tab_id, section_id):
    """Delete a section"""
    try:
        if not section_service:
            return jsonify({'error': 'Enhanced section management not available'}), 501
        
        result = section_service.delete_section(
            grant_id=grant_id,
            tab_id=tab_id,
            section_id=section_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Delete section error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/regenerate', methods=['POST'])
def regenerate_content(grant_id):
    """Regenerate content using enhanced AI with user notes"""
    try:
        if not regeneration_service:
            return jsonify({'error': 'Enhanced regeneration service not available'}), 501
        
        data = request.get_json()
        regeneration_type = data.get('type', 'section')  # 'section', 'tab', or 'full'
        target_id = data.get('target_id')  # section_id or tab_id
        user_notes = data.get('user_notes', '')
        
        if regeneration_type == 'section' and not target_id:
            return jsonify({'error': 'Section ID required for section regeneration'}), 400
        elif regeneration_type == 'tab' and not target_id:
            return jsonify({'error': 'Tab ID required for tab regeneration'}), 400
        
        result = regeneration_service.regenerate_content(
            grant_id=grant_id,
            regeneration_type=regeneration_type,
            target_id=target_id,
            user_notes=user_notes
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Regeneration error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/context-query', methods=['POST'])
def query_grant_context(grant_id):
    """Query the vector database for context specific to a grant"""
    try:
        if not document_service:
            return jsonify({'error': 'Enhanced document processing not available'}), 501
        
        data = request.get_json()
        query = data.get('query', '')
        context_type = data.get('context_type', 'all')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        result = document_service.query_context_for_generation(
            grant_id=grant_id,
            query=query,
            context_type=context_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Context query error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/processing-stats', methods=['GET'])
def get_processing_stats():
    """Get statistics about the enhanced processing system"""
    try:
        stats = {
            'enhanced_processing_available': document_service is not None,
            'section_management_available': section_service is not None,
            'regeneration_service_available': regeneration_service is not None
        }
        
        if document_service:
            processing_stats = document_service.get_processing_stats()
            stats.update(processing_stats)
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Processing stats error: {e}")
        return jsonify({'error': str(e)}), 500

# Analytics endpoints
@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        
        total_grants = conn.execute('SELECT COUNT(*) FROM grants').fetchone()[0]
        in_progress = conn.execute("SELECT COUNT(*) FROM grants WHERE status = 'In Progress'").fetchone()[0]
        submitted = conn.execute("SELECT COUNT(*) FROM grants WHERE status = 'Submitted'").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM grants WHERE status = 'Approved'").fetchone()[0]
        
        conn.close()
        
        # Get vector database statistics
        vector_stats = {}
        
        # Check if we have the enhanced three-tier system
        if hasattr(vector_db, 'list_applications'):
            applications = vector_db.list_applications()
            vector_stats['three_tier_applications'] = len(applications)
            vector_stats['applications'] = applications
        
        # Get traditional stats if available
        try:
            for doc_type in ['grant_documents', 'organization_documents', 'application_outlines']:
                if hasattr(vector_db, 'get_document_summary'):
                    vector_stats[doc_type] = vector_db.get_document_summary(doc_type)
        except:
            pass
        
        return jsonify({
            'totalGrants': total_grants,
            'inProgress': in_progress,
            'submitted': submitted,
            'approved': approved,
            'vectorDatabase': vector_stats,
            'threeTierEnabled': hasattr(vector_db, 'create_grant_application')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/load-region16-questions', methods=['POST'])
def load_region16_questions(grant_id):
    """Load the 12 Region 16 questions automatically for a new grant"""
    try:
        # Read the Region 16 questions file
        questions_file_path = os.path.join('learning_data', 'REGION_16_APPLICATION_QUESTIONS.md')
        
        if not os.path.exists(questions_file_path):
            return jsonify({'error': 'Region 16 questions file not found'}), 404
        
        with open(questions_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the questions from the markdown content
        questions = []
        lines = content.split('\n')
        current_question = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('## Question '):
                # Extract question number and title
                if current_question:
                    questions.append(current_question)
                
                # Parse question header
                parts = line.split(':', 1)
                if len(parts) == 2:
                    question_num = parts[0].replace('## Question ', '').strip()
                    question_title = parts[1].strip()
                    
                    # Extract max words if present
                    max_words = None
                    if '(Max:' in question_title:
                        title_parts = question_title.split('(Max:')
                        question_title = title_parts[0].strip()
                        if len(title_parts) > 1:
                            words_part = title_parts[1].split(')')[0].strip()
                            try:
                                max_words = int(words_part.replace(' words', ''))
                            except:
                                pass
                    
                    current_question = {
                        'question_number': question_num,
                        'question_title': question_title,
                        'max_words': max_words,
                        'content': '',
                        'required': True,
                        'section_type': 'text_response'
                    }
                    
                    # Special handling for specific question types
                    if 'Checkboxes' in question_title:
                        current_question['section_type'] = 'checkbox'
                    elif 'Funding Amount' in question_title:
                        current_question['section_type'] = 'number'
            
            elif line.startswith('---') and current_question:
                # End of current question
                if current_question:
                    questions.append(current_question)
                    current_question = None
        
        # Add the last question if exists
        if current_question:
            questions.append(current_question)
        
        # Save questions as grant sections
        conn = get_db_connection()
        saved_count = 0
        
        for i, question in enumerate(questions):
            section_name = f"question_{question['question_number']}"
            section_content = {
                'question_title': question['question_title'],
                'question_number': question['question_number'],
                'max_words': question['max_words'],
                'section_type': question['section_type'],
                'required': question['required'],
                'content': '',
                'order': i + 1
            }
            
            # Check if section already exists
            existing = conn.execute('''
                SELECT id FROM grant_sections WHERE grant_id = ? AND section_name = ?
            ''', (grant_id, section_name)).fetchone()
            
            if not existing:
                conn.execute('''
                    INSERT INTO grant_sections (grant_id, section_name, content)
                    VALUES (?, ?, ?)
                ''', (grant_id, section_name, json.dumps(section_content)))
                saved_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {len(questions)} Region 16 questions',
            'questions_loaded': len(questions),
            'sections_created': saved_count,
            'questions': questions
        })
        
    except Exception as e:
        print(f"Error loading Region 16 questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/grants/<int:grant_id>/sections', methods=['GET'])
def get_grant_sections(grant_id):
    """Get all sections for a grant"""
    try:
        conn = get_db_connection()
        sections = conn.execute('''
            SELECT * FROM grant_sections WHERE grant_id = ? ORDER BY id
        ''', (grant_id,)).fetchall()
        conn.close()
        
        # Format sections for frontend
        formatted_sections = []
        for section in sections:
            section_dict = dict(section)
            
            # Try to parse content as JSON, fallback to plain text
            try:
                content = json.loads(section['content'])
                section_dict['parsed_content'] = content
            except:
                section_dict['parsed_content'] = {
                    'content': section['content'],
                    'section_type': 'text_response'
                }
            
            formatted_sections.append(section_dict)
        
        return jsonify({
            'success': True,
            'sections': formatted_sections,
            'total_sections': len(formatted_sections)
        })
        
    except Exception as e:
        print(f"Error getting grant sections: {e}")
        return jsonify({'error': str(e)}), 500

# Catch-all route: serve React frontend for any non-API route
# This must be AFTER all API routes so /api/* is handled by Flask
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend for client-side routing"""
    if app.static_folder:
        # Check if the path corresponds to an actual static file
        file_path = os.path.join(app.static_folder, path)
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        # Otherwise serve index.html for React Router
        index_path = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(app.static_folder, 'index.html')
    return jsonify({'error': 'Frontend not built. Run: cd frontend && npm run build'}), 404


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    print("Starting Grant Writing Platform Backend...")
    print(f"Health check: http://localhost:{port}/api/health")
    print(f"Frontend: http://localhost:{port}")
    print(f"Environment: {'production' if is_production else 'development'}")
    
    app.run(debug=not is_production, host='0.0.0.0', port=port)
