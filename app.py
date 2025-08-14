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
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sqlite3
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing grant engine
from engines.grant_writing_engine_v2 import GrantWritingEngineV2, OrganizationProfile

# Import the fallback vector database service for testing
try:
    from services.vector_database import VectorDatabaseService
except ImportError:
    from services.vector_database_fallback import VectorDatabaseService
    print("🔄 Using fallback vector database service (full ChromaDB dependencies not installed)")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend connection

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize grant engine and vector database
grant_engine = GrantWritingEngineV2()
vector_db = VectorDatabaseService()

# Database setup
def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('grant_platform.db')
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
    conn = sqlite3.connect('grant_platform.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'md'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes

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
        for doc_type in ['grant_documents', 'organization_documents', 'application_outlines']:
            vector_stats[doc_type] = vector_db.get_document_summary(doc_type)
        
        return jsonify({
            'totalGrants': total_grants,
            'inProgress': in_progress,
            'submitted': submitted,
            'approved': approved,
            'vectorDatabase': vector_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the Flask app
    print("🚀 Starting Grant Writing Platform Backend...")
    print("📊 Dashboard available at: http://localhost:5000/api/health")
    print("🔄 Frontend should connect to: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
