#!/usr/bin/env python3
"""
Quick test script to verify the backend is working
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is set
if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not set in .env file")
    sys.exit(1)

print("✅ GOOGLE_API_KEY is set")

# Try importing required modules
try:
    from synthetic_agents_pipeline import run_pipeline_with_goal
    print("✅ Successfully imported synthetic_agents_pipeline")
except ImportError as e:
    print(f"ERROR: Failed to import synthetic_agents_pipeline: {e}")
    sys.exit(1)

# Try loading the dataset
try:
    from synthetic_pipeline import load_synthetic_data
    data_info = load_synthetic_data("dataset/synt_prospect_5k.csv", num_rows=10)
    if data_info["success"]:
        print(f"✅ Successfully loaded dataset ({data_info['total_rows']} total candidates)")
    else:
        print(f"ERROR: Failed to load dataset: {data_info.get('error')}")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to load dataset: {e}")
    sys.exit(1)

print("\n✅ Backend is ready!")
print("You can now test with a small batch by running:")
print("  python run_demo_cli.py 'Test goal'")

