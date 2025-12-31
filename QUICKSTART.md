# 🚀 Quick Start Guide

This guide will get you up and running with the GitLab Flock Tool in under 5 minutes.

## Prerequisites

Before starting, ensure you have:

- ✅ Python 3.11 or higher
- ✅ Git
- ✅ A GitLab instance (self-hosted or GitLab.com)
- ✅ GitLab Personal Access Token with `api` scope
- ✅ Ollama installed with a model downloaded

### Installing Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Start Ollama service
ollama serve

# In another terminal, pull a model
ollama pull llama3.2
```

## Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/LordOfTheRats/open-webui-gitlab-tool.git
cd open-webui-gitlab-tool
```

### Step 2: Install Dependencies

```bash
# Option A: Using Make (recommended)
make install

# Option B: Using pip directly
pip install -e .

# Option C: For development (includes test tools)
make dev-install
# or
pip install -e ".[dev]"
```

### Step 3: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your favorite editor
```

Minimal `.env` configuration:
```env
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-your-token-here
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Step 4: Verify Configuration

```bash
# Test GitLab connection
curl -H "PRIVATE-TOKEN: your-token" https://gitlab.example.com/api/v4/version

# Test Ollama connection
curl http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"hello"}'
```

### Step 5: Run the Server

```bash
# Option A: Using Make
make run

# Option B: Using uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: http://localhost:8000

### Step 6: Test the API

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"2.0.0"}
```

## 🐳 Quick Start with Docker

If you prefer Docker:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Start with Docker Compose (includes Ollama)
make docker-run

# 3. View logs
make docker-logs

# 4. Stop services
make docker-stop
```

Access the API at: http://localhost:8000

## 🎯 First API Call

Try analyzing a GitLab project:

```bash
curl -X POST http://localhost:8000/api/analyze-project \
  -H "Content-Type: application/json" \
  -d '{"project": "your-group/your-project"}'
```

## 🔧 Troubleshooting

### Import Errors

If you see import errors:
```bash
# Make sure you're in the project directory
cd /path/to/open-webui-gitlab-tool

# Reinstall dependencies
pip install -e .
```

### Ollama Not Responding

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not, start Ollama
ollama serve

# Verify model is available
ollama list
```

### GitLab Token Issues

Ensure your token has the `api` scope:
1. Go to GitLab → Settings → Access Tokens
2. Create a new token with `api` scope
3. Copy the token to your `.env` file

### Port Already in Use

If port 8000 is in use:
```bash
# Use a different port
uvicorn src.main:app --port 8080

# Or configure in .env
PORT=8080
```

## 📖 Next Steps

1. **Read the [Usage Guide](USAGE.md)** - Learn all API endpoints
2. **Check [Architecture](ARCHITECTURE.md)** - Understand the system
3. **Integrate with Open WebUI** - Add as a function tool
4. **Customize** - Add your own agents

## 🔗 Open WebUI Integration

To use with Open WebUI:

1. Open WebUI → Settings → Functions
2. Click "Add Function"
3. Select "Import from URL"
4. Enter: `http://localhost:8000`
5. Save

Now you can use natural language in Open WebUI:
- "Analyze the issues in my-project"
- "Review the code in src/main.py"
- "What's the status of merge request #123?"

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/LordOfTheRats/open-webui-gitlab-tool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/LordOfTheRats/open-webui-gitlab-tool/discussions)
- **Documentation**: See `*.md` files in the repository

## ✅ Verification Checklist

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`make install`)
- [ ] `.env` file configured
- [ ] Ollama running with model downloaded
- [ ] GitLab token valid and has `api` scope
- [ ] Server starts without errors
- [ ] Health check returns `healthy`
- [ ] First API call successful

## 🎉 Success!

If you've completed all steps and the health check passes, you're ready to use the GitLab Flock Tool!

Start with a simple project analysis:
```bash
curl -X POST http://localhost:8000/api/analyze-project \
  -H "Content-Type: application/json" \
  -d '{"project": "your-project-path"}'
```

Enjoy using AI-powered GitLab automation! 🚀
