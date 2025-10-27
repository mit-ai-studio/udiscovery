#!/usr/bin/env python3
"""
Demo Runner for UDiscovery Pipeline
This module provides a simple interface to run the UDiscovery pipeline
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

def run_udiscovery_demo(university_goal: str) -> dict:
    """
    Run the UDiscovery pipeline with the given university goal.
    
    Args:
        university_goal: The university's program goal/prompt
        
    Returns:
        dict: Contains 'success' and either 'result' or 'error'
    """
    
    try:
        # Import the test function from test_real_agents
        from test_real_agents import run_pipeline_with_goal
        
        logger.info(f"Running UDiscovery demo with goal: {university_goal[:100]}...")
        
        # Run the pipeline
        result = run_pipeline_with_goal(university_goal)
        
        if result:
            # Extract the text from the result
            # CrewAI returns result objects, check what attributes are available
            if hasattr(result, 'raw'):
                result_text = result.raw
            elif hasattr(result, 'content'):
                result_text = result.content
            elif hasattr(result, '__dict__'):
                # Try to get all attributes
                result_text = str(result)
            else:
                result_text = str(result)
            
            # Clean ANSI codes
            result_text = remove_ansi_codes(result_text)
            
            # Log first 500 chars for debugging
            # logger.info(f"Result preview: {result_text[:500]}")
            
            return {
                'success': True,
                'result': result_text
            }
        else:
            return {
                'success': False,
                'error': 'Pipeline execution returned no results'
            }
            
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # For testing
    if len(sys.argv) > 1:
        goal = sys.argv[1]
    else:
        goal = """
        Our primary objective is to build a diverse and mission-driven cohort across all Harvard Graduate School of Education (HGSE) master's programs.
        """
    
    result = run_udiscovery_demo(goal)
    print(json.dumps(result, indent=2))
