# Reflection — Lab 20 (Personal Report)

> **Đây là báo cáo cá nhân.** Mỗi học viên chạy lab trên laptop của mình, với spec của mình. Số liệu của bạn không so sánh được với bạn cùng lớp — chỉ so sánh **before vs after trên chính máy bạn**. Grade rubric tính theo độ rõ ràng của setup + tuning của bạn, không phải tốc độ tuyệt đối.

---

**Họ Tên:** _Nguyen Minh Chien_
**Cohort:** _A20-K2_
**MSV:** _2A202600664_
**Ngày submit:** _2026-06-24_

---

## 1. Hardware spec (từ `00-setup/detect-hardware.py`)

> Paste output của `python 00-setup/detect-hardware.py` vào đây, hoặc điền thủ công:

- **OS:** _Windows 11_
- **CPU:** _12th Gen Intel(R) Core(TM) i5-12500H_
- **Cores:** _12 physical / 16 logical_
- **CPU extensions:** _AVX2_
- **RAM:** _15.7 GB_
- **Accelerator:** _NVIDIA GeForce RTX 3050 Laptop GPU 4GB_
- **llama.cpp backend đã chọn:** _Vulkan (CUDA build failed - no CUDA Toolkit; fell back to Vulkan prebuilt wheel)_
- **Recommended model tier:** _Qwen2.5-1.5B-Instruct (Q4_K_M)_

**Setup story**: Python 3.13 không có prebuilt wheel cho llama-cpp-python; cần download wheel từ GitHub Release (v0.3.31-vulkan). Không cần WSL. CUDA Toolkit chưa install nên dùng Vulkan build chạy CPU-only inference.

---

## 2. Track 01 — Quickstart numbers (từ `benchmarks/01-quickstart-results.md`)

> Paste bảng từ `benchmarks/01-quickstart-results.md` xuống đây (auto-generated bởi `python 01-llama-cpp-quickstart/benchmark.py`).

| Model | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode rate (tok/s) |
|---|--:|--:|--:|--:|--:|
| qwen2.5-1.5b-instruct-q4_k_m.gguf | 2021 | 28 / 36 | 10.5 / 10.9 | 676 / 716 / 718 | 95.1 |
| qwen2.5-1.5b-instruct-q2_k.gguf | 1188 | 32 / 36 | 8.7 / 8.8 | 576 / 587 / 587 | 115.3 |

**Một quan sát**: Q2_K load nhanh hơn 2.2x và decode nhanh hơn ~15%, nhưng chất lượng text giảm rõ. Với RAM 16GB, Q4_K_M là lựa chọn hợp lý hơn — quality gain > latency cost.

---

## 3. Track 02 — llama-server load test

> Chạy 2 lần locust ở concurrency 10 và 50, paste tóm tắt bên dưới.

| Concurrency | Total RPS | TTFB P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 0.72 | 2848 | 26000 | 27000 | 0 |
| 50 | 0.98 | 16000 | 28000 | 30000 | 0 |

**Batching observation**: Python server không có /metrics endpoint, nên không đo được busy slots. Tuy nhiên throughput tăng từ 0.72→0.98 req/s khi tăng concurrency cho thấy server xếp hàng requests và xử lý tuần tự — bottleneck là CPU decode (single-stream).

---

## 4. Track 03 — Milestone integration

- **N16 (Cloud/IaC):** _stub: localhost only_
- **N17 (Data pipeline):** _stub: in-memory dict_
- **N18 (Lakehouse):** _stub: SQLite_
- **N19 (Vector + Feature Store):** _stub: TOY_DOCS (in-memory keyword overlap)_

**Nơi tốn nhiều ms nhất** trong pipeline (đo bằng `time.perf_counter` trong `pipeline.py`):

- embed: _N/A (toy retrieval, no embedding)_
- retrieve: _~0 ms_
- llama-server: _~2740-4735 ms_

**Reflection**: Bottleneck nằm hoàn toàn ở LLM inference (llama-server). Retrieval toy nên không đáng kể — trong production, embedding + vector search sẽ add latency nhưng vẫn << inference cost. Khớp kỳ vọng.

---

## 5. Bonus — The single change that mattered most

> **Most important section.** Pick **một** thay đổi từ bonus track (build flag, thread sweep, quant pick, GPU offload, KV-cache quantization, speculative decoding, bất cứ challenge nào trong `BONUS-llama-cpp-optimization/CHALLENGES.md`) đã tạo ra speedup lớn nhất trên máy bạn.

**Change:** _Thread count tuning: giảm từ 16 logical threads xuống 12 physical threads_

**Before vs after** (từ thread sweep):

```
t=16: ttft=317.4ms tpot=35.1ms tok/s=28.5
t=12: ttft=318.6ms tpot=29.5ms tok/s=33.9
speedup: ~1.19×
```

**Tại sao nó work**:

LLM inference (decode phase) là memory-bandwidth-bound, không phải compute-bound. Mỗi token cần đọc toàn bộ model weights từ RAM vào CPU cache — với Qwen2.5-1.5B Q4_K_M (~0.9GB), mỗi decode step đọc ~1.8GB (model weights) từ system memory. CPU memory bandwidth (DDR4 trên laptop này ~45-55 GB/s) là bottleneck.

Khi dùng 16 threads (logical cores bao gồm hyperthreads), 4 hyperthreads chia sẻ physical core với 4 threads khác, cạnh tranh cache L1/L2 và cùng memory channel — gây ra contention và slowdown. Physical 12 cores (6 P-cores + 6 E-cores) cho phép mỗi core độc lập đọc từ memory controller mà không stepping trên nhau. Kết quả: 12 threads > 16 threads, đúng với deck's prediction.

Kết quả này khớp với deck: với memory-bandwidth-bound workload, số thread = physical cores là sweet spot. Điều thú vị: ngay cả 6 threads cũng chỉ chậm hơn 12 threads ~1.36x (25 vs 33.9 tok/s), thể hiện scaling không lý tưởng vì bandwidth ceiling đã bão hòa ở ~6 threads.

---

## 6. (Optional) Điều ngạc nhiên nhất

Dù có NVIDIA RTX 3050 GPU, việc không có CUDA Toolkit khiến toàn bộ inference chạy trên CPU — nhưng Qwen2.5-1.5B Q4_K_M vẫn đạt ~33 tok/s decode với thread tuning, đủ dùng cho single-user chat. GPU offload hứa hẹn speedup đáng kể nếu build được CUDA.

---

## 7. Self-graded checklist

- [x] `hardware.json` đã commit
- [x] `models/active.json` đã commit
- [x] `benchmarks/01-quickstart-results.md` đã commit
- [x] `benchmarks/02-server-results.md` đã commit
- [x] `benchmarks/bonus-thread-sweep.md` đã commit (thread sweep)
- [ ] Ít nhất 6 screenshots trong `submission/screenshots/` (xem `submission/screenshots/README.md`) — _cần chụp thủ công_
- [ ] `make verify` exit 0 (chạy ngay trước khi push)
- [ ] Repo trên GitHub ở chế độ **public**
- [ ] Đã paste public repo URL vào VinUni LMS

---

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.
