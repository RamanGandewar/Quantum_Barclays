package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"net/http"
	"sort"
	"time"
)

type SessionInfo struct {
	Profile               string `json:"profile"`
	NegotiatedGroup       string `json:"negotiated_group"`
	CertificateAlgorithm  string `json:"certificate_algorithm"`
	CertificateChainBytes int    `json:"certificate_chain_bytes"`
	HandshakeBytes        int    `json:"handshake_bytes"`
	LatencyMS             int    `json:"latency_ms"`
}

type Result struct {
	Endpoint string `json:"endpoint"`
	Run      int    `json:"run"`
	SessionInfo
	MeasuredLatencyMS float64 `json:"measured_latency_ms"`
}

type Summary struct {
	Endpoint string  `json:"endpoint"`
	Runs     int     `json:"runs"`
	MeanMS   float64 `json:"mean_ms"`
	P50MS    float64 `json:"p50_ms"`
	P95MS    float64 `json:"p95_ms"`
	P99MS    float64 `json:"p99_ms"`
}

func percentile(values []float64, pct float64) float64 {
	if len(values) == 0 {
		return 0
	}
	index := int(math.Ceil((pct/100)*float64(len(values)))) - 1
	if index < 0 {
		index = 0
	}
	if index >= len(values) {
		index = len(values) - 1
	}
	return values[index]
}

func main() {
	endpoint := flag.String("endpoint", "http://127.0.0.1:8444/session-info", "session-info endpoint")
	runs := flag.Int("runs", 100, "number of connections")
	flag.Parse()

	results := make([]Result, 0, *runs)
	latencies := make([]float64, 0, *runs)
	for i := 0; i < *runs; i++ {
		started := time.Now()
		response, err := http.Get(*endpoint)
		if err != nil {
			panic(err)
		}
		var info SessionInfo
		if err := json.NewDecoder(response.Body).Decode(&info); err != nil {
			panic(err)
		}
		_ = response.Body.Close()
		elapsed := float64(time.Since(started).Microseconds()) / 1000
		latencies = append(latencies, elapsed)
		results = append(results, Result{Endpoint: *endpoint, Run: i + 1, SessionInfo: info, MeasuredLatencyMS: elapsed})
	}
	sort.Float64s(latencies)
	var total float64
	for _, latency := range latencies {
		total += latency
	}
	output := map[string]any{
		"summary": Summary{
			Endpoint: *endpoint,
			Runs:     *runs,
			MeanMS:   total / float64(*runs),
			P50MS:    percentile(latencies, 50),
			P95MS:    percentile(latencies, 95),
			P99MS:    percentile(latencies, 99),
		},
		"results": results,
	}
	bytes, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		panic(err)
	}
	fmt.Println(string(bytes))
}
