# Summary Service API Documentation

## Base URL
```
http://localhost:8002/api
```

## Authentication
Currently no authentication required (add in production).

---

## Endpoints

### 1. Generate Summary

Generate a stakeholder-specific summary from project documents.

**Endpoint:** `POST /summaries/generate/`

**Request Body:**
```json
{
  "document_ids": ["doc-123", "doc-456"],
  "project_id": "project-789",
  "stakeholder_role": "developer",
  "focus_areas": ["costs", "timeline", "risks"],
  "max_length": 500
}
```

**Parameters:**
- `document_ids` (array, required): List of document IDs to summarize (min: 1, max: 50)
- `project_id` (string, required): Project identifier
- `stakeholder_role` (string, required): One of:
  - `developer`
  - `contractor`
  - `architect`
  - `client`
  - `project_manager`
  - `legal`
  - `finance`
  - `executive`
- `focus_areas` (array, optional): Specific focus areas (e.g., ["costs", "timeline"])
- `max_length` (integer, optional): Maximum summary length in words (100-2000, default: 500)

**Success Response:** `201 Created`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Summary generated successfully",
  "summary": {
    "id": "sum_550e8400-e29b-41d4-a716-446655440000",
    "project_id": "project-789",
    "stakeholder_role": "developer",
    "sections": [
      {
        "id": 1,
        "title": "Technical Overview",
        "content": "The project involves...",
        "order": 0,
        "key_points": [
          "Building code compliance required",
          "Structural specifications defined"
        ],
        "evidence_ids": ["doc-123", "doc-456"]
      }
    ],
    "full_summary": "Complete summary text...",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Response:** `400 Bad Request`
```json
{
  "document_ids": ["This field is required."],
  "stakeholder_role": ["Invalid stakeholder role."]
}
```

---

### 2. Get Summary Job

Retrieve a specific summary job by ID.

**Endpoint:** `GET /summaries/{job_id}/`

**Success Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "project-789",
  "stakeholder_role": "developer",
  "document_ids": ["doc-123", "doc-456"],
  "focus_areas": ["costs", "timeline"],
  "max_length": 500,
  "status": "completed",
  "error_message": null,
  "model_used": "gpt-4-turbo-preview",
  "tokens_used": 1543,
  "processing_time": 4.56,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:05Z",
  "completed_at": "2024-01-15T10:30:05Z",
  "summary": {
    "id": "sum_550e8400-e29b-41d4-a716-446655440000",
    "full_summary": "...",
    "sections": [...]
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "Not found."
}
```

---

### 3. Get Summary Result

Get the generated summary for a completed job.

**Endpoint:** `GET /summaries/{job_id}/result/`

**Success Response (Completed):** `200 OK`
```json
{
  "summary_id": "sum_550e8400-e29b-41d4-a716-446655440000",
  "project_id": "project-789",
  "stakeholder_role": "developer",
  "sections": [
    {
      "id": 1,
      "title": "Technical Overview",
      "content": "The project involves...",
      "order": 0,
      "key_points": ["Point 1", "Point 2"],
      "evidence_ids": ["doc-123"]
    }
  ],
  "full_summary": "Complete summary text...",
  "generated_at": "2024-01-15T10:30:05Z"
}
```

**Response (Pending):** `202 Accepted`
```json
{
  "status": "pending",
  "message": "Summary generation is pending"
}
```

**Response (Processing):** `202 Accepted`
```json
{
  "status": "processing",
  "message": "Summary is being generated"
}
```

**Response (Failed):** `500 Internal Server Error`
```json
{
  "status": "failed",
  "error": "OpenAI API error: Rate limit exceeded"
}
```

---

### 4. List All Summaries

List all summary jobs with optional filtering.

**Endpoint:** `GET /summaries/`

**Query Parameters:**
- `project_id` (string, optional): Filter by project
- `stakeholder_role` (string, optional): Filter by role
- `status` (string, optional): Filter by status (pending, processing, completed, failed)
- `page` (integer, optional): Page number (default: 1)

**Success Response:** `200 OK`
```json
{
  "count": 42,
  "next": "http://localhost:8002/api/summaries/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "project_id": "project-789",
      "stakeholder_role": "developer",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      ...
    }
  ]
}
```

---

### 5. List Summaries by Project

List all summaries for a specific project.

**Endpoint:** `GET /summaries/by_project/{project_id}/`

**Query Parameters:**
- `stakeholder_role` (string, optional): Filter by role
- `status` (string, optional): Filter by status

**Success Response:** `200 OK`
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [...]
}
```

---

### 6. List Summaries by Role

List all summaries for a specific stakeholder role.

**Endpoint:** `GET /summaries/by_role/{role}/`

**Query Parameters:**
- `project_id` (string, optional): Filter by project
- `status` (string, optional): Filter by status

**Success Response:** `200 OK`
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [...]
}
```

---

### 7. List Generated Summaries

List all generated summaries directly (completed only).

**Endpoint:** `GET /generated-summaries/`

**Query Parameters:**
- `project_id` (string, optional): Filter by project
- `stakeholder_role` (string, optional): Filter by role

**Success Response:** `200 OK`
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "sum_550e8400-e29b-41d4-a716-446655440000",
      "project_id": "project-789",
      "stakeholder_role": "developer",
      "full_summary": "...",
      "sections": [...],
      "created_at": "2024-01-15T10:30:05Z"
    }
  ]
}
```

---

### 8. Get Generated Summary

Get a specific generated summary by ID.

**Endpoint:** `GET /generated-summaries/{summary_id}/`

**Success Response:** `200 OK`
```json
{
  "id": "sum_550e8400-e29b-41d4-a716-446655440000",
  "project_id": "project-789",
  "stakeholder_role": "developer",
  "full_summary": "Complete summary text...",
  "sections": [
    {
      "id": 1,
      "title": "Technical Overview",
      "content": "...",
      "order": 0,
      "key_points": ["Point 1", "Point 2"],
      "evidence_ids": ["doc-123"]
    }
  ],
  "created_at": "2024-01-15T10:30:05Z"
}
```

---

## Error Codes

- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error (check error message)
- `202 Accepted`: Request accepted but not yet completed

---

## Examples

### Generate Developer Summary

```bash
curl -X POST http://localhost:8002/api/summaries/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc-1", "doc-2", "doc-3"],
    "project_id": "project-123",
    "stakeholder_role": "developer",
    "focus_areas": ["technical", "quality"],
    "max_length": 750
  }'
```

### Get Summary Status

```bash
curl http://localhost:8002/api/summaries/550e8400-e29b-41d4-a716-446655440000/
```

### List Project Summaries

```bash
curl http://localhost:8002/api/summaries/by_project/project-123/?stakeholder_role=developer
```

---

## Notes

1. **Asynchronous Processing**: In production, summary generation should be handled asynchronously using Celery. The current implementation is synchronous for simplicity.

2. **Rate Limiting**: Implement rate limiting in production to prevent abuse and manage OpenAI API costs.

3. **Caching**: Consider caching generated summaries to avoid regenerating identical summaries.

4. **Authentication**: Add authentication and authorization in production.

5. **Webhooks**: Consider adding webhooks to notify clients when long-running summary jobs complete.
