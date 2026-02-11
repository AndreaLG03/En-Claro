import uvicorn
import sys
import os

# Add the current directory to sys.path so 'app' can be found
sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
