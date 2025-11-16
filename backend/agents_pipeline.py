#!/usr/bin/env python3
"""
UDiscovery Pipeline - Main Agents Execution
This module contains the CrewAI agents pipeline that orchestrates candidate discovery.
Creates Agent objects with roles, backstories, and tools to execute the full pipeline.
"""

import os
import sys
import json
import logging
import subprocess
import csv
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Set up logging
log_filename = f"udiscovery_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

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

def run_pipeline_with_goal(university_goal: str):
    """
    Run the UDiscovery pipeline with a custom university goal.
    This function is called by the frontend via demo_runner.py
    
    Args:
        university_goal: The university's program goal/prompt
        
    Returns:
        The final result from the pipeline execution
    """
    return execute_pipeline(university_goal)

def execute_pipeline(university_goal=None):
    """Execute the UDiscovery pipeline with a specific university goal"""
    
    if university_goal is None:
        # Default HGSE goal if not provided
        university_goal = """
    Our primary objective is to build a diverse and mission-driven cohort across all Harvard Graduate School of Education (HGSE) master's programs. We are not just looking for academics; we are looking for future **leaders, innovators, and changemakers** who want to have a systemic impact on the field of education.

    Ideal candidates often have **3-10 years of professional experience** and come from a wide range of backgrounds, including **K-12 teaching, school administration, non-profit management, education policy, and ed-tech**.

    We want to find individuals who demonstrate a deep commitment to **equity, social justice, and innovation**. Your task is to find datasets containing profiles we can analyze for these signals. Look for keywords indicating leadership, initiative, and a desire to solve complex educational problems, such as 'program manager,' 'department head,' 'founder,' 'principal,' or active involvement in 'community engagement,' 'policy writing,' or 'curriculum development'.
    """
    
    logger.info("=" * 80)
    logger.info("🚀 UDiscovery REAL Agentic Pipeline - CrewAI Agents")
    logger.info("=" * 80)
    
    # Initialize LLM - CrewAI expects a string or specific format
    google_key = os.getenv("GOOGLE_API_KEY")
    # For CrewAI, we use the model string directly
    llm_model = "gemini-2.0-flash"
    os.environ["GEMINI_API_KEY"] = google_key
    
    # Create Agent 1: Trait Inferrer
    logger.info("Creating Agent 1: Trait Inferrer...")
    trait_agent = Agent(
        role="University Strategy Analyst",
        goal="Transform university goals into candidate blueprint with ideal traits and Kaggle search keywords.",
        backstory="Expert in graduate admissions who translates institutional goals into specific candidate profiles.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )
    logger.info("✅ Trait Inferrer Agent created")
    
    # Create Agent 2: Kaggle Scout
    logger.info("Creating Agent 2: Kaggle Scout...")
    scout_agent = Agent(
        role="Data Sourcing Specialist",
        goal="Find relevant Kaggle datasets using search keywords.",
        backstory="Specialist in finding datasets. Use search tool efficiently and return results quickly.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[search_tool],
        max_iter=2,  # Reduced from 3 to save tokens
        verbose=False
    )
    logger.info("✅ Kaggle Scout Agent created")
    
    # Create Task 1: Create Blueprint
    logger.info("Creating Task 1: Create Blueprint...")
    blueprint_task = Task(
        description=f"""Analyze these university goals and create a candidate blueprint:

{university_goal}

Return JSON with:
- "ideal_profile": Description of ideal candidate traits
- "kaggle_search_keywords": 5-10 general search terms (use: "resumes", "employees", "workers", "profiles", "careers", "professional", "linkedin", "job market")""",
        agent=trait_agent,
        expected_output="JSON: ideal_profile and kaggle_search_keywords list"
    )
    logger.info("✅ Blueprint Task created")
    
    # Create Task 2: Find Datasets
    logger.info("Creating Task 2: Find Datasets...")
    search_task = Task(
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
    logger.info("✅ Search Task created")
    
    # Create Agent 3: Dataset Evaluator
    logger.info("Creating Agent 3: Dataset Evaluator...")
    evaluator_agent = Agent(
        role="Dataset Quality Analyst",
        goal="Select the best dataset from the list for candidate analysis.",
        backstory="Expert at evaluating datasets for relevance and data quality.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )
    logger.info("✅ Dataset Evaluator Agent created")
    
    # Create Agent 4: Data Ingestion
    logger.info("Creating Agent 4: Data Ingestion...")
    ingestion_agent = Agent(
        role="Data Engineer",
        goal="Prepare candidate data from the selected dataset for analysis.",
        backstory="Data engineer specializing in dataset preparation and formatting.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )
    logger.info("✅ Data Ingestion Agent created")
    
    # Create Agent 5: Propensity Modeler
    logger.info("Creating Agent 5: Propensity Modeler...")
    modeler_agent = Agent(
        role="Admissions Propensity Modeler",
        goal="Score and rank top 10 candidates with detailed justifications.",
        backstory="Expert in candidate evaluation and scoring for graduate admissions.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )
    logger.info("✅ Propensity Modeler Agent created")
    
    # Create Task 3: Evaluate Datasets
    logger.info("Creating Task 3: Evaluate Datasets...")
    evaluate_task = Task(
        description="""From Agent 2's dataset list, select the ONE best dataset for finding educational leaders.

Return: "Selected dataset: username/dataset-name" """,
        agent=evaluator_agent,
        context=[search_task],
        expected_output="Dataset slug in format: username/dataset-name"
    )
    logger.info("✅ Evaluate Task created")
    
    # Create Task 4: Ingest Data
    logger.info("Creating Task 4: Ingest Data...")
    ingest_task = Task(
        description="""Confirm data preparation from the selected dataset.

Return: "Data ingestion would download dataset [dataset-slug] and prepare candidate profiles for analysis." """,
        agent=ingestion_agent,
        context=[evaluate_task],
        expected_output="Confirmation message with dataset slug"
    )
    logger.info("✅ Ingest Task created")
    
    # Create Task 5: Rank Candidates
    logger.info("Creating Task 5: Rank Candidates...")
    rank_task = Task(
        description="""Score and rank top 10 candidates using the ideal profile from Agent 1.

Format EXACTLY as:
"Top 10 Candidates for Harvard Graduate School of Education:

1. [Full Name]
   Score: XX/100
   Background: [Detailed professional background with experience, sector, achievements]
   Why they match: [Specific reasons why this candidate is a good fit]

2. [Full Name]
   Score: XX/100
   Background: [Detailed background]
   Why they match: [Detailed explanation]

[Continue for all 10 candidates]""",
        agent=modeler_agent,
        context=[blueprint_task, ingest_task],
        expected_output="Ranked list of 10 candidates with scores, names, backgrounds, and matching explanations"
    )
    logger.info("✅ Rank Task created")
    
    # Create Crew
    logger.info("Creating Crew...")
    crew = Crew(
        agents=[trait_agent, scout_agent, evaluator_agent, ingestion_agent, modeler_agent],
        tasks=[blueprint_task, search_task, evaluate_task, ingest_task, rank_task],
        process=Process.sequential,
        verbose=False  # Reduced verbosity to save tokens
    )
    logger.info("✅ Crew created")
    
    # Execute
    logger.info("=" * 80)
    logger.info("⚡ Starting Crew execution...")
    logger.info("=" * 80)
    
    try:
        result = crew.kickoff()
        
        logger.info("=" * 80)
        logger.info("🎉 Crew execution completed!")
        logger.info("=" * 80)
        logger.info(f"Result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def run_pipeline():
    """Run the UDiscovery pipeline with default HGSE goal"""
    return execute_pipeline()

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not set")
        sys.exit(1)
    
    run_pipeline()
