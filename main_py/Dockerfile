FROM python:3.13-alpine

# Copy dependency microcheck
COPY --from=ghcr.io/tarampampam/microcheck:1 /bin/httpcheck /app/httpcheck

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:fast_app", "--host", "0.0.0.0", "--port", "8080", "--reload"]