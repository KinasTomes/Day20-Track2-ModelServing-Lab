#!/usr/bin/env python3
"""Quick thread sweep using llama-cpp-python directly."""
from __future__ import annotations

import json
import time
from pathlib import Path

from llama_cpp import Llama


def main() -> int:
    model = json.loads(Path("models/active.json").read_text())["primary_model"]
    hw = json.loads(Path("hardware.json").read_text())
    physical = hw["cpu"].get("cores_physical") or 4
    logical = hw["cpu"]["cores_logical"]

    grid = sorted({1, 2, max(physical // 4, 1) * 2, physical // 2, physical, logical})
    grid = [t for t in grid if t <= logical]

    prompt = "Explain TTFT and TPOT in one sentence each."
    results = []

    for t in grid:
        llm = Llama(
            model_path=model, n_ctx=512, n_threads=t, n_batch=512, n_gpu_layers=0, verbose=False
        )
        start = time.perf_counter()
        n_tokens = 0
        first_token_at = None
        for chunk in llm.create_completion(prompt=prompt, max_tokens=64, temperature=0.0, stream=True):
            text = chunk["choices"][0].get("text", "")
            if text and first_token_at is None:
                first_token_at = time.perf_counter()
            if text:
                n_tokens += 1
        end = time.perf_counter()
        ttft = (first_token_at - start) * 1000 if first_token_at else 0
        decode_ms = (end - (first_token_at or start)) * 1000
        tpot = decode_ms / max(n_tokens - 1, 1) if n_tokens > 1 else 0
        tok_s = round(1000.0 / tpot, 1) if tpot > 0 else 0
        results.append({"threads": t, "ttft_ms": round(ttft, 1), "tpot_ms": round(tpot, 1), "tok_s": tok_s})
        print(f"  t={t:2d}: ttft={ttft:6.1f}ms tpot={tpot:5.1f}ms tok/s={tok_s:5.1f}")

    out_dir = Path("benchmarks")
    out_dir.mkdir(exist_ok=True)

    best = max(results, key=lambda r: r["tok_s"])
    md = "# Bonus - Thread Sweep\n\n"
    md += "| threads | TTFT (ms) | TPOT (ms) | tok/s |\n|---:|---:|---:|---:|\n"
    for r in results:
        md += f"| {r['threads']} | {r['ttft_ms']} | {r['tpot_ms']} | {r['tok_s']} |\n"
    md += f"\n**Best**: {best['threads']} threads at {best['tok_s']} tok/s.\n"
    Path(out_dir / "bonus-thread-sweep.md").write_text(md, encoding="utf-8")
    Path(out_dir / "bonus-thread-sweep.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n" + md)
    return 0


if __name__ == "__main__":
    exit(main())
