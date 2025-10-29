import sqlite3

# Connect to the database
conn = sqlite3.connect('rezumai.db')
cursor = conn.cursor()

# Check resume downloads count
cursor.execute('SELECT COUNT(*) FROM resume_downloads')
count = cursor.fetchone()[0]
print(f'Total resume downloads: {count}')

# Check generated resumes count
cursor.execute('SELECT COUNT(*) FROM generated_resumes')
gen_count = cursor.fetchone()[0]
print(f'Total generated resumes: {gen_count}')

# Show sample download records
print('\nSample download records:')
cursor.execute('SELECT * FROM resume_downloads LIMIT 5')
rows = cursor.fetchall()
for row in rows:
    print(row)

# Show sample generated resumes
print('\nSample generated resumes:')
cursor.execute('SELECT id, user_id, created_at FROM generated_resumes LIMIT 5')
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()