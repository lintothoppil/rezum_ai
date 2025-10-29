import sqlite3

def add_resume_builder_tables():
    """Add tables for the enhanced resume builder."""
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    
    # Resume table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        template_type TEXT NOT NULL DEFAULT 'classic',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_public BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Resume sections table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resume_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        section_type TEXT NOT NULL,  -- 'personal', 'education', 'experience', 'skill', 'project', 'certification', 'achievement'
        section_data TEXT NOT NULL,  -- JSON string of section data
        display_order INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE
    )
    ''')
    
    # Resume downloads tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resume_downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # AI recommendations cache
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resume_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_id INTEGER,
        recommendations TEXT,  -- JSON string of AI recommendations
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Successfully added resume builder tables")

if __name__ == "__main__":
    add_resume_builder_tables()
