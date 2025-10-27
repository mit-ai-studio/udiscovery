#!/usr/bin/env python3
"""
CLI interface for running UDiscovery demo
This script is called by Node.js to execute the pipeline
"""

import sys
import json
import os
from demo_runner import run_udiscovery_demo

if __name__ == "__main__":
    # Read university goal from command line argument
    if len(sys.argv) > 1:
        university_goal = sys.argv[1]
        # Try to decode JSON if it's JSON-encoded
        try:
            university_goal = json.loads(university_goal)
        except json.JSONDecodeError:
            pass  # Use as-is if not JSON
    else:
        university_goal = sys.stdin.read()
    
    # Run the demo
    result = run_udiscovery_demo(university_goal)
    
    # Print result as JSON
    print(json.dumps(result))
    sys.exit(0 if result.get('success') else 1)
