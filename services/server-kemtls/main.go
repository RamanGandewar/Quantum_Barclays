package main

import (
	"encoding/json"
	"log"
	"net/http"
)

func main() {
	http.HandleFunc("/session-info", func(w http.ResponseWriter, r *http.Request) {
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
	log.Println("serving KEMTLS telemetry profile on :8446")
	log.Fatal(http.ListenAndServe(":8446", nil))
}
