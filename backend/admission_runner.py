#!/usr/bin/env python3
"""
Admission Runner for UDiscovery Admission Pipeline
This module provides a simple interface to run the admission assessment pipeline
and return results that can be displayed on the frontend.
"""

import os
import sys
import json
import subprocess
import logging
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging - redirect to stderr to keep stdout clean for JSON
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Send logs to stderr
)
logger = logging.getLogger(__name__)

def remove_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def run_admission_assessment(num_applications: int = None, batch_size: int = 50) -> dict:
    """
    Run the admission assessment pipeline.
    
    Args:
        num_applications: Number of applications to process (None for all)
        batch_size: Number of applications to process per batch (default 50)
        
    Returns:
        dict: Contains 'success' and either 'result' or 'error'
    """
    
    try:
        # Import the admission pipeline function
        from admission_agents_pipeline import execute_admission_pipeline
        
        logger.info(f"Running admission assessment pipeline for {num_applications or 'all'} applications...")
        logger.info(f"Using batch size: {batch_size}")
        
        # Run the pipeline
        result = execute_admission_pipeline(
            dataset_path="dataset/synt_admission.csv",
            num_applications=num_applications,
            batch_size=batch_size
        )
        
        if result is not None:
            # Convert result to JSON string
            result_json = json.dumps(result, indent=2)
            
            return {
                'success': True,
                'result': result_json
            }
        else:
            return {
                'success': False,
                'error': 'Admission pipeline execution returned no results'
            }
            
    except Exception as e:
        logger.error(f"Error running admission assessment: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # For testing
    import sys
    num_apps = None
    batch_size = 50  # Default batch size
    
    if len(sys.argv) > 1 and sys.argv[1].strip():
        try:
            num_apps = int(sys.argv[1])
        except ValueError:
            num_apps = None
    
    if len(sys.argv) > 2 and sys.argv[2].strip():
        try:
            batch_size = int(sys.argv[2])
        except ValueError:
            batch_size = 50
    
    result = run_admission_assessment(num_apps, batch_size)
    # Print only JSON to stdout, everything else goes to stderr
    # Use sys.stdout.write to avoid any extra formatting
    sys.stdout.write(json.dumps(result) + '\n')
    sys.stdout.flush()  # Ensure output is flushed

