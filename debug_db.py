import sqlite3

# Connect to the database
conn = sqlite3.connect('c:/Users/HP/OneDrive/Desktop/rezum_ai/rezumai.db')
cursor = conn.cursor()

print("=== Database Debug Info ===")

# Check users
cursor.execute('SELECT id, email FROM users')
users = cursor.fetchall()
print(f"Users ({len(users)}):")
for u in users:
    print(f"  ID: {u[0]}, Email: {u[1]}")

# Check generated resumes
cursor.execute('SELECT id, user_id FROM generated_resumes')
resumes = cursor.fetchall()
print(f"\nGenerated resumes ({len(resumes)}):")
for r in resumes:
    print(f"  ID: {r[0]}, User ID: {r[1]}")

# Check downloads
cursor.execute('SELECT user_id, resume_id FROM resume_downloads')
downloads = cursor.fetchall()
print(f"\nDownloads ({len(downloads)}):")
for d in downloads:
    print(f"  User ID: {d[0]}, Resume ID: {d[1]}")

conn.close()