package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
)

func TestSSHProfileForMode(t *testing.T) {
	tests := []struct {
		mode          string
		expectedState string
		expectedKex   string
	}{
		{"classical", "S0_CLASSICAL", "curve25519-sha256"},
		{"hybrid", "S3_HYBRID_FULL", "X25519MLKEM768"},
		{"pqc-native", "S4_PQC_NATIVE", "ML-KEM-768"},
		{"unknown", "S3_HYBRID_FULL", "X25519MLKEM768"},
	}

	for _, tc := range tests {
		t.Run(tc.mode, func(t *testing.T) {
			p := sshProfileForMode(tc.mode)
			if p.MigrationState != tc.expectedState {
				t.Errorf("mode %s: expected state %s, got %s", tc.mode, tc.expectedState, p.MigrationState)
			}
			if p.KexAlgorithm != tc.expectedKex {
				t.Errorf("mode %s: expected kex %s, got %s", tc.mode, tc.expectedKex, p.KexAlgorithm)
			}
			if p.Mode != tc.mode && tc.mode != "unknown" {
				t.Errorf("mode %s: expected mode field %s, got %s", tc.mode, tc.mode, p.Mode)
			}
		})
	}
}

func TestTelemetryJSON(t *testing.T) {
	p := sshProfileForMode("hybrid")
	data, err := json.Marshal(p)
	if err != nil {
		t.Fatalf("failed to marshal telemetry: %v", err)
	}

	var decoded Telemetry
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("failed to unmarshal telemetry: %v", err)
	}
	if decoded.MigrationState != "S3_HYBRID_FULL" {
		t.Errorf("expected S3_HYBRID_FULL, got %s", decoded.MigrationState)
	}
}

func TestServeTelemetryEndpoint(t *testing.T) {
	var store atomic.Value
	profile := sshProfileForMode("hybrid")
	store.Store(profile)

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

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var result Telemetry
	if err := json.NewDecoder(w.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}
	if result.KexAlgorithm != "X25519MLKEM768" {
		t.Errorf("expected X25519MLKEM768, got %s", result.KexAlgorithm)
	}
}

func TestSSHConfigCreation(t *testing.T) {
	profile := sshProfileForMode("hybrid")
	config, err := sshConfig(profile)
	if err != nil {
		t.Fatalf("failed to create SSH config: %v", err)
	}
	if config == nil {
		t.Fatal("expected non-nil config")
	}
	if len(config.HostKeyAlgorithms()) == 0 {
		t.Error("expected at least one host key algorithm")
	}
}
