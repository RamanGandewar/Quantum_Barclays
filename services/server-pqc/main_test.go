package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHandlerReturnsSessionInfo(t *testing.T) {
	info := SessionInfo{"pqc-native", "8443", "ML-KEM-768", "TLS_AES_256_GCM_SHA384", "ML-DSA-65", 13200, 18100, 34}
	handler := handler(info)

	req := httptest.NewRequest(http.MethodGet, "/session-info", nil)
	w := httptest.NewRecorder()
	handler(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var result SessionInfo
	if err := json.NewDecoder(w.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}
	if result.NegotiatedGroup != "ML-KEM-768" {
		t.Errorf("expected ML-KEM-768, got %s", result.NegotiatedGroup)
	}
	if result.CertificateAlgorithm != "ML-DSA-65" {
		t.Errorf("expected ML-DSA-65, got %s", result.CertificateAlgorithm)
	}
	if result.LatencyMS != 34 {
		t.Errorf("expected 34ms, got %d", result.LatencyMS)
	}
}

func TestHandlerReturns404ForWrongPath(t *testing.T) {
	info := SessionInfo{"hybrid", "8444", "X25519MLKEM768", "TLS_AES_256_GCM_SHA384", "ML-DSA-65", 13200, 18400, 31}
	handler := handler(info)

	req := httptest.NewRequest(http.MethodGet, "/wrong-path", nil)
	w := httptest.NewRecorder()
	handler(w, req)

	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", w.Code)
	}

	var errResp map[string]string
	if err := json.NewDecoder(w.Body).Decode(&errResp); err != nil {
		t.Fatalf("failed to decode error response: %v", err)
	}
	if errResp["error"] != "use /session-info" {
		t.Errorf("unexpected error message: %s", errResp["error"])
	}
}

func TestHandlerSetsContentType(t *testing.T) {
	info := SessionInfo{"classical", "8445", "X25519", "TLS_AES_128_GCM_SHA256", "ECDSA-P256", 2600, 5100, 18}
	handler := handler(info)

	req := httptest.NewRequest(http.MethodGet, "/session-info", nil)
	w := httptest.NewRecorder()
	handler(w, req)

	if ct := w.Header().Get("Content-Type"); ct != "application/json" {
		t.Errorf("expected application/json, got %s", ct)
	}
}

func TestAllProfilesHaveRequiredFields(t *testing.T) {
	profiles := []SessionInfo{
		{"pqc-native", "8443", "ML-KEM-768", "TLS_AES_256_GCM_SHA384", "ML-DSA-65", 13200, 18100, 34},
		{"hybrid", "8444", "X25519MLKEM768", "TLS_AES_256_GCM_SHA384", "ML-DSA-65", 13200, 18400, 31},
		{"classical", "8445", "X25519", "TLS_AES_128_GCM_SHA256", "ECDSA-P256", 2600, 5100, 18},
	}

	for _, p := range profiles {
		if p.NegotiatedGroup == "" {
			t.Errorf("profile %s: empty negotiated_group", p.Profile)
		}
		if p.CertificateChainBytes <= 0 {
			t.Errorf("profile %s: invalid certificate_chain_bytes %d", p.Profile, p.CertificateChainBytes)
		}
		if p.HandshakeBytes <= 0 {
			t.Errorf("profile %s: invalid handshake_bytes %d", p.Profile, p.HandshakeBytes)
		}
	}
}
