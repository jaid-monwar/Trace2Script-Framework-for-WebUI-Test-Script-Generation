# Task Management API Documentation

This document provides information about the Task Management API endpoints.

## Authentication

All endpoints require authentication using JWT tokens. To authenticate:

1. Get a token from `/api/v1/auth/token` using your username and password
2. Include the token in the Authorization header: `Authorization: Bearer <token>`

## Endpoints

### Create Task

Creates a new task for the authenticated user.

**Endpoint:** `POST /api/v1/tasks`

**Request Body:**
```json
{
  "task_name": "Example Task"
}
```

**Response:**
```json
{
  "id": 1,
  "task_name": "Example Task",
  "status": "initial",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "temperature": 0.6,
  "context_length": 16000,
  "base_url": null,
  "api_key": null,
  "browser_headless_mode": true,
  "disable_security": true,
  "window_width": 1280,
  "window_height": 720,
  "instruction": null,
  "description": null,
  "search_input_input": null,
  "search_input_action": null,
  "expected_outcome": null,
  "expected_status": null,
  "user_id": 1
}
```

### Get Tasks List

Returns a list of all tasks owned by the authenticated user.

**Endpoint:** `GET /api/v1/tasks`

**Response:**
```json
[
  {
    "id": 1,
    "task_name": "Example Task",
    "status": "initial"
  },
  {
    "id": 2,
    "task_name": "Another Task",
    "status": "completed"
  }
]
```

### Get Task by ID

Returns detailed information about a specific task.

**Endpoint:** `GET /api/v1/tasks/{task_id}`

**Response:**
```json
{
  "id": 1,
  "task_name": "Example Task",
  "status": "initial",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "temperature": 0.6,
  "context_length": 16000,
  "base_url": null,
  "api_key": null,
  "browser_headless_mode": true,
  "disable_security": true,
  "window_width": 1280,
  "window_height": 720,
  "instruction": null,
  "description": null,
  "search_input_input": null,
  "search_input_action": null,
  "expected_outcome": null,
  "expected_status": null,
  "user_id": 1
}
```

### Update Agent Settings

Updates the agent settings for a specific task.

**Endpoint:** `PATCH /api/v1/tasks/{task_id}/agent-settings`

**Request Body:**
```json
{
  "llm_provider": "anthropic",
  "llm_model": "claude-3-opus",
  "temperature": 0.8,
  "context_length": 32000,
  "base_url": "https://api.example.com",
  "api_key": "sk-example-key"
}
```

**Response:** Returns the updated task object.

**Notes:**
- Temperature must be between 0 and 2
- Task must be in "initial" or "failed" state
- Only the task owner can update settings

### Update Browser Settings

Updates the browser settings for a specific task.

**Endpoint:** `PATCH /api/v1/tasks/{task_id}/browser-settings`

**Request Body:**
```json
{
  "browser_headless_mode": false,
  "disable_security": false,
  "window_width": 1920,
  "window_height": 1080
}
```

**Response:** Returns the updated task object.

**Notes:**
- Task must be in "initial" or "failed" state
- Only the task owner can update settings

### Initiate Task

Initiates a task by providing instructions and expectations.

**Endpoint:** `PATCH /api/v1/tasks/{task_id}/initiate`

**Request Body:**
```json
{
  "instruction": "Search for information about Python",
  "description": "Find the latest Python documentation",
  "search_input_input": "Python documentation",
  "search_input_action": "Click on the first result",
  "expected_outcome": "Python documentation page",
  "expected_status": "success"
}
```

**Response:** Returns the updated task object.

**Notes:**
- All fields in the request body are required
- Task must be in "initial" or "failed" state
- Only the task owner can initiate the task

### Delete Task

Deletes a task.

**Endpoint:** `DELETE /api/v1/tasks/{task_id}`

**Response:**
```json
{
  "message": "Task deleted successfully"
}
```

**Notes:**
- Task must not be in "running" state
- Only the task owner can delete the task

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to access this task"
}
```

### 404 Not Found
```json
{
  "detail": "Task not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Cannot update agent settings task in running state"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Temperature must be between 0 and 2"
}
```