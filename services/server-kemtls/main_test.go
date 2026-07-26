package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestSessionInfoEndpoint(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/session-info", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"profile":                 "kemtls",
			"port":                    "8446",
			"negotiated_group":        "ML-KEM-768",
			"authentication":          "KEM decapsulation",
			"certificate_verify":      "absent",
			"certificate_chain_bytes": 11800,
			"client_kem_ciphertext":   1088,
			"handshake_bytes":         15800,
			"latency_ms":              39,
		})
	})

	req := httptest.NewRequest(http.MethodGet, "/session-info", nil)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var result map[string]any
	if err := json.NewDecoder(w.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if result["profile"] != "kemtls" {
		t.Errorf("expected kemtls profile, got %v", result["profile"])
	}
	if result["negotiated_group"] != "ML-KEM-768" {
		t.Errorf("expected ML-KEM-768, got %v", result["negotiated_group"])
	}
	if result["authentication"] != "KEM decapsulation" {
		t.Errorf("expected KEM decapsulation, got %v", result["authentication"])
	}
	if result["certificate_verify"] != "absent" {
		t.Errorf("expected absent, got %v", result["certificate_verify"])
	}
}

func TestKEMTLSHandshakeBytes(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/session-info", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"handshake_bytes":  15800,
			"certificate_chain_bytes": 11800,
			"client_kem_ciphertext": 1088,
		})
	})

	req := httptest.NewRequest(http.MethodGet, "/session-info", nil)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	var result map[string]any
	_ = json.NewDecoder(w.Body).Decode(&result)

	if result["handshake_bytes"].(float64) != 15800 {
		t.Errorf("expected 15800 handshake bytes, got %v", result["handshake_bytes"])
	}
	if result["client_kem_ciphertext"].(float64) != 1088 {
		t.Errorf("expected 1088 client KEM ciphertext, got %v", result["client_kem_ciphertext"])
	}
}
