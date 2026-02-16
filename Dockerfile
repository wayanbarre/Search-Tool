FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gear_finder.py .
COPY browser_opener.py .
COPY scrapers/ scrapers/

ENTRYPOINT ["python", "gear_finder.py"]
