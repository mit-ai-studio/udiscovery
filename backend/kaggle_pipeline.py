#!/usr/bin/env python3
"""
Kaggle Pipeline Module
Contains Kaggle-related agents and tasks for dataset discovery and data ingestion.
"""

import os
import json
import subprocess
import csv
from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel

# Create CrewAI-compatible tools
class SearchKaggleInput(BaseModel):
    search_query: str

class SearchKaggleTool(BaseTool):
    name: str = "search_kaggle_datasets"
    description: str = "Search for Kaggle datasets using the Kaggle CLI. Input should be a search query string."
    args_schema: type[BaseModel] = SearchKaggleInput
    
    def _run(self, search_query: str) -> str:
        """Execute Kaggle dataset search"""
        try:
            cmd = f"kaggle datasets list -s '{search_query}' --csv -p 5"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            csv_reader = csv.DictReader(result.stdout.strip().split('\n'))
            dataset_slugs = []
            for row in csv_reader:
                if 'ref' in row and row['ref']:
                    dataset_slugs.append(row['ref'])
            return json.dumps(dataset_slugs[:5])
        except Exception as e:
            return json.dumps({"error": str(e)})

# Create tool instance
search_tool = SearchKaggleTool()

def create_scout_agent():
    """Create the Kaggle Scout agent (Data Sourcing Specialist)"""
    return Agent(
        role="Data Sourcing Specialist",
        goal="Find relevant Kaggle datasets using search keywords.",
        backstory="Specialist in finding datasets. Use search tool efficiently and return results quickly.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[search_tool],
        max_iter=2,  # Reduced from 3 to save tokens
        verbose=False
    )

def create_evaluator_agent():
    """Create the Dataset Evaluator agent (Dataset Quality Analyst)"""
    return Agent(
        role="Dataset Quality Analyst",
        goal="Select the best dataset from the list for candidate analysis.",
        backstory="Expert at evaluating datasets for relevance and data quality.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )

def create_ingestion_agent():
    """Create the Data Ingestion agent (Data Engineer)"""
    return Agent(
        role="Data Engineer",
        goal="Prepare candidate data from the selected dataset for analysis.",
        backstory="Data engineer specializing in dataset preparation and formatting.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )

def create_search_task(scout_agent: Agent, blueprint_task: Task):
    """Create the search task for finding Kaggle datasets"""
    return Task(
        description="""Search Kaggle using search_kaggle_datasets tool with keyword "resume" (not "dataset" or "resume dataset").

Return numbered list:
"Datasets found:
1. username1/dataset-name-1
2. username2/dataset-name-2
3. username3/dataset-name-3"

If no results: "No datasets found".""",
        agent=scout_agent,
        context=[blueprint_task],
        expected_output="Numbered list of dataset slugs"
    )

def create_evaluate_task(evaluator_agent: Agent, search_task: Task):
    """Create the evaluate task for selecting the best dataset"""
    return Task(
        description="""From Agent 2's dataset list, select the ONE best dataset for finding educational leaders.

Return: "Selected dataset: username/dataset-name" """,
        agent=evaluator_agent,
        context=[search_task],
        expected_output="Dataset slug in format: username/dataset-name"
    )

def create_ingest_task(ingestion_agent: Agent, evaluate_task: Task):
    """Create the ingest task for data preparation"""
    return Task(
        description="""Confirm data preparation from the selected dataset.

Return: "Data ingestion would download dataset [dataset-slug] and prepare candidate profiles for analysis." """,
        agent=ingestion_agent,
        context=[evaluate_task],
        expected_output="Confirmation message with dataset slug"
    )

