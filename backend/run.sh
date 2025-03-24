# backend/run.sh
#!/bin/bash
cd ~/projects/knowledge-graph-system/backend
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload