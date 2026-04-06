"""
app_v3.py — Backward-compatibility redirect.

All functionality has been consolidated into app.py, which is the
single unified entry point for AIOS covering all modes.

This file exists so that existing docs, scripts, and CI pipelines
that call `python app_v3.py` continue to work without changes.

    python app_v3.py                  → workspace mode (same as app.py)
    python app_v3.py --mode legacy    → legacy chat interface
    python app_v3.py --mode workspace → AI-native workspace
"""
from app import main

if __name__ == "__main__":
    main()
