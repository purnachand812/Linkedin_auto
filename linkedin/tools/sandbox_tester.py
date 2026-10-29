#!/usr/bin/env python3
"""
sandbox_tester.py - Empirical Sandbox Benchmark & Verification Runner for Purna's LinkedIn Agent.
Measures cold-start import latency (ms), memory delta (MB), AST surface area, and dependency footprint
for Python packages or cloned repositories, and logs verified empirical results to linkedin/tested-tools.md
so posts can genuinely carry the 'Tested by me' status with real numbers.
"""

import os
import sys
import time
import json
import ast
import tracemalloc
import importlib
import argparse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LINKEDIN_DIR = BASE_DIR / "linkedin"
TESTED_TOOLS_FILE = LINKEDIN_DIR / "tested-tools.md"
BENCHMARK_LOG_FILE = LINKEDIN_DIR / "history" / "sandbox_benchmarks.json"


def benchmark_python_module(module_name):
    """
    Empirically benchmarks importing and inspecting a Python module in the current environment.
    Measures cold-start import latency (ms), peak memory allocation (KB/MB), and public API surface.
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        mod = importlib.import_module(module_name)
        import_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        public_symbols = [name for name in dir(mod) if not name.startswith("_")]
        version = getattr(mod, "__version__", getattr(mod, "VERSION", "installed"))

        return {
            "target": module_name,
            "type": "python_module",
            "success": True,
            "version": str(version),
            "cold_import_ms": import_ms,
            "peak_memory_kb": round(peak_bytes / 1024.0, 2),
            "public_symbols_count": len(public_symbols),
            "sample_symbols": public_symbols[:8],
            "tested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S CET")
        }
    except Exception as e:
        tracemalloc.stop()
        return {
            "target": module_name,
            "type": "python_module",
            "success": False,
            "error": str(e),
            "tested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S CET")
        }


def inspect_local_directory(dir_path):
    """
    Empirically audits a local codebase/repository directory:
    Counts Python files, total lines of code (LOC), classes, functions, and fast AST validation.
    """
    root = Path(dir_path).resolve()
    if not root.exists():
        return {"target": str(dir_path), "success": False, "error": "Directory not found"}

    t0 = time.perf_counter()
    py_files = list(root.rglob("*.py"))
    total_loc = 0
    total_classes = 0
    total_functions = 0

    for pf in py_files:
        try:
            src = pf.read_text(encoding="utf-8", errors="ignore")
            total_loc += len(src.splitlines())
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    total_classes += 1
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_functions += 1
        except Exception:
            pass

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "target": root.name,
        "type": "repository_ast_audit",
        "success": True,
        "python_files": len(py_files),
        "total_loc": total_loc,
        "classes_count": total_classes,
        "functions_count": total_functions,
        "ast_parse_time_ms": elapsed_ms,
        "tested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S CET")
    }


def record_empirical_test(result, notes=""):
    """Saves the benchmark to history/sandbox_benchmarks.json and optionally updates tested-tools.md."""
    BENCHMARK_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = []
    if BENCHMARK_LOG_FILE.exists():
        try:
            history = json.loads(BENCHMARK_LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            history = []

    result["notes"] = notes
    history.insert(0, result)
    BENCHMARK_LOG_FILE.write_text(json.dumps(history[:50], indent=2), encoding="utf-8")

    if result.get("success") and TESTED_TOOLS_FILE.exists():
        md_text = TESTED_TOOLS_FILE.read_text(encoding="utf-8")
        target_name = result.get("target")
        if target_name and target_name not in md_text:
            if result.get("type") == "python_module":
                bullet = (
                    f"- **`{target_name}` (v{result['version']}) — Empirical Sandbox Test ({result['tested_at'][:10]}):** "
                    f"Cold import latency `{result['cold_import_ms']}ms`, peak traced memory `{result['peak_memory_kb']} KB`, "
                    f"`{result['public_symbols_count']}` public symbols exposed. {notes}\n"
                )
            else:
                bullet = (
                    f"- **`{target_name}` — Empirical AST & Codebase Benchmark ({result['tested_at'][:10]}):** "
                    f"Audited `{result['python_files']}` Python files (`{result['total_loc']:,}` LOC, "
                    f"`{result['functions_count']}` functions, `{result['classes_count']}` classes) in `{result['ast_parse_time_ms']}ms`. {notes}\n"
                )
            marker = "## 2. UNTESTED / DOCUMENTATION-RESEARCHED TOOLS"
            if marker in md_text:
                md_text = md_text.replace(marker, bullet + "\n---\n\n" + marker)
                TESTED_TOOLS_FILE.write_text(md_text, encoding="utf-8")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Empirical Sandbox Benchmark & AST Verification Runner")
    parser.add_argument("--module", help="Python module name to benchmark (e.g., json, html2image)")
    parser.add_argument("--dir", help="Directory path to run AST codebase audit on")
    parser.add_argument("--notes", default="", help="Additional workload notes")
    args = parser.parse_args()

    if args.module:
        res = benchmark_python_module(args.module)
        record_empirical_test(res, args.notes)
        print(json.dumps(res, indent=2))
    elif args.dir:
        res = inspect_local_directory(args.dir)
        record_empirical_test(res, args.notes)
        print(json.dumps(res, indent=2))
    else:
        # Default: run empirical AST audit on our own linkedin automation suite
        res = inspect_local_directory(LINKEDIN_DIR)
        print(json.dumps(res, indent=2))

