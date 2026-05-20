// Package main exposes HTTP telemetry for the SSH migration state.
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync/atomic"
)

type Telemetry struct {
	Mode               string `json:"mode"`
	KexAlgorithm       string `json:"kex_algorithm"`
	HostKeyAlgorithm   string `json:"host_key_algorithm"`
	HandshakeMS        int    `json:"handshake_ms"`
	SessionBytes       int    `json:"session_bytes"`
	MigrationState     string `json:"migration_state"`
	NativeOnlyFallback bool   `json:"native_only_fallback"`
}

func sshProfileForMode(mode string) Telemetry {
	switch mode {
	case "classical":
		return Telemetry{"classical", "curve25519-sha256", "ssh-rsa", 8, 2600, "S0_CLASSICAL", false}
	case "pqc-native":
		return Telemetry{"pqc-native", "ML-KEM-768", "ml-dsa-65", 16, 3900, "S4_PQC_NATIVE", true}
	default:
		return Telemetry{"hybrid", "X25519MLKEM768", "ml-dsa-65", 12, 4200, "S3_HYBRID_FULL", true}
	}
}

func serveTelemetry(addr string, store *atomic.Value) {
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		value, ok := store.Load().(Telemetry)
		if !ok {
			w.WriteHeader(http.StatusServiceUnavailable)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "telemetry unavailable"})
			return
		}
		_ = json.NewEncoder(w).Encode(value)
	})
	log.Printf("ssh telemetry listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}
