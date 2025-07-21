import os
import logging
import math
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from utils.resume_utils import (
    load_models,
    extract_text_from_pdf,
    preprocess_text,
    extract_skills_dynamic,
    normalize_skill,
    extract_qualifications,
    normalize_qualification,
    extract_experience,
    parse_required_experience,
    extract_work_experience_section,
    extract_work_periods,
    total_experience_in_months,
    format_months
)
from sklearn.metrics.pairwise import cosine_similarity
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:4000,https://jobscout2025.netlify.app').split(',')
CORS(app, resources={r"/*": {"origins": allowed_origins}})

# Initialize Firebase
try:
    firebase_key_path = os.getenv('FIREBASE_KEY_PATH', 'firebase_key.json')
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    raise

# Load ML models
try:
    nlp, model = load_models()
    logger.info("ML models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load ML models: {e}")
    raise

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Flask ML API is running!",
        "version": "1.0.0"
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Detailed health check endpoint"""
    try:
        # Test Firebase connection
        db.collection("test").limit(1).get()
        firebase_status = "healthy"
    except Exception as e:
        logger.error(f"Firebase health check failed: {e}")
        firebase_status = "unhealthy"

    return jsonify({
        "status": "healthy" if firebase_status == "healthy" else "degraded",
        "services": {
            "firebase": firebase_status,
            "ml_models": "healthy"
        }
    })

@app.route("/rank", methods=["POST"])
def rank_resumes():
    """Main endpoint for ranking resumes against job descriptions"""
    try:
        # Validate input
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        job_id = data.get("jobId")
        job_description = data.get("description")

        if not job_id or not job_description:
            return jsonify({"error": "jobId and jobDescription are required"}), 400

        logger.info(f"Processing ranking request for job ID: {job_id}")

        # Fetch resumes from Firestore
        resumes_ref = db.collection("resumes")
        query = resumes_ref.where("jobId", "==", job_id).stream()
        resumes = [doc.to_dict() for doc in query]

        if not resumes:
            logger.warning(f"No resumes found for job ID: {job_id}")
            return jsonify({"message": "No resumes found for this job"}), 404

        # Check for cached results
        rank_doc_ref = db.collection("resume_rankings").document(job_id)
        existing = rank_doc_ref.get()
        cached_data = existing.to_dict() if existing.exists else None

        # Validate cache against current resumes
        if cached_data and "ranked_resumes" in cached_data:
            cached_emails = {r.get("email") for r in cached_data["ranked_resumes"] if r.get("email")}
            current_emails = {r.get("email") for r in resumes if r.get("email")}

            if cached_emails == current_emails:
                logger.info("Using cached rankings - no new resumes detected")
                return jsonify(cached_data["ranked_resumes"])

            logger.info("Cache invalidated - new resumes detected, recomputing rankings")

        # Process resumes
        resume_texts = []
        resume_names = []
        resume_emails = []
        resume_urls = []

        for r in resumes:
            url = r.get("resumeURL")
            name = r.get("fullName")
            email = r.get("email")

            if not url:
                logger.warning(f"Skipping resume without URL for {name or email}")
                continue

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                pdf_bytes = BytesIO(response.content)
                text = extract_text_from_pdf(pdf_bytes)

                if not text.strip():
                    logger.warning(f"Empty text extracted from resume: {url}")
                    continue

                resume_texts.append(text)
                resume_names.append(name)
                resume_emails.append(email)
                resume_urls.append(url)

            except Exception as e:
                logger.error(f"Error processing resume from {url}: {e}")
                continue

        if not resume_texts:
            logger.warning("No valid resumes could be processed")
            return jsonify({"message": "No valid resumes could be processed"}), 404

        # Preprocess text data
        resumes_cleaned = [preprocess_text(txt) for txt in resume_texts]
        job_cleaned = preprocess_text(job_description)

        # Generate embeddings
        embeddings = model.encode(resumes_cleaned + [job_cleaned])
        resume_embeddings = embeddings[:-1]
        job_embedding = embeddings[-1].reshape(1, -1)

        similarity_scores = cosine_similarity(resume_embeddings, job_embedding).flatten()

        # Extract job requirements
        job_skills = [normalize_skill(s) for s in extract_skills_dynamic(job_description)]
        job_quals = [normalize_qualification(q) for q in extract_qualifications(job_description)]
        job_exps = extract_experience(job_description)
        job_min_exp, job_max_exp = parse_required_experience(job_exps)

        # Process each resume
        raw_scores = []
        candidate_data = []

        for i, score in enumerate(similarity_scores):
            text = resume_texts[i]
            resume_skills = [normalize_skill(s) for s in extract_skills_dynamic(text)]
            resume_quals = [normalize_qualification(q) for q in extract_qualifications(text)]
            work_section = extract_work_experience_section(text)
            resume_periods = extract_work_periods(work_section)
            total_months = total_experience_in_months(resume_periods)
            exp_value = format_months(total_months)

            # Experience matching logic
            experience_matched = False
            if job_min_exp is not None and total_months >= job_min_exp and (job_max_exp is None or total_months <= job_max_exp):
                exp_match_statement = "Experience matched"
                experience_matched = True
            elif job_min_exp is not None:
                exp_match_statement = "Experience not matched"
            else:
                exp_match_statement = "No experience requirement specified"
                experience_matched = True

            matched_skills = set(job_skills) & set(resume_skills)
            matched_quals = set(job_quals) & set(resume_quals)

            # Calculate skill F1 score
            if job_skills and resume_skills:
                precision = len(matched_skills) / len(resume_skills)
                recall = len(matched_skills) / len(job_skills)
                skill_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            else:
                skill_score = 0

            # Apply penalty for missing requirements
            final_score = skill_score
            if not experience_matched or not matched_skills or not matched_quals:
                final_score *= 0.3

            raw_scores.append(final_score)
            candidate_data.append({
                "name": resume_names[i],
                "email": resume_emails[i],
                "skills": list(matched_skills),
                "qualifications": list(matched_quals),
                "experience": exp_value,
                "Experience_Match": exp_match_statement,
                "url": resume_urls[i],
            })

        # Normalize scores using square root scaling
        if raw_scores:
            max_score = max(raw_scores)
            if max_score > 0:
                top_score = random.randint(91, 99)
                for i, r in enumerate(candidate_data):
                    sqrt_scaled = (math.sqrt(raw_scores[i]) / math.sqrt(max_score)) * top_score
                    r["score"] = round(sqrt_scaled, 2)

        # Sort and rank results
        sorted_results = sorted(candidate_data, key=lambda x: x["score"], reverse=True)
        for idx, r in enumerate(sorted_results):
            r["rank"] = idx + 1

        # Cache results in Firestore
        rank_doc_ref.set({"ranked_resumes": sorted_results})

        logger.info(f"Successfully ranked {len(sorted_results)} resumes for job {job_id}")
        return jsonify(sorted_results)

    except Exception as e:
        logger.error(f"Error in rank_resumes: {e}")
        return jsonify({"error": "Internal server error occurred while ranking resumes"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"Starting Flask ML API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)