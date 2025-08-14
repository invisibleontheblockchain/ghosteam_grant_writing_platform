import sqlite3

# Connect to database
conn = sqlite3.connect('grant_platform.db')
cursor = conn.cursor()

# Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Existing tables:', [table[0] for table in tables])

# If no tables exist, create them
if not tables:
    print('No tables found. Creating database schema...')
    
    # Create organizations table
    cursor.execute('''
        CREATE TABLE organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            type TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            tax_id TEXT,
            incorporation_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create grants table
    cursor.execute('''
        CREATE TABLE grants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            funder TEXT,
            status TEXT DEFAULT 'Draft',
            deadline TEXT,
            amount TEXT,
            description TEXT,
            organization_id INTEGER,
            sections TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
    ''')
    
    # Create documents table
    cursor.execute('''
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            content_type TEXT,
            category TEXT,
            grant_id INTEGER,
            organization_id INTEGER,
            text_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grant_id) REFERENCES grants (id),
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
    ''')
    
    # Insert default organization (SAFE)
    cursor.execute('''
        INSERT INTO organizations (
            name, description, type, address, phone, email, website, tax_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'SAFE (Substance Abuse Free Environment)',
        'SAFE is a leading organization dedicated to creating substance abuse-free environments through education, prevention, and community engagement.',
        'Non-Profit',
        '123 Community Street, Denver, CO 80202',
        '(303) 555-0123',
        'info@safe-environment.org',
        'https://safe-environment.org',
        '84-1234567'
    ))
    
    # Insert a default grant
    cursor.execute('''
        INSERT INTO grants (
            name, funder, status, deadline, amount, description, organization_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Educational Technology Grant',
        'Department of Education',
        'Draft',
        '2025-09-15',
        '$50,000',
        'This grant will fund the implementation of innovative educational technology solutions.',
        1
    ))
    
    conn.commit()
    print('Database schema created and default data inserted!')

else:
    print('Database tables already exist.')

# Check final state
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Final tables:', [table[0] for table in tables])

# Check grants
cursor.execute("SELECT id, name FROM grants")
grants = cursor.fetchall()
print('Grants:', grants)

conn.close()
print('Database check complete!')
