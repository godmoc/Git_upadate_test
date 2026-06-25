import sys

packages = ["streamlit", "yfinance", "pandas", "plotly"]
print("Python:", sys.version)
print("-" * 40)
for pkg in packages:
    try:
        mod = __import__(pkg)
        print(f"[OK] {pkg:10s} {getattr(mod, '__version__', '?')}")
    except ImportError as e:
        print(f"[FAIL] {pkg:10s} {e}")
print("-" * 40)
print("All packages installed!" if all(__import__(p) for p in packages) else "Some packages missing!")