#!/usr/bin/env python3
"""
UDiscovery Pipeline with REAL CrewAI Agents
This version creates actual Agent objects with roles, backstories, and tools
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
log_filename = f"udiscovery_real_agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

def test_real_agentic_pipeline():
    """Test with REAL CrewAI agents"""
    
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
        goal="""Transform high-level university program goals into a detailed candidate blueprint 
        that includes ideal candidate traits and Kaggle search keywords for data sourcing.""",
        backstory="""You are an expert university strategy analyst with deep experience in 
        graduate admissions and student success patterns. You understand how to translate 
        institutional goals into specific candidate profiles that drive enrollment success. 
        Your expertise lies in identifying the key traits, experiences, and characteristics 
        that predict student success in specific graduate programs.""",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",  # CrewAI expects this format
        tools=[],
        verbose=True
    )
    logger.info("✅ Trait Inferrer Agent created")
    
    # Create Agent 2: Kaggle Scout
    logger.info("Creating Agent 2: Kaggle Scout...")
    scout_agent = Agent(
        role="Data Sourcing Specialist",
        goal="""Use provided search keywords to discover and identify the most relevant 
        Kaggle datasets that contain candidate information matching the university's needs.""",
        backstory="""You are a skilled data sourcing specialist with extensive experience 
        in finding and evaluating datasets across various platforms. You excel at translating 
        search requirements into effective queries and identifying high-quality datasets that 
        contain the specific information needed for candidate analysis. You work efficiently 
        and stop after finding sufficient results.""",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[search_tool],
        max_iter=3,  # Limit iterations - just one search and return
        verbose=True
    )
    logger.info("✅ Kaggle Scout Agent created")
    
    # Create Task 1: Create Blueprint
    logger.info("Creating Task 1: Create Blueprint...")
    blueprint_task = Task(
        description=f"""Analyze the following university program goals and create a candidate blueprint:
        
        {university_goal}
        
        IMPORTANT: For kaggle_search_keywords, focus on GENERAL employee/resume/worker datasets, NOT 
        education-specific ones. Think broad professional datasets that contain:
        - Resume databases
        - Employee profiles
        - Workforce data
        - Professional backgrounds
        - Career information
        
        Use terms like: "resumes", "employees", "workers", "profiles", "careers", "professional", 
        "linkedin", "job market", etc. We want to find broad professional datasets that we can filter 
        for educational backgrounds later.
        
        Return a JSON object with:
        1. "ideal_profile": Detailed description of ideal candidate traits
        2. "kaggle_search_keywords": List of 5-10 GENERAL search terms for broad resume/employee datasets""",
        agent=trait_agent,
        expected_output="A JSON object with ideal_profile and general kaggle_search_keywords"
    )
    logger.info("✅ Blueprint Task created")
    
    # Create Task 2: Find Datasets
    logger.info("Creating Task 2: Find Datasets...")
    search_task = Task(
        description="""Search for Kaggle datasets. 
        
        Use the search_kaggle_datasets tool with the keyword "resume".
        Do NOT add "dataset" to the keyword - just use "resume".
        
        After the tool returns results, return a simple numbered list like:
        "Datasets found:
        1. username1/dataset-name-1
        2. username2/dataset-name-2
        3. username3/dataset-name-3"
        
        If no results, return "No datasets found".""",
        agent=scout_agent,
        context=[blueprint_task],
        expected_output="A simple numbered list of dataset slugs or 'No datasets found'"
    )
    logger.info("✅ Search Task created")
    
    # Create Agent 3: Dataset Evaluator
    logger.info("Creating Agent 3: Dataset Evaluator...")
    evaluator_agent = Agent(
        role="Dataset Quality Analyst",
        goal="""Evaluate the file contents and structure of multiple datasets to identify 
        the single best dataset that contains the most relevant and comprehensive candidate data.""",
        backstory="""You are a meticulous dataset quality analyst with expertise in evaluating 
        data sources for completeness, relevance, and usability. You have a keen eye for 
        identifying datasets that contain the right mix of candidate attributes and sufficient 
        data quality for meaningful analysis.""",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],  # No tools for this agent
        verbose=True
    )
    logger.info("✅ Dataset Evaluator Agent created")
    
    # Create Agent 4: Data Ingestion
    logger.info("Creating Agent 4: Data Ingestion...")
    ingestion_agent = Agent(
        role="Data Engineer",
        goal="""Download the selected dataset, locate the relevant CSV files, and prepare 
        a clean sample of candidate data for analysis and scoring.""",
        backstory="""You are an experienced data engineer specializing in data ingestion and 
        preparation. You excel at downloading datasets, handling various file formats, 
        and preparing clean, structured data for downstream analysis. Your attention to 
        detail ensures data quality and proper formatting.""",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],  # We'll use direct calls for now
        verbose=True
    )
    logger.info("✅ Data Ingestion Agent created")
    
    # Create Agent 5: Propensity Modeler
    logger.info("Creating Agent 5: Propensity Modeler...")
    modeler_agent = Agent(
        role="Admissions Propensity Modeler",
        goal="""Analyze candidate data against the ideal profile blueprint to score and rank 
        candidates, producing a final list of the top 10 most promising candidates with 
        detailed justifications for each score.""",
        backstory="""You are a sophisticated admissions propensity modeler with deep expertise 
        in candidate evaluation and scoring. You understand the nuances of graduate admissions 
        and excel at creating fair, comprehensive scoring models that identify the most 
        promising candidates while providing clear justifications for your assessments.""",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=True
    )
    logger.info("✅ Propensity Modeler Agent created")
    
    # Create Task 3: Evaluate Datasets
    logger.info("Creating Task 3: Evaluate Datasets...")
    evaluate_task = Task(
        description="""Evaluate the datasets found by Agent 2 and select the single best one.
        
        Look at the datasets from Agent 2's results.
        Select ONE dataset that would be best for finding educational leaders.
        Return the dataset slug (username/dataset-name format).
        
        Your response should be: "Selected dataset: username/dataset-name" """,
        agent=evaluator_agent,
        context=[search_task],
        expected_output="A single dataset slug"
    )
    logger.info("✅ Evaluate Task created")
    
    # Create Task 4: Ingest Data
    logger.info("Creating Task 4: Ingest Data...")
    ingest_task = Task(
        description="""Ingest and prepare data from the selected dataset.
        
        For now, return a summary message like:
        "Data ingestion would download dataset [dataset-slug] and prepare candidate profiles for analysis."
        
        (Actual download disabled for speed - this demonstrates the flow)""",
        agent=ingestion_agent,
        context=[evaluate_task],
        expected_output="A confirmation that data is ready for analysis"
    )
    logger.info("✅ Ingest Task created")
    
    # Create Task 5: Rank Candidates
    logger.info("Creating Task 5: Rank Candidates...")
    rank_task = Task(
        description="""Score and rank candidates based on the ideal profile.
        
        Consider the ideal profile from Agent 1 and rank candidates from the datasets.
        Return a numbered list of top 5 candidates with scores (0-100).
        
        Format:
        "Top 5 Candidates:
        1. Candidate name/ID - Score: 95/100 - [Brief reason]
        2. Candidate name/ID - Score: 90/100 - [Brief reason]
        etc..." """,
        agent=modeler_agent,
        context=[blueprint_task, ingest_task],
        expected_output="A ranked list of top 5 candidates with scores and reasons"
    )
    logger.info("✅ Rank Task created")
    
    # Create Crew
    logger.info("Creating Crew...")
    crew = Crew(
        agents=[trait_agent, scout_agent, evaluator_agent, ingestion_agent, modeler_agent],
        tasks=[blueprint_task, search_task, evaluate_task, ingest_task, rank_task],
        process=Process.sequential,
        verbose=True
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

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not set")
        sys.exit(1)
    
    test_real_agentic_pipeline()
