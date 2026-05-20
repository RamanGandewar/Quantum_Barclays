package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type SessionInfo struct {
	Profile               string `json:"profile"`
	Port                  string `json:"port"`
	NegotiatedGroup       string `json:"negotiated_group"`
	CipherSuite           string `json:"cipher_suite"`
	CertificateAlgorithm  string `json:"certificate_algorithm"`
	CertificateChainBytes int    `json:"certificate_chain_bytes"`
	HandshakeBytes        int    `json:"handshake_bytes"`
	LatencyMS             int    `json:"latency_ms"`
}

func handler(info SessionInfo) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path != "/session-info" {
			w.WriteHeader(http.StatusNotFound)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "use /session-info"})
			return
		}
		_ = json.NewEncoder(w).Encode(info)
	}
}

func serve(port string, info SessionInfo) {
	mux := http.NewServeMux()
	mux.HandleFunc("/session-info", handler(info))
	log.Printf("serving %s profile on :%s", info.Profile, port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatal(err)
	}
}

func main() {
	go serve("8443", SessionInfo{"pqc-native", "8443", "ML-KEM-768", "TLS_AES_256_GCM_SHA384", "ML-DSA-65", 13200, 18100, 34})
	go serve("8444", SessionInfo{"hybrid", "8444", "X25519MLKEM768", "TLS_AES_256_GCM_SHA384", "ML-DSA-65", 13200, 18400, 31})
	serve("8445", SessionInfo{"classical", "8445", "X25519", "TLS_AES_128_GCM_SHA256", "ECDSA-P256", 2600, 5100, 18})
}
