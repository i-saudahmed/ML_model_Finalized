# ML Model API - Resume Ranking Service

A Flask-based machine learning API that ranks resumes against job descriptions using NLP and similarity scoring.

## Features

- Resume text extraction from PDF files
- Skill and qualification matching
- Experience requirement validation
- Semantic similarity scoring using sentence transformers
- Caching mechanism for improved performance
- Health monitoring endpoints
- Production-ready Docker configuration

## Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Firebase project with Firestore enabled
- spaCy English language model (`en_core_web_lg`)

## Installation

### Local Development

1. **Clone and navigate to the project:**
   ```bash
   cd ml_model
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_lg
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Add Firebase credentials:**
   - Place your `firebase_key.json` file in the ml_model directory
   - Ensure it has proper Firestore permissions

6. **Run the application:**
   ```bash
   python app.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually:**
   ```bash
   docker build -t ml-api .
   docker run -p 5001:5001 -v $(pwd)/firebase_key.json:/app/firebase_key.json:ro ml-api
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `PORT` | Server port | `5001` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `http://localhost:4000` |
| `FIREBASE_KEY_PATH` | Path to Firebase service account key | `firebase_key.json` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SECRET_KEY` | Flask secret key (required in production) | - |

## API Endpoints

### Health Check
- **GET** `/` - Basic health check
- **GET** `/health` - Detailed health check with service status

### Resume Ranking
- **POST** `/rank` - Rank resumes for a job

#### Request Body:
```json
{
  "jobId": "string",
  "description": "string"
}
```

#### Response:
```json
[
  {
    "rank": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "score": 85.67,
    "skills": ["python", "machine learning"],
    "qualifications": ["bachelor"],
    "experience": "3 years 6 months",
    "Experience_Match": "Experience matched",
    "url": "https://example.com/resume.pdf"
  }
]
```

## Production Deployment

### Security Considerations

1. **Environment Variables:**
   - Set a strong `SECRET_KEY`
   - Use environment-specific Firebase credentials
   - Configure appropriate `ALLOWED_ORIGINS`

2. **Firebase Security:**
   - Use service account with minimal required permissions
   - Enable Firestore security rules
   - Rotate credentials regularly

3. **Network Security:**
   - Deploy behind a reverse proxy (nginx, CloudFlare)
   - Use HTTPS in production
   - Implement rate limiting

### Scaling Considerations

1. **Horizontal Scaling:**
   - Use multiple worker processes with gunicorn
   - Deploy multiple container instances
   - Use a load balancer

2. **Performance Optimization:**
   - Model caching is built-in
   - Results are cached in Firestore
   - Consider Redis for additional caching

3. **Monitoring:**
   - Use the `/health` endpoint for health checks
   - Monitor logs for errors and performance
   - Set up alerts for service degradation

## Troubleshooting

### Common Issues

1. **spaCy model not found:**
   ```bash
   python -m spacy download en_core_web_lg
   ```

2. **Firebase connection errors:**
   - Verify `firebase_key.json` is present and valid
   - Check Firestore permissions
   - Ensure network connectivity

3. **Memory issues:**
   - ML models require significant RAM
   - Increase container memory limits
   - Consider model optimization

### Logs

Application logs include:
- Request processing information
- Error details with stack traces
- Performance metrics
- Health check results

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Code Quality
```bash
# Format code
black app.py utils/

# Lint code
flake8 app.py utils/
```

## License

This project is part of the JobScout application suite.
