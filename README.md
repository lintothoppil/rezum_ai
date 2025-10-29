

## 🧠 RezumAI — AI-Powered Resume Reviewer + Resume Builder & Job Role Recommender

RezumAI is an intelligent web application that analyzes resumes using AI to provide personalized feedback, job-role recommendations, and skill-gap insights.
It helps job seekers build **ATS-friendly resumes** and discover roles that best match their profile.

---

### 🚀 Features

✅ **AI-Based Resume Analysis** – Evaluates resumes for structure, clarity, and keyword optimization.
✅ **Job Role Recommendation** – Suggests the most suitable job titles based on skills and experience.
✅ **ATS Score Calculation** – Predicts how well a resume performs in Applicant Tracking Systems.
✅ **Skill Gap Detection** – Identifies missing technical and soft skills for targeted improvement.
✅ **Resume Builder** – Allows users to create, edit, and download resumes dynamically.
✅ **Multi-Language Support** – Supports English, Hindi, and Malayalam (via translation files).
✅ **Admin Dashboard** – Manage users, feedback, and reports with data visualizations.

---

### 🏗️ Tech Stack

| Category        | Technologies Used                                          |
| --------------- | ---------------------------------------------------------- |
| **Frontend**    | HTML5, CSS3, JavaScript, Bootstrap                         |
| **Backend**     | Python (Flask Framework)                                   |
| **Database**    | SQLite / MySQL                                             |
| **AI Model**    | OpenAI GPT model for resume analysis & job recommendations |
| **Other Tools** | Flask-Babel, Jinja Templates, Pandas                       |

---

### ⚙️ Installation & Setup

#### 1️⃣ Clone the repository

```bash
git clone https://github.com/lintothoppil/rezum_ai.git
cd rezum_ai
```

#### 2️⃣ Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # On Windows
```

#### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

#### 4️⃣ Create a `.env` file

Inside your project folder, create a file named `.env` and add:

```bash
OPENAI_API_KEY=your_api_key_here
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

#### 5️⃣ Run the app

```bash
python app.py
```

Visit **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser 🚀

---

### 📂 Project Structure

```
rezum_ai/
│
├── app.py
├── static/
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── landing.html
│   └── register.html
├── uploads/
├── migrations/
├── translations/
├── requirements.txt
├── .gitignore
└── README.md
```

---

### 🧩 Future Enhancements

* Integration with LinkedIn for automatic profile imports
* AI-based resume formatting suggestions
* Cloud storage for saved resumes
* Multi-user authentication with role management

---

### 📧 Contact

👤 **Developer:** [Linto Joy Thoppil](https://github.com/lintothoppil)
💼 **Project:** RezumAI — Smart Resume & Job Role Assistant
📩 **Email:** [lintojoythoppil@gmail.com](mailto:lintojoythoppil@gmail.com)


If you say “yes,” I can generate the **ready-to-upload markdown file** and even give you the command to add and push it to your repo.
