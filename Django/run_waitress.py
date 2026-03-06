"""Production-ish runner (Windows friendly): run Django WSGI app with Waitress.

Usage (cmd.exe):
  set DJANGO_DEBUG=0
  set DJANGO_SECRET_KEY=your-secret
  set DJANGO_ALLOWED_HOSTS=your.domain.com,localhost,127.0.0.1
  python run_waitress.py

Notes:
- This is the simplest way to deploy on a Windows server.
- For real production, put a reverse proxy (Nginx/IIS) in front of it.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Django.settings")

from waitress import serve  # noqa: E402
from Django.wsgi import application  # noqa: E402


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    threads = int(os.getenv("WAITRESS_THREADS", "8"))

    serve(application, host=host, port=port, threads=threads)

