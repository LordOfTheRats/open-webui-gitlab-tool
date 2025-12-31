# Quick Start Guide

## 🚀 Get Running in 2 Minutes

### Prerequisites
- Python 3.9+
- A GitLab instance with Personal Access Token (PAT)
- (Optional) Ollama for local LLM inference

### Step 1: Get Your GitLab Token
1. Go to your GitLab instance: https://your-gitlab.com/user/settings/personal_access_tokens
2. Create a new token with `api` scope
3. Copy the token (it starts with `glpat-`)

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Your GitLab Token
```bash
export GITLAB_TOKEN="glpat-..."
export GITLAB_URL="https://your-gitlab.com"  # If not using gitlab.example.com
```

### Step 4: Start the Server
```bash
python -m server.app
```

You'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Open the Web UI
Visit: http://localhost:8000

You should see the GitLab Agent form with your default configuration!

## 🐳 Using Docker (Even Quicker)

### Step 1: Create `.env` file
```bash
cp .env.example .env
# Edit .env and add your GITLAB_TOKEN
```

### Step 2: Start with Docker Compose
```bash
docker-compose up
```

The server will be available at http://localhost:8000 and Ollama will automatically start!

## 📝 Using the Web UI

1. **Enter your request** in the "Request" textarea
   - Examples:
     - "List all projects"
     - "Triage the latest failed pipeline"
     - "Show me open MRs"

2. **Customize if needed**:
   - Model: `ollama:gpt-4o`, `ollama:llama3`, `openai:gpt-4o`, etc.
   - Ollama Base URL: If Ollama is on a different machine
   - GitLab URL: Override the default
   - GitLab Token: If not using environment variable
   - Allow writes: Only if you want to create/modify things
   - Verify SSL: Uncheck for self-signed certificates

3. **Click the button** and wait for the response!

## 🔧 Troubleshooting

### "GITLAB_TOKEN environment variable is required"
Make sure you've set the token:
```bash
export GITLAB_TOKEN="glpat-..."
```

Or paste it in the web form's "GitLab Token (override)" field.

### "Failed to connect to Ollama"
Make sure Ollama is running:
```bash
ollama serve
```

Or use OpenAI instead:
```bash
export OPENAI_API_KEY="sk-..."
# Then use model: "openai:gpt-4o"
```

### SSL Certificate Errors
If your GitLab uses self-signed certs:
```bash
export GITLAB_VERIFY_SSL=false
```

Or uncheck "Verify SSL" in the web form.

## 📚 Learn More

- **Full Documentation**: See [SERVER.md](SERVER.md)
- **Development Notes**: See [FIX_SUMMARY.md](FIX_SUMMARY.md)
- **Agent Architecture**: See [DEEPAGENTS_README.md](DEEPAGENTS_README.md)

## 🎯 Common Commands

```bash
# Check if server is running
curl http://localhost:8000/health

# Get default configuration
curl http://localhost:8000/config

# Send a request (curl)
curl -X POST http://localhost:8000/chat \
  -F "message=List projects" \
  -F "model=ollama:gpt-4o"

# Send a request (curl, JSON)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List projects", "model": "ollama:gpt-4o"}'

# Run tests
python test_server.py

# View logs with color
python -m server.app 2>&1 | grep -E "DEBUG|INFO|ERROR|WARNING"
```

## 🔐 Security Notes

- Never commit your GITLAB_TOKEN to version control
- Use `.env` files (which are git-ignored) for local development
- In production, use environment variables or secrets management
- Keep `GITLAB_ALLOW_WRITES=false` by default (only enable when needed)
- Always `VERIFY_SSL=true` in production (only disable for testing)

## 📋 Next Steps

1. ✅ You're running the server
2. 📝 Try asking the agent to list your projects
3. 🔍 Ask it to find and summarize recent pipelines
4. 📊 Have it create a report about your MRs
5. 🚀 Integrate it into your workflow!

---

**Questions?** Check [SERVER.md](SERVER.md) for detailed documentation or review the test script in [test_server.py](test_server.py) for API examples.
