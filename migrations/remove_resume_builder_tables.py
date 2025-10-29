import sqlite3

def remove_resume_builder_tables():
    """Remove the resume builder related tables from the database."""
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    
    # Drop the resume download logs table
    cursor.execute('''
        DROP TABLE IF EXISTS resume_downloads
    ''')
    
    # Drop the generated resumes table
    cursor.execute('''
        DROP TABLE IF EXISTS generated_resumes
    ''')
    
    conn.commit()
    conn.close()
    print("Successfully removed resume builder tables")

if __name__ == "__main__":
    remove_resume_builder_tables()
