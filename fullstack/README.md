# Trace2Script Full-Stack Application

A complete web application for automated web UI test script generation, featuring a React/TypeScript frontend and FastAPI backend with PostgreSQL database.

## Quick Start

This guide will help you set up and run both the backend server and frontend client locally.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.8+** (for the backend server)
- **Node.js 16+** and **npm** (for the frontend client) 
- **PostgreSQL** (or use Docker for easy setup)
- **Git** (for cloning the repository)

## Setup Instructions

### Step 1: Clone and Navigate

```bash
git clone <your-repo-url>
cd fullstack
```

### Step 2: Database Setup

You have two options for setting up PostgreSQL:

#### Option A: Using Docker (Recommended)
```bash
# Navigate to server directory
cd server

# Start PostgreSQL using Docker Compose
docker compose -f api-compose.yml up -d

# Verify the database is running
docker ps
```

#### Option B: Local PostgreSQL Installation
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql

# Create database
sudo -u postgres psql -c "CREATE DATABASE auth_db;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE auth_db TO postgres;"
```

### Step 3: Backend Server Setup

```bash
# Navigate to server directory (if not already there)
cd server

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env

# Edit .env file with your database credentials
# The default values should work with the Docker setup:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/auth_db
```

#### Generate RSA Keys for API Key Encryption

The application uses RSA encryption for secure API key transmission. Generate the required key pair:

```bash
# Generate private key (keep this secure!)
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048

# Extract public key
openssl rsa -pubout -in private_key.pem -out public_key.pem

# Move private key to root directory (important!)
mv private_key.pem ../private_key.pem
```

#### Initialize Database and Create Admin User

```bash
# Run database migrations
alembic upgrade head

# Create an admin user
python src/api/cli/create_user.py --username admin
# You'll be prompted to enter a password
```

#### Start the Backend Server

```bash
# Start the FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# The server will be available at http://localhost:8000
# API documentation will be available at http://localhost:8000/docs
```

### Step 4: Frontend Client Setup

Open a new terminal window/tab for the frontend:

```bash
# Navigate to client directory from the fullstack root
cd client

# Install Node.js dependencies
npm install

# Create environment file
touch .env
```

#### Configure Frontend Environment

Edit the `.env` file in the client directory:

```bash
# Get the public key content
cat ../public_key.pem

# Add the public key to .env (convert newlines to \n)
echo 'VITE_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nYOUR_PUBLIC_KEY_CONTENT_HERE\n-----END PUBLIC KEY-----"' > .env
```

**Example .env content:**
```
VITE_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"
```

#### Start the Frontend Development Server

```bash
# Start the Vite development server
npm run dev

# The client will be available at http://localhost:8080
```

## Accessing the Application

1. **Frontend**: Open your browser and navigate to `http://localhost:8080`
2. **Backend API**: Available at `http://localhost:8000`
3. **API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs
4. **Database**: PostgreSQL running on `localhost:5432` (if using Docker)

## First Login

1. Open the frontend application in your browser
2. Use the admin credentials you created during setup:
   - Username: `admin` (or whatever you specified)
   - Password: The password you entered during user creation

## Running Tests

### Backend Tests
```bash
cd server
python -m pytest src/tests/ -v
```

### Frontend Tests
```bash
cd client
npm run lint
```

## Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps  # for Docker setup
sudo systemctl status postgresql  # for local setup

# Check database connectivity
psql -U postgres -h localhost -d auth_db -c "SELECT 1;"
```

#### Port Already in Use
```bash
# Kill processes on port 8000 (backend)
sudo lsof -t -i:8000 | xargs kill -9

# Kill processes on port 8080 (frontend)  
sudo lsof -t -i:8080 | xargs kill -9
```

#### Missing Private Key Error
Make sure `private_key.pem` is in the fullstack root directory (not in server/):
```bash
ls -la ../private_key.pem  # should exist
```

#### Frontend Build Issues
```bash
cd client
rm -rf node_modules package-lock.json
npm install
```

## Additional Development Commands

### Backend
```bash
# Run with auto-reload
uvicorn src.api.main:app --reload

# Run Gradio WebUI (alternative interface)
python webui.py --ip 127.0.0.1 --port 7788

# Create additional users
python src/api/cli/create_user.py --username newuser

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Frontend
```bash
# Build for production
npm run build

# Build for development
npm run build:dev

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Project Structure

```
fullstack/
├── server/                 # FastAPI backend
│   ├── src/
│   │   ├── api/           # API routes and logic
│   │   └── cli/           # Command line tools
│   ├── tests/             # Backend tests
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment template
├── client/                # React/TypeScript frontend
│   ├── src/               # Frontend source code
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   └── vite.config.ts     # Vite configuration
└── private_key.pem        # RSA private key (generate this)
```

## Production Deployment

For production deployment:

1. Set strong passwords and secure JWT secret keys
2. Use a managed PostgreSQL database service
3. Configure Cloudinary for file storage
4. Set up proper HTTPS with SSL certificates
5. Use environment-specific configuration files
6. Implement proper backup strategies

## Browser Automation Directive Prompt

The system uses the following directive prompt for browser automation agents to ensure human-like interaction behavior:

```
You are an expert QA automation agent. Your task is to execute the test case defined in the JSON payload below. Before you begin, you must understand and strictly adhere to the following critical instructions:

**Primary Directive: Simulate Human Interaction**
Your execution must mimic a real user's behavior as closely as possible. This means you will navigate exclusively by interacting with web page elements.

**Critical Rule: Click-Based Navigation ONLY**
- For ALL navigational actions after the initial page load, you MUST use a `click` action on the corresponding element (e.g., a hyperlink, button, or other clickable component).
- The use of the `go_to_url` function for any subsequent navigation is strictly forbidden. All page transitions must be the result of a simulated click.
- Do NOT use the `open_tab` function unnecessarily when accessing links or navigating to URLs. Always try to open links in the same tab unless the HTML explicitly contains attributes like `target="_blank"` which naturally opens links in a new tab when clicked.
```

This prompt ensures that the browser automation behaves like a real user, using click-based navigation instead of programmatic URL changes.

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for complete API documentation with interactive testing capabilities.

## Tips

- The backend supports hot-reloading during development with the `--reload` flag
- Frontend changes are automatically reflected thanks to Vite's HMR
- Use the browser's developer tools to debug API calls and check console logs
- The database schema is managed through Alembic migrations
- API keys are automatically encrypted on the frontend before transmission

## Need Help?

If you encounter issues:

1. Check the terminal logs for error messages
2. Verify all prerequisites are installed
3. Ensure all environment variables are properly set
4. Check that required ports (8000, 8080, 5432) are available
5. Review the troubleshooting section above

Happy coding!