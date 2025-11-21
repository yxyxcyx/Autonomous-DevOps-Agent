# Phase 4: Streamlit UI - Quick Start Guide

## Overview

The Streamlit UI provides a professional, real-time interface for monitoring the Autonomous DevOps Agent. It features:

- **Submit Bug Fix** - Interactive form to submit bug fix requests
- **Task Monitor** - Real-time visualization of agent thinking process
- **Task History** - Complete history of all bug fix attempts

## Starting the UI

### Option 1: Docker Compose (Recommended)

The UI is automatically started with all other services:

```bash
docker-compose up -d
```

Access the UI at: **http://localhost:8501**

### Option 2: Local Development

If running locally without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the UI
streamlit run ui/app.py --server.port=8501
```

## Features

### 1. Submit Bug Fix Page

Submit new bug fix requests with:
- Repository URL and branch
- Bug description
- Test command (optional)
- Programming language selection
- Priority level

### 2. Task Monitor Page

Real-time monitoring with:
- **Progress Bar** - Visual representation of current step
- **Agent Thought Process** - Live log of agent decisions
  - `[PLAN]` - Manager analyzing the bug
  - `[CODE]` - Coder generating fix
  - `[REVIEW]` - Reviewer validating code
  - `[TEST]` - TestRunner executing in sandbox
  - `[PASS]` / `[FAIL]` - Test results
- **Metrics Dashboard** - Attempts, patches, tokens used, success rate
- **Code Patches** - View all generated code fixes
- **Test Results** - Detailed stdout/stderr from sandbox execution

### 3. Task History Page

Browse all tasks with:
- Task ID and status badges
- Summary statistics
- Quick access to view any task

## API Connection

The UI connects to the FastAPI backend at `http://localhost:8000` by default.

To change the API endpoint:

**Docker:**
```yaml
# In docker-compose.yml
environment:
  - API_BASE_URL=http://your-api:8000
```

**Local:**
```bash
# In ui/app.py
API_BASE_URL = "http://your-api:8000"
```

## Auto-Refresh

The Task Monitor page automatically refreshes every 2 seconds when "Auto-refresh" is enabled. This provides real-time updates of the agent's progress.

## Troubleshooting

### UI Can't Connect to API

**Error:** "[WARNING] Cannot connect to API"

**Solution:**
1. Ensure the API is running: `docker-compose ps`
2. Check API health: `curl http://localhost:8000/`
3. Verify network connectivity between containers

### Port Already in Use

**Error:** "Port 8501 is already in use"

**Solution:**
```bash
# Change the port in docker-compose.yml
ports:
  - "8502:8501"  # Use different external port
```

## Architecture

The UI is built with:
- **Streamlit** - Python web framework for data apps
- **Plotly** - Interactive visualizations
- **streamlit-autorefresh** - Auto-refresh capability
- **Requests** - HTTP client for API calls

The UI is stateless and communicates with the backend via REST API calls.

## Development

To modify the UI:

1. Edit `ui/app.py`
2. The UI will auto-reload (if using `--reload` flag)
3. Test changes locally before building Docker image

## Screenshots Placeholder

The UI features:
- Clean, modern interface with color-coded status badges
- Professional code diff viewer
- Responsive layout that works on all screen sizes
- Syntax highlighting for code patches

## Next Steps

1. Submit your first bug fix via the UI
2. Monitor the agent's real-time progress
3. Review generated patches and test results
4. Browse task history to see all completed fixes
