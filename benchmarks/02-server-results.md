# 02 - Server Load Test Results

## Concurrency: 10 users

| Metric | Value |
|---|---|
| Total RPS | ~0.72 |
| TTFB P50 (ms) | ~2848 |
| E2E P95 (ms) | ~26000 |
| E2E P99 (ms) | ~27000 |
| Failures | 0 |

## Concurrency: 50 users

| Metric | Value |
|---|---|
| Total RPS | ~0.98 |
| TTFB P50 (ms) | ~16000 |
| E2E P95 (ms) | ~28000 |
| E2E P99 (ms) | ~30000 |
| Failures | 0 |

## Observations

- Throughput increases slightly at higher concurrency (queueing builds up), but E2E latency degrades significantly.
- No failures at either concurrency level, indicating the server handles queued requests gracefully.
- TTFT is the dominant cost with this CPU-only setup (models run on CPU since CUDA build was unavailable).
