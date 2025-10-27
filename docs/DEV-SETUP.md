# Development Environment Setup

This guide will help you set up the ScanPro development environment from scratch.

## Prerequisites

- **Docker** - Required for running the PostgreSQL database
- **Python 3.10+** - For the backend
- **Node.js 18+** - For the frontend
- **Git** - For version control

## Step 1: Database Setup

### 1.1 Start PostgreSQL Container

Run the development database using Docker:

```bash
python scripts/run_dev_database.py
```

This script will:
- Start a PostgreSQL container with the correct configuration
- Mount your local data directory (`APP_DATA/db/postgres_data/`)
- Use development configuration files from `scripts/dev_db_config/`
- Expose PostgreSQL on port `5432`

**Note:** Make sure Docker is running before executing this command.

### 1.2 Verify Database Connection

The database will be available at:
- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `scanpro_db`
- **Username:** `postgres`
- **Password:** `password`

## Step 2: Backend Setup

### 2.1 Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2.2 Create Environment File

Create a `.env` file in the **root directory** (not in backend/):

```bash
# In the root directory (ScanPro/)
echo "SCANPRO_HF_TOKEN=your_huggingface_token_here" > .env
```

**Important:** You need a Hugging Face token to download the ML models.

### 2.3 Start the Backend

```bash
cd backend
python main.py
```

The backend will:
- Load configuration from the `.env` file
- Download and cache ML models from Hugging Face
- Create database tables automatically
- Start the FastAPI server on `http://localhost:5000`

## Step 3: Frontend Setup

### 3.1 Install Node Dependencies

```bash
cd frontend
npm install
```

### 3.2 Start the Frontend

```bash
npm run dev
```

The frontend will start on `http://localhost:3000` and automatically connect to the backend.

## Step 4: Verify Setup

### 4.1 Check Backend Health

Visit `http://localhost:5000/docs` to see the API documentation and verify the backend is running.

### 4.2 Check Frontend

Visit `http://localhost:3000` to access the ScanPro web interface.

### 4.3 Test Database Connection

The backend will automatically create database tables on startup. Check the logs to confirm successful database connection.

## Development Workflow

### Daily Development

1. **Start Database:**
   ```bash
   python scripts/run_dev_database.py
   ```

2. **Start Backend** (in a new terminal):
   ```bash
   cd backend
   python main.py
   ```

3. **Start Frontend** (in a new terminal):
   ```bash
   cd frontend
   npm run dev
   ```

### Stopping Services

- **Database:** Press `Ctrl+C` in the database terminal
- **Backend:** Press `Ctrl+C` in the backend terminal  
- **Frontend:** Press `Ctrl+C` in the frontend terminal

## Troubleshooting

### Database Issues

- **Port already in use:** Make sure no other PostgreSQL instance is running on port 5432
- **Docker not found:** Install Docker Desktop and ensure it's running
- **Permission denied:** Make sure Docker has permission to mount directories

### Backend Issues

- **Module not found:** Make sure you're in the `backend/` directory when running `python main.py`
- **Database connection failed:** Ensure the PostgreSQL container is running
- **Hugging Face token error:** Verify your token in the `.env` file is correct

### Frontend Issues

- **Port 3000 in use:** The frontend will automatically use the next available port
- **API connection failed:** Ensure the backend is running on port 5000
- **Build errors:** Try deleting `node_modules` and running `npm install` again

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SCANPRO_HF_TOKEN` | Hugging Face token for model access | `hf_xxxxxxxxxxxxxxxxxxxx` |

### Optional Variables

The backend will use default values for database connection if not specified in `.env`:

- `POSTGRES_USERNAME` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: `password`)
- `POSTGRES_DB_NAME` (default: `scanpro_db`)
- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)

## File Structure

```
ScanPro/
├── .env                          # Environment variables (create this)
├── backend/
│   ├── requirements.txt          # Python dependencies
│   └── main.py                   # Backend entry point
├── frontend/
│   ├── package.json              # Node dependencies
│   └── ...                       # Frontend source code
├── scripts/
│   ├── run_dev_database.py       # Database startup script
│   └── dev_db_config/           # PostgreSQL configuration
└── APP_DATA/
    └── db/
        └── postgres_data/        # Database data directory
```

## Next Steps

Once your development environment is running:

1. **Explore the API:** Visit `http://localhost:5000/docs`
2. **Upload Documents:** Use the web interface to test document processing
3. **Check Logs:** Monitor backend logs for any issues
4. **Run Tests:** Execute `python -m pytest` in the backend directory

Happy coding! 🚀
