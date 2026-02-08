FROM golang:1.24.4 AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o main


FROM scratch

# Copy dependency from builder
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

# Copy microcheck
COPY --from=ghcr.io/tarampampam/microcheck:1 /bin/httpcheck /app/httpcheck

COPY --from=builder /app/main /app/main
EXPOSE 8000
ENTRYPOINT [ "/app/main" ]