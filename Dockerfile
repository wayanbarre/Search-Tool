FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gear_finder.py .
COPY web_app.py .
COPY browser_opener.py .
COPY scrapers/ scrapers/
COPY templates/ templates/

EXPOSE 5000

# Default: run the web UI. Override with CLI via docker compose run.
CMD ["python", "web_app.py"]
