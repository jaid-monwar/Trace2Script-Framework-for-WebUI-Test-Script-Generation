# FastAPI Authentication System

A simple FastAPI-based authentication system with JWT token support.

## Features

- User authentication with JWT tokens
- Password hashing with bcrypt
- PostgreSQL database integration with SQLModel
- Protected API endpoints
- CLI tool for user management
- Task management system with asynchronous execution
- Result management with file storage (Cloudinary integration)
- Automatic file cleanup when deleting tasks/results
- Script conversion from agent history to Python scripts

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- pip or conda for package installation
- OpenSSL (for generating RSA key pair)

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/auth_db

# JWT configuration
JWT_SECRET_KEY=supersecretkey
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440  # 24 hours

# API configuration
API_PREFIX=/api/v1

# Cloudinary configuration (optional - for file storage)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Generate RSA key pair for API key encryption:

   ```bash
   # Generate private key (must be placed in the root folder, outside src)
   openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
   
   # Extract public key
   openssl rsa -pubout -in private_key.pem -out public_key.pem
   ```

   **Important:** The `private_key.pem` file must be placed in the root folder of the project (outside the `src` directory) for the API key decryption service to work properly.

4. Set up the database:

   Option 1: Using Docker (recommended):
   ```bash
   # Start PostgreSQL database using Docker
   docker compose -f api-compose.yml up -d
   ```

   Option 2: Using psql (if PostgreSQL is installed locally):
   ```bash
   psql -U postgres -c "CREATE DATABASE auth_db;"
   ```

5. Create a user using the CLI tool:

```bash
python src/api/cli/create_user.py --username admin
# You will be prompted for a password
```

### Running the API

```bash
uvicorn src.api.main:app --reload
```

The API will be available at http://localhost:8000.

### File Storage Configuration (Optional)

The API supports file storage integration with Cloudinary for storing task result files (GIF recordings and generated Python scripts).

#### Setting up Cloudinary (Optional)

1. Create a free account at [Cloudinary](https://cloudinary.com/)
2. Get your cloud credentials from the dashboard
3. Add the credentials to your `.env` file:

```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

#### File Storage Features

- **GIF Storage**: Task execution recordings are automatically uploaded to Cloudinary
- **Script Storage**: Generated Python scripts are stored as downloadable files
- **Automatic Cleanup**: Files are automatically deleted when tasks/results are removed
- **Graceful Degradation**: API works without Cloudinary - files just won't be uploaded

If Cloudinary is not configured, the API will continue to function normally but files will only be stored locally and not be accessible via URLs.

## API Usage

### Authentication

To authenticate and get a token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Protected Endpoints

To access a protected endpoint:

```bash
curl -X GET "http://localhost:8000/api/v1/hello/protected" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Response:

```json
{
  "message": "Hello, admin!",
  "user_id": 1,
  "protected": true
}
```

### Public Endpoints

To access a public endpoint:

```bash
curl -X GET "http://localhost:8000/api/v1/hello"
```

Response:

```json
{
  "message": "Hello, World!"
}
```

### Task Management

The API includes a task management system with the following endpoints:

#### Create Task

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"task_name": "Example Task"}'
```

#### Get Tasks List

```bash
curl -X GET "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Get Task by ID

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Update Agent Settings

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/1/agent-settings" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"llm_provider": "openai", "llm_model": "gpt-4o", "temperature": 0.7}'
```

#### Update Browser Settings

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/1/browser-settings" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"browser_headless_mode": true, "window_width": 1920, "window_height": 1080}'
```

#### Initiate Task

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/1/initiate" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Search for information about Python",
    "description": "Find the latest Python documentation",
    "search_input_input": "Python documentation",
    "search_input_action": "Click on the first result",
    "expected_outcome": "Python documentation page",
    "expected_status": "success"
  }'
```

#### Delete Task

```bash
curl -X DELETE "http://localhost:8000/api/v1/tasks/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Note:** Deleting a task will also automatically delete any associated result files from Cloudinary.

### Result Management

The API includes result management for retrieving and managing task results and associated files (GIFs and scripts).

#### Get Task Result

```bash
curl -X GET "http://localhost:8000/api/v1/results/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Response:

```json
{
  "task_id": 1,
  "result_gif": "https://res.cloudinary.com/your-cloud/image/upload/task_1_result.gif",
  "result_json_url": "https://res.cloudinary.com/your-cloud/raw/upload/task_1_script.py"
}
```

#### Delete Task Result

```bash
curl -X DELETE "http://localhost:8000/api/v1/results/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Response:

```json
{
  "message": "Result and associated files deleted successfully",
  "task_id": 1,
  "files_deleted": true,
  "database_deleted": true,
  "warnings": []
}
```

**Note:** Deleting a result will remove both the database record and any associated files from Cloudinary (GIF recordings and generated Python scripts).


## License

MIT