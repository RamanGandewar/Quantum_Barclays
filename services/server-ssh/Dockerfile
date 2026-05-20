FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod .
RUN go mod download
COPY main.go telemetry.go .
RUN go build -o /out/server-ssh .

FROM alpine:3.20
COPY --from=build /out/server-ssh /usr/local/bin/server-ssh
EXPOSE 22 8447
CMD ["server-ssh", "--mode", "hybrid", "--ssh-addr", ":22", "--http-addr", ":8447"]
