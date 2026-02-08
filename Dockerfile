FROM go:1.24.4-alpine AS builder

WORKDIR /app
COPY main_go/go.mod main_go/go.sum ./
RUN go mod download

COPY main_go/ .
RUN go build -o go_main


FROM python:3.13-alpine

# Copy dependency microcheck
COPY --from=ghcr.io/tarampampam/microcheck:1 /bin/httpcheck /app/httpcheck

COPY --from=builder /app/go_main /app/go_main

WORKDIR /app
COPY main_py/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY main_py/ .
EXPOSE 8080
ENTRYPOINT [ "/app/go_main" ]
CMD ["uvicorn", "main:fast_app", "--host", "0.0.0.0", "--port", "8080", "--reload"]