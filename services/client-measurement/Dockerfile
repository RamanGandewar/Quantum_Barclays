FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod .
COPY main.go .
RUN go build -o /out/client-measurement .

FROM alpine:3.20
COPY --from=build /out/client-measurement /usr/local/bin/client-measurement
ENTRYPOINT ["client-measurement"]
