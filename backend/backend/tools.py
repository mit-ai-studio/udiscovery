"""
UDiscovery Agentic Pipeline - Tools Module

This module contains the KaggleTools class with all necessary functions
for interacting with Kaggle datasets using the Kaggle CLI.
"""

import subprocess
import pandas as pd
import json
import os
import csv
from typing import List
from langchain_core.tools import tool


class KaggleTools:
    """
    A class containing tools for interacting with Kaggle datasets.
    All methods are decorated with @tool for use in LangChain agents.
    """
    
    @tool
    def search_kaggle_datasets(self, search_query: str) -> str:
        """
        Search for Kaggle datasets using the Kaggle CLI.
        
        Args:
            search_query (str): The search term to find relevant datasets
            
        Returns:
            str: A JSON string containing a list of the top 5 dataset slugs
        """
        try:
            # Execute Kaggle CLI command to search datasets
            cmd = f"kaggle datasets list -s '{search_query}' --csv -p 5"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            
            # Parse CSV output
            csv_reader = csv.DictReader(result.stdout.strip().split('\n'))
            dataset_slugs = []
            
            for row in csv_reader:
                if 'ref' in row and row['ref']:
                    # Extract slug from ref (format: username/dataset-name)
                    slug = row['ref']
                    dataset_slugs.append(slug)
            
            # Return as JSON string
            return json.dumps(dataset_slugs[:5])  # Ensure we only return top 5
            
        except subprocess.CalledProcessError as e:
            return json.dumps({"error": f"Kaggle CLI error: {e.stderr}"})
        except Exception as e:
            return json.dumps({"error": f"Unexpected error: {str(e)}"})
    
    @tool
    def inspect_dataset_files(self, dataset_slug: str) -> str:
        """
        Inspect the files within a specific Kaggle dataset.
        
        Args:
            dataset_slug (str): The dataset slug (username/dataset-name)
            
        Returns:
            str: A JSON string containing a list of filenames in the dataset
        """
        try:
            # Execute Kaggle CLI command to list dataset files
            cmd = f"kaggle datasets files '{dataset_slug}' --csv"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            
            # Parse CSV output
            csv_reader = csv.DictReader(result.stdout.strip().split('\n'))
            filenames = []
            
            for row in csv_reader:
                if 'name' in row and row['name']:
                    filenames.append(row['name'])
            
            return json.dumps(filenames)
            
        except subprocess.CalledProcessError as e:
            return json.dumps({"error": f"Kaggle CLI error: {e.stderr}"})
        except Exception as e:
            return json.dumps({"error": f"Unexpected error: {str(e)}"})
    
    @tool
    def download_kaggle_dataset(self, dataset_slug: str) -> str:
        """
        Download and unzip a Kaggle dataset.
        
        Args:
            dataset_slug (str): The dataset slug (username/dataset-name)
            
        Returns:
            str: The full file path to the first CSV file found in the downloaded dataset
        """
        try:
            # Create download directory if it doesn't exist
            download_dir = "downloaded_dataset"
            os.makedirs(download_dir, exist_ok=True)
            
            # Execute Kaggle CLI command to download dataset
            cmd = f"kaggle datasets download -d '{dataset_slug}' -p {download_dir} --unzip"
            subprocess.run(cmd, shell=True, check=True)
            
            # Scan the downloaded directory for CSV files
            csv_files = []
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    if file.endswith('.csv'):
                        csv_files.append(os.path.join(root, file))
            
            if csv_files:
                # Return the first CSV file found
                return csv_files[0]
            else:
                return json.dumps({"error": "No CSV files found in downloaded dataset"})
                
        except subprocess.CalledProcessError as e:
            return json.dumps({"error": f"Kaggle CLI error: {e.stderr}"})
        except Exception as e:
            return json.dumps({"error": f"Unexpected error: {str(e)}"})
    
    @tool
    def read_csv_data(self, csv_file_path: str) -> str:
        """
        Read CSV data using pandas and return as JSON.
        
        Args:
            csv_file_path (str): The full path to the CSV file
            
        Returns:
            str: JSON string containing the first 50 rows of the CSV data
        """
        try:
            # Check if file exists
            if not os.path.exists(csv_file_path):
                return json.dumps({"error": f"File not found: {csv_file_path}"})
            
            # Read CSV with pandas (first 50 rows only)
            df = pd.read_csv(csv_file_path, nrows=50)
            
            # Convert to JSON string
            json_data = df.to_json(orient='records')
            return json_data
            
        except pd.errors.EmptyDataError:
            return json.dumps({"error": "CSV file is empty"})
        except pd.errors.ParserError as e:
            return json.dumps({"error": f"CSV parsing error: {str(e)}"})
        except Exception as e:
            return json.dumps({"error": f"Unexpected error: {str(e)}"})


# Create a global instance for easy access
kaggle_tools = KaggleTools()
