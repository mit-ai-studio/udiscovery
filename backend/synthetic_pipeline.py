#!/usr/bin/env python3
"""
Synthetic Pipeline Module
Contains data loading and preparation for the synthetic candidate dataset.
"""

import os
import json
import pandas as pd
from crewai import Agent, Task

def load_synthetic_data(dataset_path: str = "dataset/synt_prospec.csv", num_rows: int = None):
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
    return Task(
        description=f"""Load and prepare the synthetic candidate dataset.

The dataset has been loaded and contains {data_info['total_rows']} candidates with the following fields:
{', '.join(data_info['columns'])}

Here is the candidate data (first {data_info['sample_size']} candidates):

CANDIDATE_DATA_START
{data_info['data']}
CANDIDATE_DATA_END

Return a summary:
- Total number of candidates: {data_info['total_rows']}
- Key fields available: {', '.join(data_info['columns'][:10])}...
- Sample of 5 candidates with their key information (name, position, experience, education)

Format:
"Dataset loaded successfully. Found {data_info['total_rows']} candidates.

Available fields: {', '.join(data_info['columns'])}

Sample candidates:
1. [Full Name: first_name + last_name] - [Current Position], [Years Work Experience] years work exp, [Years Education Experience] years education exp, [Prior Degree Level] in [Prior Degree Field]. Interest: [Interest]. GPA: [GPA]. Located in [State].
2. [Full Name] - [Current Position], [Years Work Experience] years work exp, [Years Education Experience] years education exp, [Prior Degree Level] in [Prior Degree Field]. Interest: [Interest]. GPA: [GPA]. Located in [State].
[Continue for 5 candidates]"
""",
        agent=data_loader_agent,
        expected_output="Summary of loaded candidate data with sample records"
    )

