import PyPDF2
import re
import spacy
import subprocess
from sentence_transformers import SentenceTransformer
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Load models (run only once)
def load_models():
    spacy_model = "en_core_web_lg"
    try:
        nlp = spacy.load(spacy_model)
    except OSError:
        subprocess.run(["python", "-m", "spacy", "download", spacy_model], check=True)
        nlp = spacy.load(spacy_model)
    model = SentenceTransformer("all-mpnet-base-v2")
    return nlp, model

# Extract text from PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + " "
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

# Clean text
def preprocess_text(text):
    text = re.sub(r'([a-zA-Z])\.([a-zA-Z])', r'\1.\2', text)
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9_\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Normalize skills
def normalize_skill(skill):
    skill = skill.lower()
    skill = re.sub(r'[\s\.\-]', '', skill)
    if skill.endswith('js'):
        skill = skill[:-2]
    skill = re.sub(r'[^a-z0-9]', '', skill)
    return skill

# Normalize qualifications
def normalize_qualification(q):
    q = q.lower()
    bachelor_terms = {'bachelor', 'bs', 'b.sc', 'bsc', 'bachelors'}
    master_terms = {'master', 'ms', 'msc', 'm.sc', 'm.tech', 'mtech', 'masters'}
    phd_terms = {'phd', 'ph.d', 'm.phil'}
    mba_terms = {'mba'}
    bba_terms = {'bba'}
    if q in bachelor_terms:
        return 'bachelor'
    if q in master_terms:
        return 'master'
    if q in phd_terms:
        return 'phd'
    if q in mba_terms:
        return 'mba'
    if q in bba_terms:
        return 'bba'
    return q

# Extract skills using NLP
def extract_skills_dynamic(text):
    nlp = spacy.load("en_core_web_lg")
    doc = nlp(text)
    skills = set()
    for chunk in doc.noun_chunks:
        if 1 < len(chunk.text) < 40:
            skills.add(chunk.text.strip().lower())
    for ent in doc.ents:
        if ent.label_ in ["SKILL", "LANGUAGE"]:
            skills.add(ent.text.strip().lower())
    skills = {s for s in skills if not nlp.vocab[s].is_stop and len(s) > 2}
    qualifications = set(extract_qualifications(text))
    return list(skills - qualifications)

# Extract qualifications
def extract_qualifications(text):
    pattern = r"\b(bachelor|bachelors|bachelor's|bs|b\.tech|bsc|master|masters|master's|ms|m\.tech|msc|phd|ph\.d|m\.phil|mba|bba|computer science|engineering|it|software|cs)\b"
    return list(set(re.findall(pattern, text.lower())))

# Extract experience patterns
def extract_experience(text):
    patterns = [
        r'(fresh\s*(?:to|-|–)\s*\d+\s*(?:years?|months?))',    # e.g. Fresh to 6 months
        r'(\d+\s*(?:to|-|–)\s*\d+\s*(?:years?|months?))',      # e.g. 1-2 years, 6 months - 1 year, 1 to 2 years
        r'(\d+\s*(?:years?|months?))',                         # e.g. 2 years, 6 months
    ] 
    matches = []
    for pattern in patterns:
        matches += re.findall(pattern, text.lower())
    return list(set(matches))

# Parse required experience
def parse_required_experience(job_exps):
    min_months, max_months = None, None
    all_mins, all_maxs = [], []
    for exp in job_exps:
        exp = exp.lower()
        if 'fresh' in exp:
            all_mins.append(0)
            match = re.search(r'fresh\s*(?:to|-|–)\s*(\d+)\s*months?', exp)
            if match:
                all_maxs.append(int(match.group(1)))
            continue
        match = re.search(r'(\d+)\s*(?:-|to|–)\s*(\d+)\s*months?', exp)
        if match:
            all_mins.append(int(match.group(1)))
            all_maxs.append(int(match.group(2)))
            continue
        match = re.search(r'(\d+)\s*(?:-|to|–)\s*(\d+)\s*years?', exp)
        if match:
            all_mins.append(int(match.group(1)) * 12)
            all_maxs.append(int(match.group(2)) * 12)
            continue
        match = re.search(r'(\d+)\s*years?', exp)
        if match:
            months = int(match.group(1)) * 12
            all_mins.append(months)
            all_maxs.append(months)
            continue
        match = re.search(r'(\d+)\s*months?', exp)
        if match:
            months = int(match.group(1))
            all_mins.append(months)
            all_maxs.append(months)
            continue
    if all_mins:
        min_months = min(all_mins)
    if all_maxs:
        max_months = max(all_maxs)
    return min_months, max_months

# Extract WORK EXPERIENCE section
def extract_work_experience_section(text):
    match = re.search(r'(WORK EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY)[:\s\n]*(.*?)(?:\n[A-Z][A-Z\s]+:|\Z)', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(2)
    match = re.search(r'(WORK EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY)[:\s\n]*(.*)', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(2)
    return ""

# Extract date periods from experience section
def extract_work_periods(text):
    pattern1 = r'([A-Za-z]{3,9} \d{4})\s*(?:–|-|to)\s*([A-Za-z]{3,9} \d{4}|current|present)'
    pattern2 = r'(\d{2}[/\-]\d{4})\s*(?:–|-|to)\s*(\d{2}[/\-]\d{4}|current|present)'
    matches = re.findall(pattern1, text, re.IGNORECASE) + re.findall(pattern2, text, re.IGNORECASE)
    periods = []
    for start, end in matches:
        try:
            start_date = date_parser.parse(start)
            end_date = datetime.today() if end.lower() in ['current', 'present'] else date_parser.parse(end)
            if end_date < start_date:
                continue
            delta = relativedelta(end_date, start_date)
            total_months = delta.years * 12 + delta.months
            if 0 <= total_months <= 600:
                periods.append(total_months)
        except Exception:
            continue
    return periods

# Calculate total months of experience
def total_experience_in_months(periods):
    return sum(periods)

# Format months into human-readable format
def format_months(months):
    years = months // 12
    rem_months = months % 12
    if years > 0:
        return f"{years} year{'s' if years > 1 else ''} {rem_months} month{'s' if rem_months != 1 else ''}".strip()
    else:
        return f"{rem_months} month{'s' if rem_months != 1 else ''}"
