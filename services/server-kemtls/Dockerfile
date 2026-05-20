FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod .
COPY main.go .
RUN go build -o /out/server-kemtls .

FROM alpine:3.20
COPY --from=build /out/server-kemtls /usr/local/bin/server-kemtls
EXPOSE 8446
CMD ["server-kemtls"]
