# Hướng dẫn chạy benchmark để chụp screenshot

> Chạy các lệnh sau trong terminal (PowerShell) tại thư mục gốc của repo.
> Dùng `.venv` đã tạo sẵn: `.\.venv\Scripts\Activate.ps1`

---

## 1. Hardware probe — `01-hardware-probe.png`

```powershell
$env:PYTHONIOENCODING='utf-8'; python 00-setup/detect-hardware.py
```

**Chụp**: toàn bộ output từ `Platform:` đến `Saved hardware.json`.

---

## 2. Quickstart benchmark — `02-quickstart-bench.png`

```powershell
$env:PYTHONIOENCODING='utf-8'; python 01-llama-cpp-quickstart/benchmark.py
```

**Chụp**: phần per-prompt table (`[1/10]` đến `[10/10]`) + summary table cuối.

---

## 3. Server running — `03-server-running.png`

**Bước A** — Mở **terminal riêng**, chạy server:

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m llama_cpp.server --model models/qwen2.5-1.5b-instruct-q4_k_m.gguf --host 0.0.0.0 --port 8080 --n_threads 12 --n_gpu_layers 99 --n_ctx 2048
```

**Chụp**: dòng `Uvicorn running on http://0.0.0.0:8080`.

**Bước B** — Ở terminal khác, smoke-test:

```powershell
python 02-llama-cpp-server/smoke-test.py
```

---

## 4. Locust 10 users — `04-locust-10.png`

Server phải đang chạy từ bước 3. Ở terminal khác:

```powershell
.\.venv\Scripts\locust.exe -f 02-llama-cpp-server/load-test.py --headless -u 10 -r 1 -t 1m --host http://localhost:8080
```

**Chụp**: phần `Response time percentiles` cuối cùng (P50, P95, P99, # reqs).

---

## 5. Locust 50 users — `05-locust-50.png`

```powershell
.\.venv\Scripts\locust.exe -f 02-llama-cpp-server/load-test.py --headless -u 50 -r 1 -t 1m --host http://localhost:8080
```

**Chụp**: phần `Response time percentiles` cuối cùng.

---

## 6. Bonus sweep — `06-bonus-sweep.png`

```powershell
$env:PYTHONIOENCODING='utf-8'; python BONUS-llama-cpp-optimization/benchmarks/quick-thread-sweep.py
```

**Chụp**: toàn bộ output bảng thread sweep.

---

## Tips chụp ảnh

- Dùng **Snipping Tool** (Windows + Shift + S) để crop gọn, chỉ lấy terminal output.
- File PNG, đặt đúng tên trong thư mục `submission/screenshots/`.
- Sau khi có đủ 6 ảnh, chạy verify: `python scripts/verify.py`
