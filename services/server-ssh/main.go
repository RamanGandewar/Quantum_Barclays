// Package main implements the SSH layer for the PQC migration demo.
package main

import (
	"crypto/rand"
	"crypto/rsa"
	"encoding/json"
	"flag"
	"io"
	"log"
	"net"
	"os"
	"sync/atomic"
	"time"

	"golang.org/x/crypto/ssh"
)

type connectionLog struct {
	Timestamp          string `json:"timestamp"`
	RemoteAddr         string `json:"remote_addr"`
	Mode               string `json:"mode"`
	KexAlgorithm       string `json:"kex_algorithm"`
	HostKeyAlgorithm   string `json:"host_key_algorithm"`
	MigrationState     string `json:"migration_state"`
	SessionBytes       int64  `json:"session_bytes"`
	NativeOnlyFallback bool   `json:"native_only_fallback"`
}

var currentTelemetry atomic.Value

func main() {
	mode := flag.String("mode", "hybrid", "SSH mode: classical, hybrid, or pqc-native")
	sshAddr := flag.String("ssh-addr", ":22", "SSH listen address")
	httpAddr := flag.String("http-addr", ":8447", "telemetry HTTP listen address")
	flag.Parse()

	profile := sshProfileForMode(*mode)
	currentTelemetry.Store(profile)
	go serveTelemetry(*httpAddr, &currentTelemetry)

	config, err := sshConfig(profile)
	if err != nil {
		log.Fatal(err)
	}
	listener, err := net.Listen("tcp", *sshAddr)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("pqc ssh server listening on %s in %s mode", *sshAddr, profile.Mode)
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("accept error: %v", err)
			continue
		}
		go handleConn(conn, config, profile)
	}
}

func sshConfig(profile Telemetry) (*ssh.ServerConfig, error) {
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, err
	}
	signer, err := ssh.NewSignerFromKey(key)
	if err != nil {
		return nil, err
	}
	config := &ssh.ServerConfig{
		NoClientAuth: true,
		Config: ssh.Config{
			KeyExchanges: []string{"curve25519-sha256", "curve25519-sha256@libssh.org"},
			Ciphers:      []string{"aes256-gcm@openssh.com", "aes128-gcm@openssh.com"},
			MACs:         []string{"hmac-sha2-256-etm@openssh.com"},
		},
	}
	if profile.Mode == "classical" {
		config.Config.KeyExchanges = []string{"curve25519-sha256", "curve25519-sha256@libssh.org"}
	}
	// NATIVE-ONLY: ML-KEM and ML-DSA SSH algorithms do not have finalized RFC support.
	// Demo mode logs the requested PQC profile while using standard SSH primitives.
	config.AddHostKey(signer)
	return config, nil
}

func handleConn(conn net.Conn, config *ssh.ServerConfig, profile Telemetry) {
	started := time.Now()
	sshConn, chans, reqs, err := ssh.NewServerConn(conn, config)
	if err != nil {
		log.Printf("ssh handshake error: %v", err)
		return
	}
	defer sshConn.Close()
	go ssh.DiscardRequests(reqs)
	var sessionBytes int64
	for channel := range chans {
		if channel.ChannelType() != "session" {
			_ = channel.Reject(ssh.UnknownChannelType, "only session channels are supported")
			continue
		}
		accepted, requests, err := channel.Accept()
		if err != nil {
			continue
		}
		go func() {
			for req := range requests {
				_ = req.Reply(req.Type == "shell" || req.Type == "exec", nil)
			}
		}()
		n, _ := io.WriteString(accepted, "pqc ssh telemetry server\n")
		sessionBytes += int64(n)
		_ = accepted.Close()
	}
	elapsed := time.Since(started).Milliseconds()
	if elapsed > 0 {
		profile.HandshakeMS = int(elapsed)
	}
	profile.SessionBytes = int(sessionBytes)
	currentTelemetry.Store(profile)
	logJSON(connectionLog{
		Timestamp:          time.Now().UTC().Format(time.RFC3339),
		RemoteAddr:         sshConn.RemoteAddr().String(),
		Mode:               profile.Mode,
		KexAlgorithm:       profile.KexAlgorithm,
		HostKeyAlgorithm:   profile.HostKeyAlgorithm,
		MigrationState:     profile.MigrationState,
		SessionBytes:       sessionBytes,
		NativeOnlyFallback: profile.NativeOnlyFallback,
	})
}

func logJSON(value any) {
	bytes, err := json.Marshal(value)
	if err != nil {
		log.Printf("json log error: %v", err)
		return
	}
	_, _ = os.Stdout.Write(append(bytes, '\n'))
}
