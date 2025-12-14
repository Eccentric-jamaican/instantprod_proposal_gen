import sys
from pathlib import Path

# Add project root to sys.path so we can import from api_server.py
# Vercel places files in /var/task/ but respects relative imports if path is set
sys.path.append(str(Path(__file__).parent.parent))

from api_server import app

# Vercel looks for 'app' variable by default in this file
