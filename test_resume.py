import json
import pdfplumber
import re
from app import is_valid_resume_content, generate_ats_pdf

# Sample resume data
sample_resume_data = {
    "user_type": "experienced",
    "template_type": "classic",
    "personal_details": {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1 234 567 8900",
        "location": "New York, NY",
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe"
    },
    "education": [
        {
            "degree": "B.Tech",
            "institution": "ABC University",
            "location": "New York, NY",
            "start_date": "2015-09",
            "end_date": "2019-06",
            "start_year": "2015",
            "end_year": "2019",
            "currently_studying": False
        }
    ],
    "technical_skills": {
        "programming_languages": "Python, JavaScript, Java",
        "frameworks": "Django, React, Spring",
        "databases": "MySQL, PostgreSQL, MongoDB",
        "cloud_technologies": "AWS, Docker, Kubernetes",
        "devops_tools": "Git, Jenkins, Terraform",
        "other_technical_skills": "REST APIs, Microservices"
    },
    "soft_skills": ["Communication", "Teamwork", "Problem Solving"],
    "work_experience": [
        {
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "start_date": "2019-07",
            "end_date": "2023-05",
            "currently_working": False,
            "bullet_points": "Developed scalable web applications using Python and Django\nImplemented RESTful APIs for mobile applications\nCollaborated with cross-functional teams to deliver high-quality software"
        }
    ],
    "projects": [
        {
            "project_name": "E-commerce Platform",
            "technologies_used": "Python, Django, React, PostgreSQL",
            "description": "A full-stack e-commerce platform with payment integration",
            "github_link": "https://github.com/johndoe/ecommerce",
            "demo_link": "https://ecommerce.example.com"
        }
    ],
    "certifications": [
        {
            "certification_name": "AWS Certified Solutions Architect",
            "organization": "Amazon Web Services",
            "start_date": "2020-03",
            "end_date": "2023-03",
            "currently_valid": True,
            "certification_id": "AWS-123456"
        }
    ]
}

# Generate PDF
pdf_buffer = generate_ats_pdf(sample_resume_data)

# Save PDF to file for inspection
with open("test_resume.pdf", "wb") as f:
    f.write(pdf_buffer.getvalue())

# Extract text from the generated PDF
pdf_buffer.seek(0)
text = ""
with pdfplumber.open(pdf_buffer) as pdf:
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

print("Extracted text from PDF:")
print("=" * 50)
print(text)
print("=" * 50)

# Check if it's a valid resume
is_valid = is_valid_resume_content(text)
print(f"\nIs valid resume content: {is_valid}")

# Count words
word_count = len(re.findall(r'\w+', text.lower()))
print(f"Word count: {word_count}")

# Check for keywords
resume_keywords = ["education", "skills", "experience", "projects", "certifications", "summary"]
found_keywords = sum(1 for keyword in resume_keywords if keyword in text.lower())
print(f"Found keywords: {found_keywords}")

# Check for email
has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+', text.lower()))
print(f"Has email: {has_email}")