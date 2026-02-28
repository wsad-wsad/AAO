FROM golang:1.24.4 AS builder

WORKDIR /app
COPY main_go/go.mod main_go/go.sum ./
RUN go mod download

COPY main_go/ .
RUN go build -o main_go


FROM python:3.13-slim

# Copy dependency microcheck
COPY --from=ghcr.io/tarampampam/microcheck:1 /bin/httpcheck /app/httpcheck

COPY --from=builder /app/main_go /app/main_go

WORKDIR /app/main_py
COPY main_py/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

RUN playwright install \
    && playwright install-deps

COPY start.sh /app/start.sh
COPY main_py/ .
EXPOSE 8080
RUN chmod +x /app/start.sh
ENTRYPOINT [ "/app/start.sh" ]