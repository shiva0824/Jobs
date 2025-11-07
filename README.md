# Job Skill Extractor & Resume Matching Engine

An end-to-end NLP project for extracting skills from job descriptions, parsing resumes, and building a recommendation engine to match candidates with job-specific skill profiles.

---

## Contents

- [Step 1: Data Acquisition (Web Scraping)](#step-1-data-acquisition-web-scraping)
- [Step 2: ETL Data Preprocessing Pipeline](#step-2-etl-data-preprocessing-pipeline)
- [Step 3: Model Training](#step-3-model-training)
- [Step 4: Model API](#step-4-model-api)
- [Step 5: Recommendation Engine](#step-5-recommendation-engine)
- [Step 6: Web UI (SkillMatch AI Interface)](#step-6-web-ui-skillmatch-ai-interface)

---

## Step 1: Data Acquisition (Web Scraping)

The project began by building a high-quality dataset of job descriptions.  
A custom web scraping script was developed to collect postings from various job portals using the following job titles:

- Data Analyst
- Data Engineer
- Data Scientist
- Machine Learning Engineer
- Cloud Engineer
- Cybersecurity Analyst
- Full Stack Developer
- Software Developer
- DevOps Engineer
- Database Administrator

This process resulted in **4,429 raw job descriptions**, stored in JSON format.  
This dataset serves as the foundation for training the Named Entity Recognition (NER) model used for skill extraction.

---

## Step 2: ETL Data Preprocessing Pipeline

A robust, three-stage ETL pipeline was developed to prepare the raw data for model training, ensuring the final dataset is clean, balanced, and accurately labeled.

**Extract:** The pipeline reads raw job description data from the `data/raw` directory.

**Transform:** Modular scripts clean the text, perform sentence segmentation, and apply BIO-tagging based on a comprehensive list of technical and soft skills. To address data imbalance and prevent model bias, oversampling techniques duplicate sentences from underrepresented job roles.

**Load:** The processed dataset, formatted for model training, is saved to the `data/processed` directory.

This ETL pipeline ensures the model is trained on high-quality data, which is crucial for accurate and generalized skill extraction.

---

## Step 3: Model Training

Trained and evaluated **four Transformer models** for job skill Named Entity Recognition (NER):

- **BERT-base-cased**
- **DistilBERT-base-cased**
- **RoBERTa-base**
- **SpanBERT-base-cased**

### Setup

- **Training**: 2–4 epochs on Colab T4 GPU
- **Framework**: HuggingFace Transformers (Trainer API)
- **Tracking**: MLflow + DagsHub (metrics, hyperparameters, artifacts)
- **Evaluation**: Precision, Recall, F1, Accuracy, Loss
- **Post-processing**: Subword merge + Hybrid Dictionary Lookup (to reduce fragmentation and catch unseen skills)

---

### Results

| Model                     | Eval Accuracy |    Eval F1 | Eval Precision | Eval Recall |   Eval Loss |
| ------------------------- | ------------: | ---------: | -------------: | ----------: | ----------: |
| **BERT-base-cased**       |        0.9978 |     0.9856 |         0.9826 |      0.9886 |     0.00796 |
| **DistilBERT-base-cased** |    **0.9985** | **0.9902** |     **0.9872** |  **0.9933** |     0.00633 |
| **RoBERTa-base**          |        0.9983 |     0.9889 |         0.9863 |      0.9916 | **0.00601** |
| **SpanBERT-base-cased**   |        0.9973 |     0.9825 |         0.9775 |      0.9875 |     0.01131 |

---

### Visualization

Parallel coordinates comparing the four models across metrics:

![Model Comparison](docs/images/model_comparison.png)

_(Generated in DagsHub via MLflow experiment tracking.)_

---

### Conclusion

- **Best Overall F1 & Recall:** DistilBERT-base-cased
- **Cleanest Entities in Inference:** BERT-base-cased (less token fragmentation)
- **Close Runner-up:** RoBERTa-base (needs better BPE merging logic)
- **De-prioritized:** SpanBERT-base-cased (slightly weaker on this dataset)

**Final choice:**

- **Production model:** **BERT-base-cased** (balanced metrics + cleaner span predictions, easier downstream use).
- **Fast mode / backup:** DistilBERT-base-cased (best F1/recall, lightweight, faster inference).

---

## Step 4: Model API

The chosen model (**BERT-base-cased**) was wrapped into a production-grade **FastAPI** service, making skill extraction accessible via secure HTTP requests.

### Authentication

- **JWT-based authentication** secures all protected endpoints.
- `/auth/login` → Takes **username + password**, returns a **signed JWT access token**.
- Tokens embed:
  - `sub` → user identity
  - `exp` → token expiry
- Routes like `/api/predict` require a valid token.
- **Password Security**: User credentials are stored as **bcrypt-hashed passwords** (via `passlib`). Plain-text passwords are never stored.

### Skill Extraction Endpoint

**POST** `/api/predict`

- **Input**: JSON job description
- **Output**: Extracted skills in three categories:
  - `technical_skills`
  - `soft_skills`
  - `suggested` (model-only predictions below strict confidence thresholds)

**Example Request & Response**:

```bash
curl -X POST "http://localhost:8000/api/predict" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Looking for a Data Scientist with Python, SQL, and AWS experience. Strong communication skills required."}'

Response:
{
  "technical_skills": [
    "Python",
    "SQL",
    "AWS"
  ],
  "soft_skills": [
    "communication"
  ],
  "suggested": []
}
```

### Input Validation & Sanitization

Inputs are validated via **Pydantic models**.  
Raw job descriptions are sanitized before inference:

- Normalize whitespace & line endings
- Strip HTML tags and unwanted symbols
- Reject empty or malformed input

This ensures the API handles real-world messy job postings without errors.

### Inference Pipeline (`inference.py`)

The core service powering skill extraction:

**Model Inference**

- Loads **BERT-base-cased** (fine-tuned for NER)
- Performs subword merging and span reconstruction

**Hybrid Dictionary Lookup**

- Uses curated dictionaries (`lookup_phrases.json`) of technical, tool, language, and soft skills
- Guarantees recall for domain-specific terms not always captured by the model

**Advanced Postprocessing**

- Confidence-based filtering (0.92 for technical, 0.95 for suggested)
- Removes fragments (`Ten → TensorFlow`, `data pipeline` vs `data pipelines`)
- Deduplicates and normalizes casing (`PyTorch` over `pytorch`)

**Output:** clean, production-ready skill lists.  
This layered approach ensures both **precision** and **recall** while keeping results professional.

## Step 5: Recommendation Engine

This phase introduced resume parsing, skill suggestions, resume ↔ job description matching, and job recommendations.

### Resume Parsing

Endpoint: **POST** `/api/resume/parse`

- **Input**: Resume file (PDF/DOCX).
- **Output**:

```json
{
  "name": "Shiva Prasad",
  "skills": {
    "technical": ["Python", "SQL", "Machine Learning"],
    "soft": ["communication"]
  },
  "experience": "2 years"
}
```

#### Implementation details:

- Extracts text using pdfplumber (PDF) and python-docx (DOCX).
- Identifies skill sections via headers (Technical Skills, Core Skills, Tools & Technologies).
- Separates technical vs soft skills using skill_phrases.json.
- Regex-based fallback to capture years of experience.
- If no skills are extracted, API returns a message instructing the user to enter them manually.

#### Challenge faced:

Public resume NER models did not yield clean results, so pivoted to a section-based fallback approach, which proved more robust and explainable.

### Skill Suggestions (Autocomplete)

Endpoint: GET /api/skills/suggest?q=

- Loads skill_phrases.json into memory.
- Returns case-insensitive prefix matches (e.g., py → Python, PyTorch, PySpark).
- Limited to top 10 suggestions.
- Supports UI autocomplete when entering skills manually.

### Resume ↔ Job Description Matching

Endpoint: POST /api/match

Input:

```
{
"job_description": "Looking for a Data Engineer with Python, SQL, Airflow.",
"resume_skills": {
"technical": ["Python", "SQL", "Git"],
"soft": ["teamwork"]}
}
```

Output:

```
{
"match_score": 72,
"technical": {
"matched": ["Python", "SQL"],
"missing": ["Airflow"],
"extra": ["Git"]
},
"soft": {
"matched": ["teamwork"],
"missing": [],
"extra": []}
}
```

#### Scoring logic:

Weighted Jaccard similarity:

- 70% technical skills
- 30% soft skills

Outputs matched, missing, and extra skills for transparency.

### Job Recommendations

Endpoint: POST /api/recommend/jobs

Input: Candidate’s skills (parsed from resume).

Output: Ranked job recommendations with missing and extra skills.

```
{
"recommendations": [
{
"title": "Data Engineer",
"level": "mid",
"score": 65,
"breakdown": {
"technical": {
"matched": ["Python", "SQL"],
"missing": ["Airflow", "Kafka", "Spark"],
"extra": ["Git"]
},
"soft": {
"matched": ["teamwork"],
"missing": ["problem-solving"],
"extra": []}}
}
]
}
```

Knowledge Base (KB):

- Initially used static JSON (job_skill_kb.json).
- Migrated to Postgres for scalability:
  - roles table: job titles & levels
  - skills table: normalized skills
  - role_skills table: mapping between roles and skills

## Step 6: Web UI (SkillMatch AI Interface)

A fully responsive, interactive front-end built with **HTML / CSS / JavaScript**, designed to interact with the FastAPI backend.

### Pages:

- **Login Page:** Secure access using JWT-based auth.
- **Match Page:** Upload a job description and see extracted skills, missing/matched/extra analysis.
- **Recommendation Page:** Upload a resume to get AI-generated job suggestions.
- **About Page:** Explains how the AI works, data limitations, and privacy.

### Tech Highlights:

- Responsive design with custom CSS (no frameworks)
- FontAwesome icons + gradient theme
- Async JS fetch calls to backend APIs
- Dynamic loading overlay (SkillMatch AI animation)
- Error handling + feedback cards

## What's Next

Upcoming work will focus on full cloud deployment with **Terraform + AWS**:

- **FastAPI Deployment:** EC2 behind ALB + ACM (HTTPS)
- **Database:** PostgreSQL in RDS (private subnet)
- **Networking:** Custom VPC + public/private subnets + NAT gateway
- **Automation:** Cron patches, backups to S3
- **Frontend:** Netlify /Vercel hosting
