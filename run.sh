# backend/run.sh
#!/bin/bash
cd ~/projects/knowledge-graph-system/backend
#source ../venv/bin/activate
#uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > uvicorn.log 2>&1 &

cd ~/projects/knowledge-graph-system/frontend
nohup npm run serve > npm.log 2>&1 &
