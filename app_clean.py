import os
import sqlite3
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_babel import Babel, gettext, get_locale
import json
import logging
from collections import Counter
import pdfplumber  
import docx
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# --- Comprehensive ATS Skills Database ---
BASE_SKILLS = {
    "Python Developer": ["python", "django", "flask", "fastapi", "pandas", "numpy", "scikit-learn"],
    "Java Developer": ["java", "spring", "spring boot", "hibernate", "maven", "gradle", "microservices"],
    "Frontend Developer": ["react", "javascript", "typescript", "html", "css", "angular", "vue", "ui", "ux", "responsive design"],
    "Backend Developer": ["node", "php", "express", "laravel", "api", "rest", "graphql", "microservices"],
    "Full Stack Developer": ["fullstack", "mern", "mean", "lamp", "jamstack", "nextjs", "nuxt"],
    "Data Analyst": ["sql", "excel", "tableau", "powerbi", "data", "analytics", "statistics", "r", "python"],
    "Data Scientist": ["python", "r", "machine learning", "deep learning", "tensorflow", "pytorch", "data science", "nlp"],
    "Project Manager": ["management", "agile", "scrum", "jira", "communication", "leadership", "budget", "stakeholder"],
    "HR Specialist": ["hr", "recruitment", "onboarding", "hris", "compliance", "employee relations", "talent acquisition"],
    "Cloud Engineer": ["aws", "azure", "gcp", "cloud", "terraform", "kubernetes", "docker", "ci/cd"],
    "DevOps Engineer": ["devops", "docker", "kubernetes", "jenkins", "gitlab", "linux", "ansible", "terraform"],
    "Cybersecurity Analyst": ["cybersecurity", "security", "penetration testing", "vulnerability assessment", "siem", "compliance"],
    "Software Engineer": ["c", "c++", ".net", "c#", "algorithms", "data structures", "software development", "testing"],
    "Content Writer": ["content", "writer", "copywriting", "seo", "marketing", "social media", "blogging"],
    "Marketing Specialist": ["marketing", "digital marketing", "seo", "sem", "social media", "analytics", "campaigns"],
    "Sales Representative": ["sales", "crm", "lead generation", "negotiation", "customer relationship", "revenue"],
    "Business Analyst": ["business analysis", "requirements", "documentation", "stakeholder", "process improvement", "data analysis"],
    "UX/UI Designer": ["ux", "ui", "design", "figma", "sketch", "adobe", "user research", "wireframing", "prototyping"],
    "Product Manager": ["product management", "roadmap", "strategy", "user stories", "agile", "stakeholder management"],
    "Quality Assurance": ["qa", "testing", "manual testing", "automation", "selenium", "test cases", "bug tracking"],
    "Medical Professional": ["nurse", "doctor", "pharma", "radiology", "medical", "healthcare", "patient care"],
    "Financial Analyst": ["finance", "financial analysis", "excel", "vba", "budgeting", "forecasting", "financial modeling"],
    "Operations Manager": ["operations", "process improvement", "supply chain", "logistics", "quality control", "lean"],
    "Customer Success": ["customer success", "customer support", "retention", "satisfaction", "onboarding", "account management"]
}

# --- Industry-Specific Keywords for ATS Analysis ---
INDUSTRY_KEYWORDS = {
    "Technology": ["software", "development", "programming", "coding", "api", "database", "cloud", "ai", "ml", "data"],
    "Healthcare": ["patient", "medical", "healthcare", "clinical", "diagnosis", "treatment", "pharmaceutical", "nursing"],
    "Finance": ["financial", "banking", "investment", "risk", "compliance", "audit", "accounting", "trading"],
    "Marketing": ["marketing", "campaign", "brand", "digital", "social media", "seo", "content", "analytics"],
    "Sales": ["sales", "revenue", "client", "customer", "lead", "prospect", "crm", "negotiation"],
    "HR": ["hr", "human resources", "recruitment", "talent", "employee", "onboarding", "training", "compliance"],
    "Operations": ["operations", "process", "efficiency", "quality", "supply chain", "logistics", "management"],
    "Education": ["education", "teaching", "training", "curriculum", "student", "learning", "instruction", "academic"]
}

# --- Action Verbs for Quantifiable Achievements ---
ACTION_VERBS = {
    "achievement": ["achieved", "accomplished", "delivered", "completed", "exceeded", "surpassed"],
    "improvement": ["improved", "increased", "enhanced", "optimized", "streamlined", "reduced", "accelerated"],
    "leadership": ["led", "managed", "supervised", "directed", "coordinated", "mentored", "guided"],
    "development": ["developed", "created", "built", "designed", "implemented", "launched", "established"],
    "analysis": ["analyzed", "evaluated", "assessed", "researched", "investigated", "identified", "measured"]
}

# --- Utility Functions ---

def extract_text_from_resume(filepath):
    """Extract text from resume files using pdfplumber for PDFs and python-docx for DOCX"""
    text = ""
    try:
        if filepath.lower().endswith(".pdf"):
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif filepath.lower().endswith((".docx", ".doc")):
            doc = docx.Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            logging.error(f"Unsupported file format: {filepath}")
    except Exception as e:
        logging.error(f"Error extracting text from {filepath}: {e}")
    
    return text

def load_jobs_data():
    """Loads job data from jobs.json and a placeholder for an API call."""
    try:
        with open("jobs.json", "r", encoding="utf-8") as f:
            local_jobs = json.load(f)
    except FileNotFoundError:
        logging.warning("jobs.json not found. Returning placeholder jobs.")
        local_jobs = []
    
    api_jobs = [
        {"title": "DevOps Engineer", "company_name": "CloudNine", "url": "https://example.com/job/devops", "skills": ["aws", "docker", "kubernetes", "linux"]},
        {"title": "AI/ML Engineer", "company_name": "Innovate AI", "url": "https://example.com/job/ai", "skills": ["python", "ml", "ai", "data"]}
    ]
    return local_jobs + api_jobs

def get_all_known_skills(jobs):
    """Extracts all unique skills from the provided job list AND the base skills dictionary."""
    all_skills = set()
    for job in jobs:
        all_skills.update([s.lower() for s in job.get("skills", [])])
    
    for skill_list in BASE_SKILLS.values():
        all_skills.update(skill_list)

    return all_skills

def extract_keywords(text):
    """Extracts keywords from text based on a known list of skills."""
    all_known_skills = get_all_known_skills(load_jobs_data())
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    keywords = [w for w in words if w in all_known_skills]
    return list(set(keywords))

def suggest_job_role(keywords):
    """Suggests a job role based on extracted keywords."""
    role_mappings = {
        "Python Developer": ["python", "django", "flask"],
        "Java Developer": ["java", "spring"],
        "Frontend Developer": ["react", "javascript", "html", "css", "angular", "ui", "ux", "frontend"],
        "Backend Developer": ["node", "php", "backend"],
        "Full Stack Developer": ["fullstack"],
        "Data Analyst": ["sql", "excel", "tableau", "powerbi", "data"],
        "Data Scientist": ["data", "ml", "ai", "python"],
        "Project Manager": ["management", "agile", "jira", "manager"],
        "HR Specialist": ["hr", "recruitment"],
        "Cloud Engineer": ["aws", "azure", "cloud"],
        "DevOps Engineer": ["devops", "docker", "kubernetes", "linux"],
        "Cybersecurity Analyst": ["cybersecurity", "security"],
        "Software Engineer": ["c", "c++", ".net"],
        "Content Writer": ["content", "writer"],
        "Medical Professional": ["nurse", "doctor", "pharma", "radiology", "medical"]
    }
    
    predicted_roles = set()
    for role, skills in role_mappings.items():
        if any(skill in keywords for skill in skills):
            predicted_roles.add(role)

    if not predicted_roles:
        return ["General Job Seeker"]

    return list(predicted_roles)

def fetch_jobs(predicted_roles, keywords):
    """Fetch jobs from a local JSON file based on predicted roles and keywords."""
    jobs_data = load_jobs_data()
    recommended_jobs = []
    seen_urls = set()

    for job in jobs_data:
        title = job.get("title", "").lower()
        title_match = any(role.lower() in title for role in predicted_roles)
        
        job_skills = {s.lower() for s in job.get("skills", [])}
        skill_overlap = len(job_skills.intersection(set(keywords)))
        
        if (title_match or skill_overlap > 0) and job.get("url") not in seen_urls:
            job["match_score"] = skill_overlap
            recommended_jobs.append(job)
            seen_urls.add(job.get("url"))

    recommended_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return recommended_jobs[:5]

def get_recommendation_label(score):
    if score > 85:
        return "Great 🌟"
    elif score > 70:
        return "Good ✅"
    elif score > 50:
        return "Can be Better 🔧"
    elif score > 30:
        return "Bad ⚠️"
    else:
        return "Flop ❌"

def comprehensive_ats_analysis(text, keywords):
    """
    Advanced ATS Resume Analysis with comprehensive scoring and feedback.
    Returns detailed analysis including job match percentages, skill gaps, and improvement suggestions.
    """
    text_lower = text.lower()
    analysis = {
        'ats_score': 0,
        'job_matches': [],
        'keyword_analysis': {},
        'skill_gaps': {},
        'improvements': [],
        'quantified_suggestions': [],
        'summary_suggestions': '',
        'skills_suggestions': '',
        'ats_explanation': ''
    }
    
    # 1. Advanced ATS Score Calculation (0-100)
    ats_score = calculate_advanced_ats_score(text, keywords)
    analysis['ats_score'] = ats_score
    
    # 2. Job Role Prediction with Match Percentages
    predicted_roles = predict_job_roles_with_scores(keywords, text)
    analysis['job_matches'] = predicted_roles
    
    # 3. Keyword & Skill Match Analysis
    keyword_analysis = analyze_keyword_matches(keywords, predicted_roles)
    analysis['keyword_analysis'] = keyword_analysis
    
    # 4. Skill Gap Analysis by Role
    skill_gaps = analyze_skill_gaps(keywords, predicted_roles)
    analysis['skill_gaps'] = skill_gaps
    
    # 5. Quantifiable Bullet Point Improvements
    quantified_suggestions = generate_quantified_suggestions(text, keywords, predicted_roles)
    analysis['quantified_suggestions'] = quantified_suggestions
    
    # 6. Role-specific Tailoring Advice
    tailoring_advice = generate_tailoring_advice(predicted_roles, keywords)
    analysis['improvements'] = tailoring_advice
    
    # 7. ATS-Optimized Summary and Skills
    summary_suggestions = generate_ats_summary(text, keywords, predicted_roles)
    skills_suggestions = generate_ats_skills_section(keywords, predicted_roles)
    analysis['summary_suggestions'] = summary_suggestions
    analysis['skills_suggestions'] = skills_suggestions
    
    # 8. ATS Explanation
    analysis['ats_explanation'] = generate_ats_explanation(ats_score)
    
    return analysis

def calculate_advanced_ats_score(text, keywords):
    """Advanced ATS score calculation with detailed criteria."""
    score = 0
    text_lower = text.lower()
    word_count = len(re.findall(r'\w+', text))
    
    # 1. Keyword Density & Relevance (Max 30 points)
    keyword_score = min(30, len(keywords) * 3)
    score += keyword_score
    
    # 2. Quantified Achievements (Max 25 points)
    quantified_patterns = [
        r'\d+\s*(%|percent|million|thousand|k|lakhs|x|\$|\£|\€)',
        r'\d+\s*(years?|months?|days?)\s+of',
        r'increased|decreased|improved|reduced|saved|generated|achieved',
        r'\d+\s*(times?|fold|people|users|customers|clients)'
    ]
    quantified_count = sum(len(re.findall(pattern, text_lower)) for pattern in quantified_patterns)
    quantified_score = min(25, quantified_count * 2)
    score += quantified_score
    
    # 3. Action Verbs Usage (Max 15 points)
    action_verb_count = sum(len(re.findall(f'\\b{verb}\\b', text_lower)) 
                           for verb_list in ACTION_VERBS.values() 
                           for verb in verb_list)
    action_score = min(15, action_verb_count * 1.5)
    score += action_score
    
    # 4. Resume Structure & Length (Max 15 points)
    structure_score = 0
    if 400 <= word_count <= 1000:
        structure_score = 15
    elif 300 <= word_count < 400 or 1000 < word_count <= 1500:
        structure_score = 10
    elif 200 <= word_count < 300 or 1500 < word_count <= 2000:
        structure_score = 5
    score += structure_score
    
    # 5. Contact Information & Professional Elements (Max 10 points)
    contact_score = 0
    if re.search(r'[\w\.-]+@[\w\.-]+', text_lower):
        contact_score += 3
    if re.search(r'\+?[\d\s\-\(\)]{10,}', text_lower):
        contact_score += 2
    if any(section in text_lower for section in ['experience', 'education', 'skills', 'summary']):
        contact_score += 5
    score += contact_score
    
    # 6. Industry-Specific Keywords (Max 5 points)
    industry_keyword_count = sum(len(re.findall(f'\\b{kw}\\b', text_lower)) 
                                for kw_list in INDUSTRY_KEYWORDS.values() 
                                for kw in kw_list)
    industry_score = min(5, industry_keyword_count * 0.5)
    score += industry_score
    
    return max(0, min(100, int(score)))

def predict_job_roles_with_scores(keywords, text):
    """Predict job roles with match percentages based on skills and content."""
    text_lower = text.lower()
    role_matches = []
    
    for role, skills in BASE_SKILLS.items():
        # Calculate skill overlap
        skill_matches = sum(1 for skill in skills if skill in keywords or skill in text_lower)
        skill_match_percentage = (skill_matches / len(skills)) * 100
        
        # Boost score for industry-specific keywords
        industry_boost = 0
        for industry, industry_kw in INDUSTRY_KEYWORDS.items():
            industry_matches = sum(1 for kw in industry_kw if kw in text_lower)
            industry_boost += industry_matches * 2
        
        # Calculate final match percentage
        final_score = min(100, skill_match_percentage + industry_boost)
        
        if final_score > 20:  # Only include roles with reasonable match
            role_matches.append({
                'role': role,
                'match_percentage': round(final_score, 1),
                'matched_skills': [skill for skill in skills if skill in keywords or skill in text_lower],
                'missing_skills': [skill for skill in skills if skill not in keywords and skill not in text_lower]
            })
    
    # Sort by match percentage and return top matches
    role_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return role_matches[:5]

def analyze_keyword_matches(keywords, predicted_roles):
    """Analyze keyword matches and missing keywords by role."""
    analysis = {}
    
    for role_data in predicted_roles:
        role = role_data['role']
        matched = role_data['matched_skills']
        missing = role_data['missing_skills'][:5]  # Top 5 missing skills
        
        analysis[role] = {
            'found_keywords': matched,
            'missing_keywords': missing,
            'keyword_density': len(matched),
            'improvement_needed': missing[:3] if missing else []
        }
    
    return analysis

def analyze_skill_gaps(keywords, predicted_roles):
    """Comprehensive skill gap analysis with detailed recommendations for 100% job match."""
    gaps = {}
    
    for role_data in predicted_roles:
        role = role_data['role']
        missing_skills = role_data['missing_skills']
        matched_skills = role_data['matched_skills']
        match_percentage = role_data['match_percentage']
        
        # Get comprehensive skill recommendations for the role
        skill_recommendations = get_comprehensive_skill_recommendations(role, matched_skills, missing_skills)
        
        gaps[role] = {
            'match_percentage': match_percentage,
            'current_skills': matched_skills,
            'critical_gaps': missing_skills[:5],
            'recommended_skills': skill_recommendations['recommended_skills'],
            'learning_path': skill_recommendations['learning_path'],
            'certifications': skill_recommendations['certifications'],
            'projects': skill_recommendations['projects'],
            'tools_platforms': skill_recommendations['tools_platforms'],
            'soft_skills': skill_recommendations['soft_skills'],
            'priority_level': 'High' if match_percentage > 70 else 'Medium' if match_percentage > 50 else 'Low',
            'gap_analysis': skill_recommendations['gap_analysis'],
            'action_plan': skill_recommendations['action_plan']
        }
    
    return gaps

def get_comprehensive_skill_recommendations(role, matched_skills, missing_skills):
    """Get comprehensive skill recommendations to achieve 100% job match."""
    
    # Comprehensive skill databases for each role
    role_skill_database = {
        'Data Analyst': {
            'technical_skills': {
                'programming': ['Python', 'R', 'SQL', 'JavaScript', 'VBA'],
                'tools': ['Excel', 'Tableau', 'Power BI', 'Google Analytics', 'Jupyter Notebook', 'Pandas', 'NumPy'],
                'databases': ['MySQL', 'PostgreSQL', 'MongoDB', 'SQL Server', 'Oracle'],
                'statistics': ['Statistical Analysis', 'A/B Testing', 'Regression Analysis', 'Data Visualization']
            },
            'soft_skills': ['Analytical Thinking', 'Problem Solving', 'Communication', 'Attention to Detail', 'Critical Thinking'],
            'certifications': ['Google Data Analytics Certificate', 'Microsoft Power BI Certification', 'Tableau Desktop Specialist', 'AWS Certified Data Analytics'],
            'projects': ['Sales Dashboard', 'Customer Segmentation Analysis', 'Predictive Analytics Model', 'Business Intelligence Report'],
            'learning_path': [
                'Week 1-2: Master Excel advanced functions and pivot tables',
                'Week 3-4: Learn SQL fundamentals and practice queries',
                'Week 5-8: Complete Python for Data Analysis course',
                'Week 9-12: Build 2-3 data visualization projects using Tableau/Power BI'
            ]
        },
        'Software Engineer': {
            'technical_skills': {
                'programming': ['Python', 'Java', 'JavaScript', 'C++', 'C#', 'Go', 'Rust'],
                'frameworks': ['React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Spring Boot', 'Node.js'],
                'tools': ['Git', 'Docker', 'Kubernetes', 'Jenkins', 'AWS', 'Azure', 'Linux'],
                'databases': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch']
            },
            'soft_skills': ['Problem Solving', 'Team Collaboration', 'Code Review', 'Technical Writing', 'Agile Development'],
            'certifications': ['AWS Certified Developer', 'Google Cloud Professional Developer', 'Microsoft Azure Developer', 'Oracle Java Certification'],
            'projects': ['Full-Stack Web Application', 'REST API Development', 'Microservices Architecture', 'Mobile App Development'],
            'learning_path': [
                'Week 1-4: Master one programming language (Python/Java)',
                'Week 5-8: Learn web development frameworks (React/Django)',
                'Week 9-12: Build 2-3 full-stack projects with database integration',
                'Week 13-16: Learn cloud platforms and DevOps tools'
            ]
        },
        'Project Manager': {
            'technical_skills': {
                'methodologies': ['Agile', 'Scrum', 'Kanban', 'Waterfall', 'Lean', 'Six Sigma'],
                'tools': ['JIRA', 'Asana', 'Trello', 'Microsoft Project', 'Confluence', 'Slack'],
                'analytics': ['Project Analytics', 'Risk Management', 'Budget Planning', 'Resource Allocation']
            },
            'soft_skills': ['Leadership', 'Communication', 'Negotiation', 'Time Management', 'Stakeholder Management', 'Conflict Resolution'],
            'certifications': ['PMP (Project Management Professional)', 'Certified ScrumMaster (CSM)', 'PRINCE2', 'Agile Certified Practitioner'],
            'projects': ['Software Development Project', 'Marketing Campaign Management', 'Process Improvement Initiative', 'Team Restructuring Project'],
            'learning_path': [
                'Week 1-2: Master project management fundamentals and methodologies',
                'Week 3-4: Learn Agile/Scrum frameworks and tools',
                'Week 5-8: Practice with project management software (JIRA, Asana)',
                'Week 9-12: Lead a small project and document lessons learned'
            ]
        },
        'HR Specialist': {
            'technical_skills': {
                'systems': ['Workday', 'BambooHR', 'ADP', 'SuccessFactors', 'Taleo', 'HRIS'],
                'analytics': ['HR Analytics', 'Recruitment Metrics', 'Employee Engagement Analysis', 'Performance Management'],
                'compliance': ['Labor Law', 'Employment Regulations', 'Diversity & Inclusion', 'Workplace Safety']
            },
            'soft_skills': ['Interpersonal Skills', 'Empathy', 'Confidentiality', 'Cultural Awareness', 'Conflict Resolution', 'Coaching'],
            'certifications': ['SHRM-CP', 'PHR (Professional in Human Resources)', 'CIPD', 'HR Analytics Certificate'],
            'projects': ['Employee Onboarding Program', 'Performance Review System', 'Diversity Initiative', 'Training Program Development'],
            'learning_path': [
                'Week 1-2: Master HR fundamentals and employment law',
                'Week 3-4: Learn HRIS systems and recruitment tools',
                'Week 5-8: Develop skills in employee relations and performance management',
                'Week 9-12: Create HR policies and procedures documentation'
            ]
        },
        'Marketing Specialist': {
            'technical_skills': {
                'digital_marketing': ['SEO', 'SEM', 'Google Ads', 'Facebook Ads', 'Email Marketing', 'Content Marketing'],
                'analytics': ['Google Analytics', 'Facebook Analytics', 'HubSpot', 'Mailchimp', 'Hootsuite'],
                'design': ['Canva', 'Adobe Creative Suite', 'Figma', 'Video Editing', 'Graphic Design']
            },
            'soft_skills': ['Creativity', 'Communication', 'Strategic Thinking', 'Brand Management', 'Customer Focus', 'Data Interpretation'],
            'certifications': ['Google Ads Certification', 'Facebook Blueprint', 'HubSpot Content Marketing', 'Google Analytics Certification'],
            'projects': ['Digital Marketing Campaign', 'Brand Awareness Strategy', 'Lead Generation Campaign', 'Social Media Strategy'],
            'learning_path': [
                'Week 1-2: Master digital marketing fundamentals and platforms',
                'Week 3-4: Learn SEO/SEM and paid advertising strategies',
                'Week 5-8: Develop content creation and social media skills',
                'Week 9-12: Execute a complete marketing campaign and measure results'
            ]
        },
        'Sales Representative': {
            'technical_skills': {
                'crm': ['Salesforce', 'HubSpot', 'Pipedrive', 'Zoho CRM', 'Microsoft Dynamics'],
                'tools': ['LinkedIn Sales Navigator', 'ZoomInfo', 'Calendly', 'DocuSign', 'Sales Analytics'],
                'platforms': ['B2B Sales', 'B2C Sales', 'E-commerce', 'Lead Generation', 'Sales Automation']
            },
            'soft_skills': ['Persuasion', 'Active Listening', 'Relationship Building', 'Negotiation', 'Resilience', 'Goal Orientation'],
            'certifications': ['Salesforce Certified Sales Cloud Consultant', 'HubSpot Sales Software', 'Challenger Sale Methodology', 'SPIN Selling'],
            'projects': ['Sales Territory Development', 'Customer Acquisition Campaign', 'Sales Process Optimization', 'Client Retention Program'],
            'learning_path': [
                'Week 1-2: Master sales fundamentals and CRM systems',
                'Week 3-4: Learn prospecting and lead generation techniques',
                'Week 5-8: Develop negotiation and closing skills',
                'Week 9-12: Build a sales pipeline and track performance metrics'
            ]
        },
        'Business Analyst': {
            'technical_skills': {
                'analysis': ['Requirements Gathering', 'Process Mapping', 'Data Analysis', 'Business Process Modeling'],
                'tools': ['Visio', 'Lucidchart', 'JIRA', 'Confluence', 'Power BI', 'Tableau'],
                'methodologies': ['Agile', 'Waterfall', 'Six Sigma', 'Lean', 'BPMN']
            },
            'soft_skills': ['Critical Thinking', 'Communication', 'Stakeholder Management', 'Problem Solving', 'Documentation', 'Presentation Skills'],
            'certifications': ['CBAP (Certified Business Analysis Professional)', 'PMI-PBA', 'Agile Analysis Certification', 'Six Sigma Green Belt'],
            'projects': ['Business Process Improvement', 'Requirements Documentation', 'System Implementation', 'Data Analysis Project'],
            'learning_path': [
                'Week 1-2: Master business analysis fundamentals and methodologies',
                'Week 3-4: Learn requirements gathering and documentation techniques',
                'Week 5-8: Develop skills in process mapping and data analysis',
                'Week 9-12: Complete a business analysis project from start to finish'
            ]
        }
    }
    
    # Get role-specific recommendations
    role_data = role_skill_database.get(role, {
        'technical_skills': {'general': ['Problem Solving', 'Analytical Thinking', 'Communication']},
        'soft_skills': ['Communication', 'Teamwork', 'Adaptability'],
        'certifications': ['Industry-specific certifications'],
        'projects': ['Relevant project experience'],
        'learning_path': ['Focus on role-specific skills and experience']
    })
    
    # Analyze gaps and create recommendations
    gap_analysis = analyze_specific_gaps(role, matched_skills, missing_skills, role_data)
    action_plan = create_action_plan(role, gap_analysis, role_data)
    
    return {
        'recommended_skills': get_priority_skills(role_data, missing_skills),
        'learning_path': role_data.get('learning_path', ['Focus on role-specific skills']),
        'certifications': role_data.get('certifications', ['Industry certifications']),
        'projects': role_data.get('projects', ['Relevant projects']),
        'tools_platforms': get_tools_platforms(role_data),
        'soft_skills': role_data.get('soft_skills', ['Communication', 'Teamwork']),
        'gap_analysis': gap_analysis,
        'action_plan': action_plan
    }

def analyze_specific_gaps(role, matched_skills, missing_skills, role_data):
    """Analyze specific skill gaps with detailed explanations."""
    analysis = {
        'critical_gaps': [],
        'moderate_gaps': [],
        'nice_to_have': [],
        'strengths': matched_skills,
        'recommendations': []
    }
    
    # Categorize missing skills by importance
    all_required_skills = []
    for category, skills in role_data.get('technical_skills', {}).items():
        all_required_skills.extend(skills)
    
    for skill in missing_skills:
        if skill.lower() in [s.lower() for s in all_required_skills[:10]]:
            analysis['critical_gaps'].append(skill)
        elif skill.lower() in [s.lower() for s in all_required_skills[10:20]]:
            analysis['moderate_gaps'].append(skill)
        else:
            analysis['nice_to_have'].append(skill)
    
    # Generate specific recommendations
    if analysis['critical_gaps']:
        analysis['recommendations'].append(f"Priority 1: Master {', '.join(analysis['critical_gaps'][:3])} - These are essential for {role} roles")
    
    if analysis['moderate_gaps']:
        analysis['recommendations'].append(f"Priority 2: Learn {', '.join(analysis['moderate_gaps'][:3])} - These will significantly improve your competitiveness")
    
    return analysis

def create_action_plan(role, gap_analysis, role_data):
    """Create a detailed action plan to achieve 100% job match."""
    action_plan = {
        'immediate_actions': [],
        'short_term_goals': [],
        'long_term_goals': [],
        'timeline': '12-16 weeks to achieve 100% job match potential'
    }
    
    # Immediate actions (Week 1-2)
    if gap_analysis['critical_gaps']:
        action_plan['immediate_actions'].append(f"Start learning {gap_analysis['critical_gaps'][0]} - highest priority skill")
        action_plan['immediate_actions'].append("Update resume with current skills and quantify achievements")
        action_plan['immediate_actions'].append("Begin building a portfolio project showcasing your skills")
    
    # Short-term goals (Week 3-8)
    action_plan['short_term_goals'].append("Complete 2-3 online courses in critical skills")
    action_plan['short_term_goals'].append("Build 1-2 portfolio projects demonstrating expertise")
    action_plan['short_term_goals'].append("Obtain 1 industry-relevant certification")
    
    # Long-term goals (Week 9-16)
    action_plan['long_term_goals'].append("Master all critical skills for the role")
    action_plan['long_term_goals'].append("Complete 3-4 portfolio projects")
    action_plan['long_term_goals'].append("Achieve 2-3 professional certifications")
    action_plan['long_term_goals'].append("Network with professionals in the field")
    
    return action_plan

def get_priority_skills(role_data, missing_skills):
    """Get prioritized skill recommendations."""
    priority_skills = []
    
    # Add critical missing skills first
    for category, skills in role_data.get('technical_skills', {}).items():
        for skill in skills[:5]:  # Top 5 skills per category
            if skill.lower() in [s.lower() for s in missing_skills]:
                priority_skills.append(skill)
    
    return priority_skills[:10]  # Top 10 priority skills

def get_tools_platforms(role_data):
    """Get recommended tools and platforms."""
    tools = []
    for category, skills in role_data.get('technical_skills', {}).items():
        if 'tools' in category.lower() or 'platforms' in category.lower():
            tools.extend(skills)
    return tools[:8]  # Top 8 tools/platforms

def generate_quantified_suggestions(text, keywords, predicted_roles):
    """Generate quantifiable bullet point improvements using X-Y-Z formula."""
    suggestions = []
    text_lower = text.lower()
    
    # Extract current bullet points or experience descriptions
    bullet_patterns = re.findall(r'[-•]\s*([^-\n]+)', text)
    
    # Generate improved versions for top 3 roles
    for i, role_data in enumerate(predicted_roles[:3]):
        role = role_data['role']
        matched_skills = role_data['matched_skills']
        
        # Create X-Y-Z formula examples based on role
        examples = generate_role_specific_examples(role, matched_skills)
        suggestions.extend(examples[:2])  # 2 examples per role
    
    return suggestions[:6]  # Limit to 6 total suggestions

def generate_role_specific_examples(role, matched_skills):
    """Generate role-specific X-Y-Z formula examples with concrete, actionable suggestions."""
    examples = []
    
    # Role-specific improvement examples with actual numbers and tools
    role_examples = {
        'Data Analyst': [
            {
                'weak_example': 'Responsible for data analysis tasks',
                'strong_example': 'Analyzed 15+ datasets using Python and SQL, improving data accuracy by 25% and reducing processing time by 40%',
                'role': role,
                'formula_explanation': 'Concrete example: 15+ datasets (Achievement) + Python/SQL (Tools) + 25% accuracy improvement (Measurable Result)'
            },
            {
                'weak_example': 'Created reports for management',
                'strong_example': 'Created 12 automated weekly reports using Tableau and Power BI, reducing manual work by 8 hours per week',
                'role': role,
                'formula_explanation': 'Specific metrics: 12 reports (Achievement) + Tableau/Power BI (Tools) + 8 hours saved (Measurable Result)'
            }
        ],
        'Software Engineer': [
            {
                'weak_example': 'Developed software applications',
                'strong_example': 'Developed 3 new features using React and Node.js, increasing user engagement by 35% and reducing page load time by 2.5 seconds',
                'role': role,
                'formula_explanation': 'Measurable impact: 3 features (Achievement) + React/Node.js (Technology) + 35% engagement increase (Result)'
            },
            {
                'weak_example': 'Worked on bug fixes and maintenance',
                'strong_example': 'Resolved 50+ critical bugs using Python and automated testing tools, improving system stability by 40%',
                'role': role,
                'formula_explanation': 'Quantified results: 50+ bugs fixed (Achievement) + Python/testing tools (Method) + 40% stability improvement (Result)'
            }
        ],
        'Project Manager': [
            {
                'weak_example': 'Managed project teams',
                'strong_example': 'Led 4 cross-functional projects using Agile methodology, delivering all projects 15% under budget and 2 weeks ahead of schedule',
                'role': role,
                'formula_explanation': 'Project metrics: 4 projects (Achievement) + Agile methodology (Method) + 15% budget savings (Result)'
            },
            {
                'weak_example': 'Coordinated team activities',
                'strong_example': 'Managed 8 team members using JIRA and Slack, improving team productivity by 30% and reducing project delivery time by 25%',
                'role': role,
                'formula_explanation': 'Team impact: 8 team members (Scale) + JIRA/Slack (Tools) + 30% productivity increase (Result)'
            }
        ],
        'HR Specialist': [
            {
                'weak_example': 'Handled recruitment processes',
                'strong_example': 'Streamlined hiring process using Workday HRIS, reducing time-to-hire by 20 days and improving candidate satisfaction by 45%',
                'role': role,
                'formula_explanation': 'HR metrics: Streamlined process (Achievement) + Workday HRIS (Tool) + 20 days reduction (Result)'
            },
            {
                'weak_example': 'Managed employee relations',
                'strong_example': 'Implemented employee wellness program using HR analytics, increasing retention by 25% and reducing turnover costs by $150K annually',
                'role': role,
                'formula_explanation': 'Retention impact: Wellness program (Achievement) + HR analytics (Method) + 25% retention increase (Result)'
            }
        ],
        'Marketing Specialist': [
            {
                'weak_example': 'Managed marketing campaigns',
                'strong_example': 'Executed 8 digital marketing campaigns using Google Ads and Facebook Ads, generating 2,500+ qualified leads and increasing ROI by 60%',
                'role': role,
                'formula_explanation': 'Campaign results: 8 campaigns (Achievement) + Google/Facebook Ads (Platforms) + 2,500 leads generated (Result)'
            },
            {
                'weak_example': 'Created marketing content',
                'strong_example': 'Optimized website content using SEO tools and A/B testing, increasing organic traffic by 80% and conversion rate by 35%',
                'role': role,
                'formula_explanation': 'SEO impact: Content optimization (Achievement) + SEO tools/A/B testing (Method) + 80% traffic increase (Result)'
            }
        ],
        'Sales Representative': [
            {
                'weak_example': 'Responsible for sales targets',
                'strong_example': 'Exceeded quarterly sales targets by 35% using CRM tools and consultative selling, generating $2.5M in revenue',
                'role': role,
                'formula_explanation': 'Sales achievement: 35% target exceed (Achievement) + CRM tools/consultative selling (Method) + $2.5M revenue (Result)'
            },
            {
                'weak_example': 'Managed client relationships',
                'strong_example': 'Built and maintained 150+ client relationships using Salesforce CRM, increasing customer retention by 40% and upsell revenue by $500K',
                'role': role,
                'formula_explanation': 'Relationship metrics: 150+ clients (Achievement) + Salesforce CRM (Tool) + 40% retention increase (Result)'
            }
        ],
        'Business Analyst': [
            {
                'weak_example': 'Analyzed business processes',
                'strong_example': 'Analyzed 12 business processes using data analytics and process mapping, identifying cost savings of $300K annually',
                'role': role,
                'formula_explanation': 'Process impact: 12 processes analyzed (Achievement) + Data analytics/process mapping (Method) + $300K savings (Result)'
            },
            {
                'weak_example': 'Created business requirements',
                'strong_example': 'Documented 25+ business requirements using Visio and JIRA, reducing project delivery time by 30% and improving stakeholder satisfaction by 50%',
                'role': role,
                'formula_explanation': 'Requirements impact: 25+ requirements (Achievement) + Visio/JIRA (Tools) + 30% time reduction (Result)'
            }
        ]
    }
    
    # Default examples for roles not specifically defined
    default_examples = [
        {
            'weak_example': 'Responsible for general tasks',
            'strong_example': 'Improved operational efficiency by 25% using process optimization and team collaboration, resulting in $100K cost savings',
            'role': role,
            'formula_explanation': 'General improvement: 25% efficiency increase (Achievement) + Process optimization (Method) + $100K savings (Result)'
        },
        {
            'weak_example': 'Worked on various projects',
            'strong_example': 'Completed 5 major projects using project management methodologies, delivering 100% on-time with 20% cost reduction',
            'role': role,
            'formula_explanation': 'Project success: 5 projects (Achievement) + Project management methodologies (Method) + 20% cost reduction (Result)'
        }
    ]
    
    # Get role-specific examples or use defaults
    examples_to_use = role_examples.get(role, default_examples)
    
    # Return top 2 examples for the role
    return examples_to_use[:2]

def generate_tailoring_advice(predicted_roles, keywords):
    """Generate role-specific tailoring advice."""
    advice = []
    
    for role_data in predicted_roles[:3]:
        role = role_data['role']
        match_pct = role_data['match_percentage']
        
        if match_pct > 70:
            advice.append(f'✅ Strong match for {role} ({match_pct}%) - Your resume aligns well with this role')
        elif match_pct > 50:
            advice.append(f'🔧 Good potential for {role} ({match_pct}%) - Add missing skills to improve match')
        else:
            advice.append(f'⚠️ Consider {role} ({match_pct}%) - Focus on relevant skills and experience')
    
    return advice

def generate_ats_summary(text, keywords, predicted_roles):
    """Generate ATS-optimized professional summary."""
    if not predicted_roles:
        return "Results-driven professional with expertise in various domains. Seeking opportunities to apply skills and contribute to organizational success."
    
    top_role = predicted_roles[0]['role']
    matched_skills = predicted_roles[0]['matched_skills'][:5]  # Top 5 skills
    
    # Create industry-appropriate summary
    industry_context = get_industry_context(top_role)
    skills_text = ', '.join(matched_skills)
    
    summary = f"Results-driven {industry_context} with expertise in {skills_text}. "
    
    # Add quantified achievements if found in text
    quantified_found = re.search(r'\d+\s*(%|million|thousand|k)', text.lower())
    if quantified_found:
        summary += "Demonstrated success in optimizing processes and driving measurable performance improvements. "
    
    summary += f"Seeking to leverage technical skills and experience to contribute to {top_role} opportunities."
    
    return summary

def generate_ats_skills_section(keywords, predicted_roles):
    """Generate ATS-optimized skills section."""
    if not predicted_roles:
        return "Skills: " + ', '.join(keywords[:10])
    
    # Categorize skills
    technical_skills = []
    soft_skills = []
    tools_skills = []
    
    for role_data in predicted_roles:
        matched_skills = role_data['matched_skills']
        for skill in matched_skills:
            if any(tech in skill.lower() for tech in ['programming', 'software', 'database', 'cloud', 'api']):
                technical_skills.append(skill)
            elif any(tool in skill.lower() for tool in ['excel', 'tableau', 'powerbi', 'jira', 'git']):
                tools_skills.append(skill)
            else:
                soft_skills.append(skill)
    
    # Remove duplicates and limit
    technical_skills = list(set(technical_skills))[:8]
    soft_skills = list(set(soft_skills))[:6]
    tools_skills = list(set(tools_skills))[:6]
    
    skills_text = "Technical Skills: " + ', '.join(technical_skills)
    if tools_skills:
        skills_text += " | Tools: " + ', '.join(tools_skills)
    if soft_skills:
        skills_text += " | Professional Skills: " + ', '.join(soft_skills)
    
    return skills_text

def get_industry_context(role):
    """Get industry context for role."""
    context_map = {
        'Data Analyst': 'data professional',
        'Software Engineer': 'software developer',
        'Project Manager': 'project management professional',
        'HR Specialist': 'human resources professional',
        'Marketing Specialist': 'marketing professional',
        'Sales Representative': 'sales professional'
    }
    return context_map.get(role, 'professional')

def generate_ats_explanation(score):
    """Generate explanation of ATS scoring."""
    if score >= 90:
        level = "Excellent"
        explanation = "Your resume is highly ATS-optimized with strong keyword density, quantified achievements, and proper structure."
    elif score >= 80:
        level = "Good"
        explanation = "Your resume has a solid foundation but can be improved with more quantified achievements and keyword optimization."
    elif score >= 70:
        level = "Fair"
        explanation = "Your resume needs improvement in keyword density, quantified results, and ATS-friendly formatting."
    elif score >= 60:
        level = "Poor"
        explanation = "Your resume requires significant improvements in structure, keywords, and quantified achievements."
    else:
        level = "Very Poor"
        explanation = "Your resume needs major improvements across all ATS criteria including keywords, structure, and achievements."
    
    return f"ATS Score: {score}/100 ({level}) - {explanation}"

def calculate_resume_score(text, keywords):
    """Legacy function - now calls the advanced analysis."""
    return calculate_advanced_ats_score(text, keywords)

def analyze_for_improvements(score, text, keywords):
    """Provides personalized feedback based on the resume score."""
    feedback = []
    text_lower = text.lower()
    
    if score < 86:
        feedback.append("Your resume could use some improvements to get a 'Great' score.")
    
    if len(keywords) < 3:
        feedback.append("You have few relevant keywords. Try adding more skills and industry-specific terms.")

    if not re.search(r'\d+\s*(%|million|thousand|k|lakhs|x)', text_lower):
        feedback.append("Include numbers or metrics to quantify your achievements (e.g., 'increased sales by 15%').")
        
    weak_verbs = ["responsible for", "worked on", "assisted in", "helped"]
    if any(verb in text_lower for verb in weak_verbs):
        feedback.append("Try using stronger action verbs to start your bullet points (e.g., 'managed', 'developed', 'implemented').")

    word_count = len(re.findall(r'\w+', text))
    if word_count < 300:
        feedback.append("Your resume is quite short. Expand on your experiences and projects to provide more detail.")
    if word_count > 800:
        feedback.append("Your resume might be too long. Consider keeping it to 1-2 pages for readability.")

    if not feedback:
        feedback.append("Your resume is well-optimized and looks great! 🎉")
        
    return feedback

def is_valid_resume_content(text):
    """Checks if a document is likely a resume based on a simple heuristic."""
    text_lower = text.lower()
    word_count = len(re.findall(r'\w+', text_lower))
    
    # 1. Length Check
    if word_count < 150 or word_count > 2000:
        return False
        
    # 2. Keyword Check
    resume_keywords = ["education", "skills", "experience", "projects", "certifications", "summary"]
    
    # Check for at least 2 common resume section keywords
    found_keywords = sum(1 for keyword in resume_keywords if keyword in text_lower)
    if found_keywords < 2:
        return False
        
    # 3. Contact Info Check (simple email check)
    if not re.search(r'[\w\.-]+@[\w\.-]+', text_lower):
        return False
        
    return True

def generate_ats_pdf(resume_data):
    """
    Generates an ATS-friendly PDF resume using ReportLab.
    Handles both freshers and experienced professionals.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                          topMargin=0.5*inch, 
                          bottomMargin=0.5*inch,
                          leftMargin=0.5*inch,
                          rightMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles for ATS optimization
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=6,
        textColor=colors.HexColor('#2c3e50'),
        borderBottom=1,
        borderColor=colors.HexColor('#bdc3c7')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        spaceAfter=6
    )
    
    story = []
    
    # Personal Details Section
    personal_info = resume_data.get('personal_details', {})
    name = personal_info.get('full_name', '')
    email = personal_info.get('email', '')
    phone = personal_info.get('phone', '')
    location = personal_info.get('location', '')
    linkedin = personal_info.get('linkedin', '')
    github = personal_info.get('github', '')
    
    if name:
        story.append(Paragraph(name.upper(), title_style))
    
    contact_info = []
    if phone:
        contact_info.append(phone)
    if email:
        contact_info.append(email)
    if location:
        contact_info.append(location)
    if linkedin:
        contact_info.append(f"LinkedIn: {linkedin}")
    if github:
        contact_info.append(f"GitHub: {github}")
    
    if contact_info:
        contact_paragraph = Paragraph(" | ".join(contact_info), normal_style)
        story.append(contact_paragraph)
    
    story.append(Spacer(1, 0.2*inch))
    
    # Professional Summary
    summary = resume_data.get('professional_summary', '')
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
        story.append(Paragraph(summary, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Technical Skills
    skills_data = resume_data.get('technical_skills', {})
    if skills_data:
        story.append(Paragraph("TECHNICAL SKILLS", heading_style))
        
        skills_text = []
        for category, skills in skills_data.items():
            if skills and skills.strip():
                skills_text.append(f"<b>{category}:</b> {skills}")
        
        if skills_text:
            skills_paragraph = Paragraph(" | ".join(skills_text), normal_style)
            story.append(skills_paragraph)
            story.append(Spacer(1, 0.1*inch))
    
    # Work Experience - Handle freshers
    is_fresher = resume_data.get('is_fresher', False)
    work_experience = resume_data.get('work_experience', [])
    
    if not is_fresher:
        # Check if the list contains at least one entry with non-empty content
        has_experience = False
        for exp in work_experience:
            if (exp.get('job_title', '').strip() or 
                exp.get('company', '').strip() or 
                exp.get('bullet_points', '').strip()):
                has_experience = True
                break

        if has_experience:
            story.append(Paragraph("WORK EXPERIENCE", heading_style))
            
            for exp in work_experience:
                job_title = exp.get('job_title', '')
                company = exp.get('company', '')
                start_date = exp.get('start_date', '')
                end_date = exp.get('end_date', '')
                bullet_points = exp.get('bullet_points', '').split('\n') if exp.get('bullet_points') else []
                
                # Skip this entry if it's completely empty
                if not (job_title.strip() or company.strip() or bullet_points):
                    continue
                
                # Job header
                job_header = f"<b>{job_title}</b>"
                if company:
                    job_header += f" | {company}"
                if start_date:
                    job_header += f" | {start_date} - {end_date if end_date else 'Present'}"
                
                story.append(Paragraph(job_header, normal_style))
                
                # Bullet points
                for point in bullet_points:
                    if point.strip():
                        story.append(Paragraph(f"• {point.strip()}", normal_style))
                
                story.append(Spacer(1, 0.05*inch))
            
            story.append(Spacer(1, 0.1*inch))
    else:
        # For freshers, add a note about focusing on education and skills
        fresher_note = "Recent graduate with strong academic background and technical skills. Seeking to apply knowledge and contribute to organizational success."
        story.append(Paragraph("CAREER OBJECTIVE", heading_style))
        story.append(Paragraph(fresher_note, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Education
    education = resume_data.get('education', [])
    has_education = False
    for edu in education:
        if (edu.get('degree', '').strip() or 
            edu.get('institution', '').strip()):
            has_education = True
            break

    if has_education:
        story.append(Paragraph("EDUCATION", heading_style))
        
        for edu in education:
            degree = edu.get('degree', '')
            institution = edu.get('institution', '')
            location = edu.get('location', '')
            graduation_year = edu.get('graduation_year', '')
            
            # Skip empty education entries
            if not (degree.strip() or institution.strip()):
                continue
            
            edu_text = f"<b>{degree}</b>"
            if institution:
                edu_text += f" | {institution}"
            if location:
                edu_text += f" | {location}"
            if graduation_year:
                edu_text += f" | {graduation_year}"
            
            story.append(Paragraph(edu_text, normal_style))
            story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.1*inch))
    
    # Certifications
    certifications = resume_data.get('certifications', [])
    has_certifications = False
    for cert in certifications:
        if (cert.get('certification_name', '').strip() or 
            cert.get('organization', '').strip()):
            has_certifications = True
            break

    if has_certifications:
        story.append(Paragraph("CERTIFICATIONS", heading_style))
        
        for cert in certifications:
            cert_name = cert.get('certification_name', '')
            organization = cert.get('organization', '')
            completion_date = cert.get('completion_date', '')
            
            # Skip empty certification entries
            if not (cert_name.strip() or organization.strip()):
                continue
            
            cert_text = f"<b>{cert_name}</b>"
            if organization:
                cert_text += f" | {organization}"
            if completion_date:
                cert_text += f" | {completion_date}"
            
            story.append(Paragraph(cert_text, normal_style))
            story.append(Spacer(1, 0.05*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def log_login(user_id):
    """Logs a user's login event in the logins table."""
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logins (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def log_resume_download(user_id, resume_id):
    """Logs a resume download event."""
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO resume_downloads (user_id, resume_id) VALUES (?, ?)', (user_id, resume_id))
    conn.commit()
    conn.close()

def init_db():
    """Initializes the database schema if tables do not already exist."""
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            security_question TEXT NOT NULL,
            security_answer_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT FALSE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_resumes (
            resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            suggestion TEXT,
            admin_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replied_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # NEW TABLES FOR RESUME GENERATOR
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generated_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            resume_data TEXT NOT NULL, -- JSON format storing all resume data
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            resume_id INTEGER,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (resume_id) REFERENCES generated_resumes (id)
        )
    ''')
    
    # Check for and create the admin user if it doesn't exist
    cursor.execute('SELECT email FROM users WHERE email = ?', ('admin@rezum.ai',))
    if not cursor.fetchone():
        admin_password = generate_password_hash('Admin@123')
        admin_security_answer = generate_password_hash('admin')
        cursor.execute('''
            INSERT INTO users (email, name, password_hash, security_question, security_answer_hash, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin@rezum.ai', 'Admin', admin_password, SECURITY_QUESTIONS[0], admin_security_answer, True))
    
    conn.commit()
    conn.close()

# --- Flask App Initialization ---

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

def get_db_connection():
    """Create and return a database connection with row factory."""
    conn = sqlite3.connect('rezumai.db')
    conn.row_factory = sqlite3.Row  # This enables name-based access to columns
    return conn
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# i18n configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
SUPPORTED_LANGUAGES = {'en': 'English'}
babel = Babel()

def select_locale() -> str:
    return session.get('lang', 'en')

babel.init_app(app, locale_selector=select_locale)

# Expose gettext and get_locale to Jinja
app.jinja_env.globals.update(_=gettext, get_locale=get_locale, SUPPORTED_LANGUAGES=SUPPORTED_LANGUAGES)

SECURITY_QUESTIONS = [
    "What is your favorite color?",
    "What is your favorite place?",
    "What was the name of your first school?",
    "What is your mother's maiden name?",
    "What was your first pet's name?",
    "In what city were you born?",
    "What is your favorite movie?",
    "What was your childhood nickname?"
]

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Flask Routes ---

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang not in SUPPORTED_LANGUAGES:
        lang = 'en'
    session['lang'] = lang
    next_url = request.referrer or url_for('index')
    return redirect(next_url)

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('rezumai.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, password_hash, is_admin FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['user_email'] = email
            session['user_name'] = user[1]
            session['is_admin'] = bool(user[3])
            log_login(session['user_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard' if session['is_admin'] else 'dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    return render_template('login.html', security_questions=SECURITY_QUESTIONS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        security_question = request.form['security_question'].strip()
        security_answer = request.form['security_answer'].strip()

        if not name or len(name) < 2:
            flash('Please enter a valid full name (min 2 characters).', 'danger')
            return render_template('register.html', security_questions=SECURITY_QUESTIONS)

        email_regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html', security_questions=SECURITY_QUESTIONS)

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html', security_questions=SECURITY_QUESTIONS)

        if len(password) < 6 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            flash('Password must be at least 6 characters and include letters and numbers.', 'danger')
            return render_template('register.html', security_questions=SECURITY_QUESTIONS)

        if not security_question:
            flash('Please select a security question.', 'danger')
            return render_template('register.html', security_questions=SECURITY_QUESTIONS)

        if not security_answer or len(security_answer) < 2:
            flash('Please provide a valid security answer.', 'danger')
            return render_template('register.html', security_questions=SECURITY_QUESTIONS)
        conn = sqlite3.connect('rezumai.db')
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        security_answer_hash = generate_password_hash(security_answer.lower())
        
        try:
            cursor.execute('''
                INSERT INTO users (email, name, password_hash, security_question, security_answer_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, name, password_hash, security_question, security_answer_hash))
            
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()
            flash('Email already registered! Please use a different email or log in.', 'danger')
            return render_template('register.html', security_questions=SECURITY_QUESTIONS)
            
    return render_template('register.html', security_questions=SECURITY_QUESTIONS)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        step = request.form.get('step', '1')
        if step == '1':
            email = request.form['email']
            conn = sqlite3.connect('rezumai.db')
            cursor = conn.cursor()
            cursor.execute('SELECT email, security_question FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            if user:
                session['reset_email'] = email
                return render_template('forgot_password.html', step=2, security_question=user[1], email=email)
            else:
                flash('Email not found!', 'danger')
        elif step == '2':
            email = session.get('reset_email')
            security_answer = request.form['security_answer']
            conn = sqlite3.connect('rezumai.db')
            cursor = conn.cursor()
            cursor.execute('SELECT security_answer_hash FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            if user and check_password_hash(user[0], security_answer.lower()):
                return render_template('forgot_password.html', step=3, email=email)
            else:
                flash('Incorrect security answer!', 'danger')
                return redirect(url_for('forgot_password'))
        elif step == '3':
            email = session.get('reset_email')
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            if new_password != confirm_password:
                flash('Passwords do not match!', 'danger')
                return render_template('forgot_password.html', step=3, email=email)
            conn = sqlite3.connect('rezumai.db')
            cursor = conn.cursor()
            new_password_hash = generate_password_hash(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (new_password_hash, email))
            conn.commit()
            conn.close()
            session.pop('reset_email', None)
            flash('Password updated successfully! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('forgot_password.html', step=1)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()

    cursor.execute('SELECT rating, suggestion, admin_reply, created_at, replied_at FROM feedback WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    user_feedback = cursor.fetchall()
    
    cursor.execute('SELECT filepath, uploaded_at FROM uploaded_resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1', (user_id,))
    last_resume = cursor.fetchone()

    # Get latest generated resume data
    cursor.execute('SELECT id, resume_data, created_at FROM generated_resumes WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,))
    latest_resume = cursor.fetchone()
    
@app.route('/save_resume', methods=['POST'])
def save_resume():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'You must be logged in to save a resume.'})
    
    try:
        # Get resume data from form
        resume_data = request.get_json()
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert or update resume
        cursor.execute('''
            INSERT INTO generated_resumes (user_id, resume_data)
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET 
                resume_data = excluded.resume_data,
                updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], json.dumps(resume_data)))
        
        resume_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'resume_id': resume_id, 'message': 'Resume saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving resume: {str(e)}'})

@app.route('/generate_resume_pdf', methods=['POST'])
def generate_resume_pdf():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'You must be logged in to generate a resume.'})
    
    try:
        # Get resume data from request
        resume_data = request.get_json()
        
        # Generate PDF
        pdf_buffer = generate_ats_pdf(resume_data)
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert resume data
        cursor.execute('''
            INSERT INTO generated_resumes (user_id, resume_data)
            VALUES (?, ?)
        ''', (session['user_id'], json.dumps(resume_data)))
        
        resume_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return PDF
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'resume_{session["user_email"]}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error generating resume: {str(e)}'})

@app.route('/download_resume_pdf/<int:resume_id>')
def download_resume_pdf(resume_id):
    if 'user_id' not in session:
        flash('You must be logged in to download a resume.', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Get resume data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT resume_data FROM generated_resumes 
            WHERE id = ? AND user_id = ?
        ''', (resume_id, session['user_id']))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            flash('Resume not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        resume_data = json.loads(result['resume_data'])
        
        # Generate PDF
        pdf_buffer = generate_ats_pdf(resume_data)
        
        # Log download
        log_resume_download(session['user_id'], resume_id)
        
        # Return PDF
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'resume_{session["user_email"]}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating resume: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()

    cursor.execute('SELECT rating, suggestion, admin_reply, created_at, replied_at FROM feedback WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    user_feedback = cursor.fetchall()
    
    cursor.execute('SELECT filepath, uploaded_at FROM uploaded_resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1', (user_id,))
    last_resume = cursor.fetchone()

    # Get latest generated resume data
    cursor.execute('SELECT id, resume_data, created_at FROM generated_resumes WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,))
    latest_resume = cursor.fetchone()
    
    generated_resume_data = None
    if latest_resume:
        resume_id, resume_json, created_at = latest_resume
        generated_resume_data = {
            'id': resume_id,
            'data': json.loads(resume_json),
            'created_at': created_at
        }

    last_analysis = None
    if last_resume:
        filepath = last_resume[0]
        uploaded_at = last_resume[1]
        text = extract_text_from_resume(filepath)
        if text:  # Only analyze if text extraction was successful
            keywords = extract_keywords(text)
            
            # Use comprehensive ATS analysis
            comprehensive_analysis = comprehensive_ats_analysis(text, keywords)
            
            # Get jobs for top predicted roles
            top_roles = [match['role'] for match in comprehensive_analysis['job_matches'][:3]]
            jobs = fetch_jobs(top_roles, keywords)

            last_analysis = {
                "keywords": keywords,
                "predicted_role": ", ".join(top_roles),
                "jobs": jobs,
                "timestamp": uploaded_at,
                "resume_score": comprehensive_analysis['ats_score'],
                "improvement_feedback": comprehensive_analysis['improvements'],
                "recommendation_label": get_recommendation_label(comprehensive_analysis['ats_score']),
                # Advanced analysis data
                "job_matches": comprehensive_analysis['job_matches'],
                "keyword_analysis": comprehensive_analysis['keyword_analysis'],
                "skill_gaps": comprehensive_analysis['skill_gaps'],
                "quantified_suggestions": comprehensive_analysis['quantified_suggestions'],
                "summary_suggestions": comprehensive_analysis['summary_suggestions'],
                "skills_suggestions": comprehensive_analysis['skills_suggestions'],
                "ats_explanation": comprehensive_analysis['ats_explanation']
            }
    
    conn.close()

    return render_template(
        'dashboard.html',
        user_feedback=user_feedback,
        last_analysis=last_analysis,
        generated_resume=generated_resume_data
    )

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    
    # Existing queries for the stats cards and recent activity tables
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = FALSE')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM uploaded_resumes')
    total_uploads = cursor.fetchone()[0]
    cursor.execute('SELECT AVG(CAST(rating AS FLOAT)) FROM feedback')
    avg_rating_result = cursor.fetchone()[0]
    avg_rating = round(avg_rating_result, 1) if avg_rating_result else 0
    cursor.execute('SELECT COUNT(*) FROM resume_downloads')
    total_downloads = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT u.email, u.name, l.login_time FROM logins l 
        JOIN users u ON l.user_id = u.id
        ORDER BY l.login_time DESC LIMIT 10
    ''')
    recent_logins = cursor.fetchall()
    
    cursor.execute('''
        SELECT r.filename, u.email, r.uploaded_at 
        FROM uploaded_resumes r 
        JOIN users u ON r.user_id = u.id 
        ORDER BY r.uploaded_at DESC LIMIT 10
    ''')
    recent_uploads = cursor.fetchall()
    
    cursor.execute('''
        SELECT f.id, u.name, f.rating, f.suggestion, f.admin_reply, f.created_at 
        FROM feedback f 
        JOIN users u ON f.user_id = u.id
        ORDER BY f.created_at DESC
    ''')
    all_feedback = cursor.fetchall()

    # --- Queries for chart data ---
    cursor.execute("SELECT DATE(login_time) as login_date, COUNT(*) FROM logins GROUP BY login_date ORDER BY login_date")
    daily_logins_data = cursor.fetchall()
    login_labels = [row[0] for row in daily_logins_data]
    login_counts = [row[1] for row in daily_logins_data]

    cursor.execute("SELECT DATE(uploaded_at) as upload_date, COUNT(*) FROM uploaded_resumes GROUP BY upload_date ORDER BY upload_date")
    daily_uploads_data = cursor.fetchall()
    upload_labels = [row[0] for row in daily_uploads_data]
    upload_counts = [row[1] for row in daily_uploads_data]

    cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating")
    feedback_ratings_data = cursor.fetchall()
    rating_labels = [f"{row[0]} Stars" for row in feedback_ratings_data]
    rating_counts = [row[1] for row in feedback_ratings_data]

    # New queries for resume downloads chart
    cursor.execute("SELECT DATE(downloaded_at) as download_date, COUNT(*) FROM resume_downloads GROUP BY download_date ORDER BY download_date")
    daily_downloads_data = cursor.fetchall()
    download_labels = [row[0] for row in daily_downloads_data]
    download_counts = [row[1] for row in daily_downloads_data]

    conn.close()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_uploads=total_uploads,
                           avg_rating=avg_rating,
                           total_downloads=total_downloads,
                           recent_logins=recent_logins,
                           recent_uploads=recent_uploads,
                           all_feedback=all_feedback,
                           login_labels=json.dumps(login_labels),
                           login_counts=json.dumps(login_counts),
                           upload_labels=json.dumps(upload_labels),
                           upload_counts=json.dumps(upload_counts),
                           rating_labels=json.dumps(rating_labels),
                           rating_counts=json.dumps(rating_counts),
                           download_labels=json.dumps(download_labels),
                           download_counts=json.dumps(download_counts))

# Live metrics endpoint for admin dashboard auto-refresh
@app.route('/admin_metrics')
def admin_metrics():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()

    # KPIs
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM uploaded_resumes')
    total_uploads = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM resume_downloads')
    total_downloads = cursor.fetchone()[0]
    cursor.execute('SELECT AVG(rating) FROM feedback')
    avg_rating = round(cursor.fetchone()[0] or 0, 2)

    # Charts
    cursor.execute("SELECT DATE(login_time) as d, COUNT(*) FROM logins GROUP BY d ORDER BY d")
    daily_logins_data = cursor.fetchall()
    login_labels = [row[0] for row in daily_logins_data]
    login_counts = [row[1] for row in daily_logins_data]

    cursor.execute("SELECT DATE(uploaded_at) as d, COUNT(*) FROM uploaded_resumes GROUP BY d ORDER BY d")
    daily_uploads_data = cursor.fetchall()
    upload_labels = [row[0] for row in daily_uploads_data]
    upload_counts = [row[1] for row in daily_uploads_data]

    cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating")
    feedback_ratings_data = cursor.fetchall()
    rating_labels = [f"{row[0]} Stars" for row in feedback_ratings_data]
    rating_counts = [row[1] for row in feedback_ratings_data]

    cursor.execute("SELECT DATE(downloaded_at) as d, COUNT(*) FROM resume_downloads GROUP BY d ORDER BY d")
    daily_downloads_data = cursor.fetchall()
    download_labels = [row[0] for row in daily_downloads_data]
    download_counts = [row[1] for row in daily_downloads_data]

    conn.close()

    return jsonify({
        'success': True,
        'data': {
            'kpis': {
                'total_users': total_users,
                'total_uploads': total_uploads,
                'avg_rating': avg_rating,
                'total_downloads': total_downloads
            },
            'login_labels': login_labels,
            'login_counts': login_counts,
            'upload_labels': upload_labels,
            'upload_counts': upload_counts,
            'rating_labels': rating_labels,
            'rating_counts': rating_counts,
            'download_labels': download_labels,
            'download_counts': download_counts
        }
    })

@app.route('/resume_builder')
def resume_builder():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's existing resume data if any
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user has any saved resumes
    cursor.execute('SELECT * FROM resumes WHERE user_id = ?', (session['user_id'],))
    resume = cursor.fetchone()
    
    resume_data = {
        'personal_info': {},
        'education': [],
        'experience': [],
        'skills': [],
        'projects': [],
        'certifications': [],
        'achievements': []
    }
    
    if resume:
        # Get resume sections
        cursor.execute('''
            SELECT section_type, section_data 
            FROM resume_sections 
            WHERE resume_id = ?
            ORDER BY display_order
        ''', (resume['id'],))
        
        for section in cursor.fetchall():
            section_data = json.loads(section['section_data'])
            if section['section_type'] == 'personal':
                resume_data['personal_info'] = section_data
            else:
                resume_data[f"{section['section_type']}s"].append(section_data)
    
    conn.close()
    
    return render_template('resume_builder.html', 
                         resume=resume_data,
                         resume_id=resume['id'] if resume else None)

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'You must be logged in to upload a resume.'})
        
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['resume']
    if file.filename == '' or file.filename is None:
        return jsonify({'success': False, 'message': 'No file selected'})

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Only PDF, DOC, DOCX allowed.'})

    user_id = session['user_id']
    filename = secure_filename(file.filename) if file.filename else 'resume'
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    text = extract_text_from_resume(save_path)

    # Check if text extraction was successful
    if not text or len(text.strip()) < 50:
        os.remove(save_path)
        return jsonify({'success': False, 'message': 'Could not extract text from the resume. Please ensure the file is not corrupted or password protected.'})

    # --- Validation Check: Is this document likely a resume? ---
    if not is_valid_resume_content(text):
        os.remove(save_path) # Delete the file if it's not a resume
        return jsonify({'success': False, 'message': 'This document does not appear to be a resume. Please upload a valid resume document.'})


    keywords = extract_keywords(text)

    # Use comprehensive ATS analysis
    comprehensive_analysis = comprehensive_ats_analysis(text, keywords)
    
    # Get jobs for top predicted roles
    top_roles = [match['role'] for match in comprehensive_analysis['job_matches'][:3]]
    recommended_jobs = fetch_jobs(top_roles, keywords)

    conn = sqlite3.connect('rezumai.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO uploaded_resumes (user_id, filename, filepath) VALUES (?, ?, ?)",
        (user_id, filename, save_path)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Resume uploaded successfully",
        "uploaded_filename": filename,
        "keywords": keywords,
        "predicted_role": top_roles,
        "recommended_jobs": recommended_jobs,
        "resume_score": comprehensive_analysis['ats_score'],
        "improvement_feedback": comprehensive_analysis['improvements'],
        "recommendation_label": get_recommendation_label(comprehensive_analysis['ats_score']),
        # Advanced analysis data
        "job_matches": comprehensive_analysis['job_matches'],
        "keyword_analysis": comprehensive_analysis['keyword_analysis'],
        "skill_gaps": comprehensive_analysis['skill_gaps'],
        "quantified_suggestions": comprehensive_analysis['quantified_suggestions'],
        "summary_suggestions": comprehensive_analysis['summary_suggestions'],
        "skills_suggestions": comprehensive_analysis['skills_suggestions'],
        "ats_explanation": comprehensive_analysis['ats_explanation']
    })

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    rating = int(request.form['rating'])
    suggestion = request.form.get('suggestion', '')
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO feedback (user_id, rating, suggestion) VALUES (?, ?, ?)',
                   (session['user_id'], rating, suggestion))
    conn.commit()
    conn.close()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reply_feedback', methods=['POST'])
def reply_feedback():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    feedback_id = request.form['feedback_id']
    admin_reply = request.form['admin_reply']
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE feedback SET admin_reply = ?, replied_at = CURRENT_TIMESTAMP WHERE id = ?',
                   (admin_reply, feedback_id))
    conn.commit()
    conn.close()
    flash('Reply sent successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/chat', methods=['POST'])
def chat():
    """AI-powered chat endpoint for resume assistance."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'message': 'Please provide a message'})
    
    # Get user's latest resume analysis for context
    user_id = session['user_id']
    conn = sqlite3.connect('rezumai.db')
    cursor = conn.cursor()
    
    # Get latest uploaded resume analysis
    cursor.execute('SELECT filepath, uploaded_at FROM uploaded_resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1', (user_id,))
    last_resume = cursor.fetchone()
    
    context = ""
    if last_resume:
        text = extract_text_from_resume(last_resume[0])
        if text:
            keywords = extract_keywords(text)
            analysis = comprehensive_ats_analysis(text, keywords)
            context = f"User's resume analysis: {analysis['ats_explanation']}. Top job matches: {', '.join([match['role'] for match in analysis['job_matches'][:3]])}"
    
    conn.close()
    
    # Generate AI response based on message and context
    response = generate_ai_response(message, context)
    
    return jsonify({'success': True, 'response': response})

def generate_ai_response(message, context=""):
    """Generate AI response for resume assistance."""
    message_lower = message.lower()
    
    # Role- and degree-specific summaries (HTML formatted, no markdown asterisks)
    if any(w in message_lower for w in ['summary', 'about', 'profile', 'objective']):
        # MCA summary
        if 'mca' in message_lower:
            return (
                "<div><strong>MCA Summary (Experienced)</strong><br>"
                "Results-driven Software Engineer with an MCA and [X]+ years in full-stack development. "
                "Expertise in designing scalable systems using Python/Java, REST APIs, and relational/NoSQL databases. "
                "Delivered <strong>[quantified results]</strong> by optimizing services and implementing CI/CD on cloud platforms. "
                "Seeking to drive impact in a product-focused team.</div>"
                "<div style='margin-top:8px;'><strong>MCA Summary (Fresher)</strong><br>"
                "MCA graduate with strong fundamentals in Data Structures, OOPs, and DBMS. Built projects in Python/JavaScript, "
                "including <strong>[project name]</strong> using Flask/React and SQL. Quick learner with hands-on Git, Docker basics, and cloud fundamentals. "
                "Eager to contribute to a high-growth engineering team.</div>"
            )
        # BCA summary
        if 'bca' in message_lower:
            return (
                "<div><strong>BCA Summary (Experienced)</strong><br>"
                "Technology professional with a BCA and [X]+ years across application development and support. "
                "Skilled in scripting (Python/JS), data handling (SQL), and automation for operational efficiency. "
                "Improved processes by <strong>[quantified result]</strong>. Seeking roles in application development or data-centric teams.</div>"
                "<div style='margin-top:8px;'><strong>BCA Summary (Fresher)</strong><br>"
                "BCA graduate with solid understanding of programming, web technologies, and databases. "
                "Built <strong>[project]</strong> demonstrating clean code and problem-solving. "
                "Motivated to learn modern frameworks and contribute to real-world products.</div>"
            )
        # Sales/Marketing summary
        if 'sales' in message_lower or 'marketing' in message_lower:
            return (
                "<div><strong>Sales Summary (Experienced)</strong><br>"
                "Target-driven Sales Professional with [X] years in B2B/B2C environments. Proven success in pipeline building, consultative selling, "
                "and CRM-driven forecasting, achieving <strong>[quantified achievements]</strong>. Adept at stakeholder management and cross-functional collaboration.</div>"
                "<div style='margin-top:8px;'><strong>Marketing Summary (Experienced)</strong><br>"
                "Marketing Specialist with [X] years across digital campaigns, SEO/SEM, content strategy, and analytics (GA, Search Console). "
                "Drove acquisition and retention with <strong>[quantified impact]</strong>. Comfortable with A/B testing and performance optimization.</div>"
                "<div style='margin-top:8px;'><strong>Fresher Template (Sales/Marketing)</strong><br>"
                "Graduate with internships/projects in digital marketing/sales enablement. Familiar with SEO/SEM, social media tools, and campaign analytics. "
                "Strong communication, research, and presentation skills.</div>"
            )
    
    # Skill suggestions
    if any(word in message_lower for word in ['skill', 'skills', 'technical', 'programming']):
        # Tailor suggestions by degree/track if mentioned
        if 'mca' in message_lower:
            return (
                "<div><strong>MCA Skill Focus</strong></div>"
                "<ul>"
                "<li>Programming: Python/Java, OOPs, data structures</li>"
                "<li>Backend & APIs: REST, Flask/Django/Spring</li>"
                "<li>Databases: SQL, normalization, basic NoSQL</li>"
                "<li>DevOps Basics: Git, CI/CD, Docker</li>"
                "<li>Cloud Fundamentals: AWS/Azure basics</li>"
                "</ul>"
            )
        if 'bca' in message_lower:
            return (
                "<div><strong>BCA Skill Focus</strong></div>"
                "<ul>"
                "<li>Core: Programming fundamentals, web (HTML/CSS/JS)</li>"
                "<li>Data: SQL, basic analytics with Excel/Python</li>"
                "<li>Tools: Git/GitHub, basic scripting</li>"
                "<li>Projects: CRUD apps, simple dashboards</li>"
                "</ul>"
            )
        if 'sales' in message_lower or 'marketing' in message_lower:
            return (
                "<div><strong>Sales/Marketing Skills</strong></div>"
                "<ul>"
                "<li>Sales: Prospecting, pipeline management, CRM (HubSpot/Salesforce)</li>"
                "<li>Marketing: SEO/SEM, content, campaign analytics (GA, Ads)</li>"
                "<li>Communication: Presentation, negotiation, stakeholder mgmt</li>"
                "</ul>"
            )
        # Generic fresher vs experienced
        if 'fresher' in message_lower or 'new' in message_lower or 'beginner' in message_lower:
            return (
                "<div><strong>Fresher Skill Roadmap</strong></div>"
                "<ul>"
                "<li>Programming: Python/Java/JS</li>"
                "<li>Web basics: HTML/CSS, HTTP</li>"
                "<li>Databases: SQL</li>"
                "<li>Version Control: Git</li>"
                "<li>Projects: 2-3 hands-on projects</li>"
                "</ul>"
                "<div>Want suggestions tailored to MCA/BCA/Sales/Marketing? Tell me your target role.</div>"
            )
        else:
            return (
                "<div><strong>Experienced Skills by Role</strong></div>"
                "<ul>"
                "<li><strong>Software Engineer:</strong> Advanced programming, system design, cloud, DevOps</li>"
                "<li><strong>Data Analyst:</strong> Advanced SQL, Python/R, Tableau/Power BI, statistics</li>"
                "<li><strong>Project Manager:</strong> Agile/Scrum, JIRA, stakeholder mgmt, risk</li>"
                "<li><strong>Marketing:</strong> Digital marketing, SEO/SEM, analytics tools, campaigns</li>"
                "</ul>"
                "<div><strong>Universal:</strong> Leadership, strategy, collaboration, certifications</div>"
                "<div style='margin-top:6px;'>What specific role or industry are you targeting?</div>"
            )
    
    # Summary/About Me suggestions
    elif any(word in message_lower for word in ['summary', 'about', 'profile', 'objective']):
        if 'fresher' in message_lower:
            return (
                "<div><strong>Fresher Summary Template</strong></div>"
                "<div>Recent [Degree] graduate with strong foundation in [relevant skills]. Passionate about [field] with hands-on experience in [projects/internships]. "
                "Demonstrated ability to <strong>[specific achievement]</strong>. Seeking to contribute to [company type].</div>"
                "<div style='margin-top:8px;'><strong>Key Elements</strong></div>"
                "<ul><li>Degree and relevant skills</li><li>Projects/internships/certifications</li><li>Keep 3-4 sentences</li><li>Action verbs and specifics</li></ul>"
                "<div>Want me to personalize this? Share role, experience, and key skills.</div>"
            )
        else:
            return (
                "<div><strong>Experienced Summary Template</strong></div>"
                "<div>Results-driven [Role] with [X] years in [industry/domain]. Expertise in [key skills] with demonstrated success in <strong>[quantified achievements]</strong>. "
                "Strong background in [technologies/methodologies]. Seeking to drive [specific goals] in [target company type].</div>"
                "<div style='margin-top:8px;'><strong>Key Elements</strong></div>"
                "<ul><li>Role and years of experience</li><li>2-3 role-relevant skills</li><li>1-2 quantified achievements</li><li>Relevant tech/methodologies</li><li>Career goal</li></ul>"
                "<div>Share your role/domain for a customized version (MCA/BCA/IT/Sales/Marketing).</div>"
            )
    
    # ATS optimization
    elif any(word in message_lower for word in ['ats', 'optimization', 'optimize', 'score']):
        return (
            "<div><strong>ATS Optimization Tips</strong></div>"
            "<div style='margin-top:6px;'><strong>Keywords & Skills</strong></div>"
            "<ul><li>Use exact keywords from job descriptions</li><li>Add industry terminology</li><li>Include technical and soft skills</li><li>Use key term variations</li></ul>"
            "<div><strong>Formatting</strong></div>"
            "<ul><li>Standard headings (Experience, Education, Skills)</li><li>Avoid tables/graphics</li><li>Clean fonts (Arial/Calibri)</li><li>Text-based PDF or .docx</li></ul>"
            "<div><strong>Content Structure</strong></div>"
            "<ul><li>Quantifiable achievements</li><li>Strong action verbs</li><li>Concise bullet points</li><li>Clear contact info</li></ul>"
            "<div><strong>Length</strong></div>"
            "<ul><li>1-2 pages</li><li>400-1000 words</li><li>Prioritize relevance</li></ul>"
            "<div>Want targeted ATS improvements? Share your role and sample JD keywords.</div>"
        )
    
    # Job search advice
    elif any(word in message_lower for word in ['job', 'interview', 'application', 'search']):
        return (
            "<div><strong>Job Search Strategy</strong></div>"
            "<div style='margin-top:6px;'><strong>Resume Optimization</strong></div>"
            "<ul><li>Tailor for each application</li><li>Use JD keywords</li><li>Quantify achievements</li><li>Highlight relevant experience</li></ul>"
            "<div><strong>Application Process</strong></div>"
            "<ul><li>Apply within 24-48 hours</li><li>Custom cover letters</li><li>Follow up after 1-2 weeks</li><li>Professional contact info</li></ul>"
            "<div><strong>Interview Preparation</strong></div>"
            "<ul><li>Research company/role</li><li>Prepare STAR stories</li><li>Practice common questions</li><li>Prepare questions for interviewer</li></ul>"
            "<div><strong>Networking</strong></div>"
            "<ul><li>Optimize LinkedIn</li><li>Connect with professionals</li><li>Attend events/webinars</li><li>Leverage alumni</li></ul>"
            "<div>Tell me your target role to tailor this further.</div>"
        )
    
    # Default response
    else:
        return (
            f"<div>I'm here to help with your resume and career development! Based on your message about '<strong>{message}</strong>', here are ways I can assist:</div>"
            "<div style='margin-top:6px;'><strong>I can help with</strong></div>"
            "<ul><li>Skill suggestions for your target roles</li><li>Professional summaries and objectives</li><li>ATS optimization and keywords</li><li>Job search and interview prep</li><li>Career transitions</li><li>Resume formatting/structure</li></ul>"
            f"<div><strong>Current Context</strong>: {context if context else 'No resume analysis available. Upload a resume for personalized advice.'}</div>"
            "<div style='margin-top:6px;'><strong>Try asking</strong></div>"
            "<ul><li>Suggest skills for a data analyst fresher</li><li>Help write a summary for a software engineer</li><li>How to improve my ATS score?</li><li>Interview tips for project manager roles</li></ul>"
            "<div>What would you like to focus on today?</div>"
        )

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

# Prevent cached pages from being shown after logout (Back button protection)
@app.after_request
def add_no_cache_headers(response):
    try:
        if request.endpoint != 'static':
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
    except Exception:
        # In case request context is missing, just return response
        pass
    return response

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
