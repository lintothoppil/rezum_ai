import sqlite3

# Connect to the database
conn = sqlite3.connect('rezumai.db')
cursor = conn.cursor()

# Check if foreign keys are enabled
cursor.execute('PRAGMA foreign_keys')
fk_status = cursor.fetchone()[0]
print(f'Foreign key enforcement: {fk_status}')

# Get a sample resume
cursor.execute('SELECT id, user_id FROM generated_resumes LIMIT 1')
resume = cursor.fetchone()
print(f'Sample resume: {resume}')

# Try to insert a download record manually
if resume:
    resume_id, user_id = resume
    print(f'Trying to insert download record for resume_id={resume_id}, user_id={user_id}')
    try:
        cursor.execute('INSERT INTO resume_downloads (user_id, resume_id) VALUES (?, ?)', (user_id, resume_id))
        conn.commit()
        print('Successfully inserted download record')
    except Exception as e:
        print(f'Error inserting download record: {e}')

# Check download count
cursor.execute('SELECT COUNT(*) FROM resume_downloads')
count = cursor.fetchone()[0]
print(f'Total resume downloads: {count}')

conn.close()