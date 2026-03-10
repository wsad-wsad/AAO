FROM golang:1.24.4 AS builder

WORKDIR /app
COPY main_go/go.mod main_go/go.sum ./
RUN go mod download

COPY main_go/ .
RUN go build -o main_go


FROM python:3.13-slim

# Copy dependency microcheck and uv
COPY --from=ghcr.io/tarampampam/microcheck:1 /bin/httpcheck /app/httpcheck
COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /uvx /bin/

COPY --from=builder /app/main_go /app/main_go

WORKDIR /app/main_py
COPY main_py/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

RUN playwright install chromium \
    && playwright install-deps

COPY start.sh /app/start.sh
COPY main_py/ .
EXPOSE 8080
RUN chmod +x /app/start.sh
ENTRYPOINT [ "/app/start.sh" ]