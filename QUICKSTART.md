# Quick Start Guide - Summary Service

Get the summary generation service running in 5 minutes.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or use Docker Compose)
- OpenAI API key

## Option 1: Local Development

### 1. Set up environment

```bash
cd services/summary

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set:
```
OPENAI_API_KEY=your-actual-api-key-here
POSTGRES_HOST=localhost
POSTGRES_DB=propclaim
POSTGRES_USER=propclaim
POSTGRES_PASSWORD=changeme
```

### 3. Set up database

Make sure PostgreSQL is running, then:

```bash
# Create database
createdb propclaim

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 4. Run the service

```bash
python manage.py runserver 8002
```

The service will be available at `http://localhost:8002`

### 5. Test the API

```bash
# Generate a test summary
curl -X POST http://localhost:8002/api/summaries/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc-1", "doc-2"],
    "project_id": "test-project",
    "stakeholder_role": "developer",
    "focus_areas": ["technical", "quality"],
    "max_length": 500
  }'
```

Or use the management command:

```bash
python manage.py generate_test_summary --project-id test-proj --role developer
```

## Option 2: Docker Compose (Easiest)

### 1. Configure environment

```bash
cd services/summary
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your-actual-api-key-here
```

### 2. Start services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Summary service on port 8002

### 3. Run migrations

```bash
docker-compose exec summary python manage.py migrate
docker-compose exec summary python manage.py createsuperuser
```

### 4. Test the API

```bash
curl -X POST http://localhost:8002/api/summaries/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc-1", "doc-2"],
    "project_id": "test-project",
    "stakeholder_role": "executive",
    "max_length": 500
  }'
```

## Accessing the Admin Interface

1. Navigate to `http://localhost:8002/admin/`
2. Log in with the superuser credentials you created
3. You can view and manage:
   - Summary Jobs
   - Generated Summaries
   - Summary Sections
   - Document Contexts

## API Documentation

View the full API documentation in `API.md` or access:
- API endpoints: `http://localhost:8002/api/`
- Admin panel: `http://localhost:8002/admin/`

## Common Tasks

### Generate a summary for different stakeholder roles

```bash
# Developer summary
python manage.py generate_test_summary --role developer

# Executive summary
python manage.py generate_test_summary --role executive

# Legal summary
python manage.py generate_test_summary --role legal

# Finance summary
python manage.py generate_test_summary --role finance
```

### Check job status

```bash
curl http://localhost:8002/api/summaries/{job_id}/
```

### Get summary result

```bash
curl http://localhost:8002/api/summaries/{job_id}/result/
```

### List all summaries for a project

```bash
curl http://localhost:8002/api/summaries/by_project/test-project/
```

## Troubleshooting

### "OpenAI API key not configured"

Make sure you've set `OPENAI_API_KEY` in your `.env` file.

### "Connection to database failed"

- Check PostgreSQL is running
- Verify database credentials in `.env`
- For Docker: `docker-compose logs db`

### "Import Error: No module named 'langchain'"

Make sure you've installed all requirements:
```bash
pip install -r requirements.txt
```

### Token limit exceeded

If you're hitting OpenAI token limits:
1. Reduce the number of documents
2. Reduce `max_length` parameter
3. Check your OpenAI account quota

## Next Steps

1. Review the architecture in `README.md`
2. Check out the API documentation in `API.md`
3. Explore the code:
   - `summary/models.py` - Database models
   - `summary/services.py` - LangChain integration
   - `summary/views.py` - API endpoints
4. Customize stakeholder prompts in `services.py`
5. Add custom management commands
6. Integrate with other services (ingestion, extraction)

## Production Deployment

For production:
1. Use a production WSGI server (gunicorn, uwsgi)
2. Set `DJANGO_DEBUG=False`
3. Configure proper `SECRET_KEY`
4. Use managed PostgreSQL
5. Implement Celery for async processing
6. Add Redis for caching
7. Set up monitoring and logging
8. Implement rate limiting
9. Add authentication/authorization
10. Use environment-specific configuration

## Support

For issues or questions, refer to the main project documentation.
