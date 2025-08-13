"""
Application settings for GhostTeam Grant Writing Platform.
"""
import os
from pathlib import Path
from typing import Optional

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Environment configuration
class Config:
    """Base configuration class."""
    
    # Basic Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/ghosteam_grants.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    # Vector Database Configuration
    VECTOR_DB_PATH = BASE_DIR / 'data' / 'vector_db'
    
    # File upload configuration
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'md'}
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Security configuration
    WTF_CSRF_ENABLED = True
    
    # Application configuration
    GRANTS_PER_PAGE = 20
    SEARCH_RESULTS_PER_PAGE = 10
    
    # Cache configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'ghosteam.log'
    
    @classmethod
    def init_app(cls, app):
        """Initialize the Flask app with configuration."""
        # Create necessary directories
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.VECTOR_DB_PATH, exist_ok=True)
        os.makedirs(cls.LOG_FILE.parent, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config() -> Config:
    """Get the current configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])

# SAFE Knowledge Base Configuration
class SAFEConfig:
    """Configuration for SAFE (Sober AF Entertainment) knowledge base."""
    
    # Organization details
    ORGANIZATION_NAME = "Sober AF Entertainment"
    ORGANIZATION_ACRONYM = "SAFE"
    ORGANIZATION_TYPE = "Non-Profit"
    
    # Mission and vision
    MISSION = """To provide sober entertainment opportunities and support for individuals 
    in recovery and those choosing alcohol-free lifestyles."""
    
    VISION = """A community where sobriety is celebrated and everyone has access to 
    engaging, alcohol-free entertainment and social opportunities."""
    
    # Core programs
    PROGRAMS = [
        {
            "name": "Sober Events",
            "description": "Alcohol-free social gatherings, concerts, and activities",
            "target_audience": "Adults in recovery and sober-curious individuals",
            "frequency": "Monthly"
        },
        {
            "name": "Peer Support Groups",
            "description": "Facilitated support groups for individuals in recovery",
            "target_audience": "Adults in recovery",
            "frequency": "Weekly"
        },
        {
            "name": "Community Outreach",
            "description": "Educational programs about addiction and recovery",
            "target_audience": "General community",
            "frequency": "Quarterly"
        }
    ]
    
    # Key staff roles
    STAFF_ROLES = [
        "Executive Director",
        "Program Manager",
        "Event Coordinator",
        "Outreach Specialist",
        "Administrative Assistant"
    ]
    
    # Financial information
    ANNUAL_BUDGET_RANGE = "$50,000 - $100,000"
    FUNDING_SOURCES = [
        "Individual donations",
        "Foundation grants",
        "Government grants",
        "Event fees",
        "Corporate sponsorships"
    ]
    
    # Geographic service area
    SERVICE_AREA = "Metropolitan area and surrounding communities"
    
    # Key metrics
    IMPACT_METRICS = [
        "Number of individuals served",
        "Number of events hosted",
        "Number of support group sessions",
        "Community engagement levels",
        "Participant satisfaction scores"
    ]

# Grant Writing Configuration
class GrantConfig:
    """Configuration for grant writing features."""
    
    # Common grant sections
    STANDARD_SECTIONS = [
        "Executive Summary",
        "Statement of Need",
        "Project Description",
        "Goals and Objectives",
        "Methodology",
        "Evaluation Plan",
        "Budget Narrative",
        "Organizational Capacity",
        "Sustainability Plan",
        "Conclusion"
    ]
    
    # Budget categories
    BUDGET_CATEGORIES = [
        "Personnel",
        "Fringe Benefits",
        "Travel",
        "Equipment",
        "Supplies",
        "Contractual",
        "Total Direct Costs",
        "Indirect Costs",
        "Total Project Costs"
    ]
    
    # Common funder types
    FUNDER_TYPES = [
        "Federal Government",
        "State Government",
        "Local Government",
        "Private Foundation",
        "Corporate Foundation",
        "Community Foundation",
        "Corporate Giving Program"
    ]
    
    # Grant statuses
    GRANT_STATUSES = [
        "Draft",
        "Under Review",
        "Submitted",
        "Pending Decision",
        "Awarded",
        "Declined",
        "Closed"
    ]
    
    # Priority levels
    PRIORITY_LEVELS = [
        "High",
        "Medium", 
        "Low"
    ]

# AI Prompts Configuration
class AIPrompts:
    """Configuration for AI prompts and templates."""
    
    CONTENT_GENERATION_PROMPT = """
    You are an expert grant writer helping to create compelling proposal content.
    
    Context:
    - Organization: {organization_name}
    - Section: {section_name}
    - Requirements: {requirements}
    - Previous successful content: {reference_content}
    
    Generate a well-written, professional section that:
    1. Addresses all requirements
    2. Uses the organization's voice and style
    3. Incorporates relevant data and evidence
    4. Is compelling and persuasive
    
    Content:
    """
    
    BUDGET_REVIEW_PROMPT = """
    Review this grant budget for accuracy and completeness:
    
    Budget: {budget_data}
    Project Description: {project_description}
    
    Check for:
    1. Mathematical accuracy
    2. Reasonable cost estimates
    3. Alignment with project activities
    4. Inclusion of all necessary categories
    5. Proper indirect cost calculations
    
    Provide feedback and suggestions:
    """
    
    COMPLIANCE_CHECK_PROMPT = """
    Review this grant proposal for compliance with funder requirements:
    
    Funder Guidelines: {guidelines}
    Proposal Content: {proposal_content}
    
    Check for:
    1. Word/character limits
    2. Required sections
    3. Formatting requirements
    4. Eligibility criteria
    5. Submission requirements
    
    Identify any compliance issues:
    """
