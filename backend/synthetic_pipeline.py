#!/usr/bin/env python3
"""
Synthetic Pipeline Module
Contains data loading and preparation for the synthetic candidate dataset.
"""

import os
import json
import pandas as pd
from crewai import Agent, Task

def load_synthetic_data(dataset_path: str = "dataset/synt_prospect_5k.csv", num_rows: int = None):
    """
    Load synthetic candidate data from CSV file.
    
    Args:
        dataset_path: Path to the synthetic dataset CSV file
        num_rows: Number of rows to load (None for all)
        
    Returns:
        dict: Contains 'success', 'data' (JSON string), 'columns', and 'total_rows'
    """
    try:
        # Get absolute path
        if not os.path.isabs(dataset_path):
            # Assume it's relative to the backend directory
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            dataset_path = os.path.join(backend_dir, "..", dataset_path)
            dataset_path = os.path.normpath(dataset_path)
        
        if not os.path.exists(dataset_path):
            return {
                "success": False,
                "error": f"Dataset file not found: {dataset_path}"
            }
        
        # Load the dataset
        df = pd.read_csv(dataset_path, nrows=num_rows)
        
        # Convert to JSON
        data_json = df.to_json(orient='records')
        
        return {
            "success": True,
            "data": data_json,
            "columns": list(df.columns),
            "total_rows": len(df),
            "sample_size": num_rows if num_rows else len(df)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def create_data_loader_agent():
    """Create the Data Loader agent (Data Engineer)"""
    return Agent(
        role="Data Engineer",
        goal="Load and prepare candidate data from the synthetic dataset for analysis.",
        backstory="Data engineer specializing in dataset loading and preparation for candidate analysis.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )

def create_load_data_task(data_loader_agent: Agent, data_info: dict):
    """Create the data loading task with actual data embedded"""
    import json
    all_data = json.loads(data_info['data'])
    
    # For large datasets, we'll include all candidates but in compact JSON format (no indentation)
    # This allows processing many candidates while staying within token limits
    full_data_json = data_info['data']  # Already compact JSON from to_json()
    
    # Show a small sample with indentation for structure reference
    sample_data = all_data[:10]  # Small sample for structure reference
    sample_json = json.dumps(sample_data, indent=2)
    
    return Task(
        description=f"""Load and prepare the synthetic candidate dataset.

The dataset contains {data_info['total_rows']} total candidates in the full dataset, and we are processing {data_info['sample_size']} candidates with the following fields:
{', '.join(data_info['columns'])}

Here is a sample of candidate data (first 10 candidates to show the structure):

CANDIDATE_DATA_SAMPLE_START
{sample_json}
CANDIDATE_DATA_SAMPLE_END

The dataset with {data_info['sample_size']} candidates to process is provided below in compact JSON format. You MUST output ALL {data_info['sample_size']} candidates in your response:

CANDIDATE_DATA_START
{full_data_json}
CANDIDATE_DATA_END

Return ALL {data_info['sample_size']} candidates in JSON format, wrapped between CANDIDATE_DATA_START and CANDIDATE_DATA_END markers. Do not summarize - include the complete dataset.
""",
        agent=data_loader_agent,
        expected_output=f"Complete dataset with all {data_info['sample_size']} candidates in JSON format, wrapped between CANDIDATE_DATA_START and CANDIDATE_DATA_END markers"
    )

