FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod .
COPY main.go .
RUN go build -o /out/server-pqc .

FROM alpine:3.20
COPY --from=build /out/server-pqc /usr/local/bin/server-pqc
EXPOSE 8443 8444 8445
CMD ["server-pqc"]
