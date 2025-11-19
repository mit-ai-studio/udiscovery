#!/usr/bin/env python3
"""
UDiscovery Pipeline - Main Orchestrator
This module orchestrates the complete pipeline by combining:
- Trait Inferrer (trait_inferrer.py)
- Kaggle Pipeline (kaggle_pipeline.py)
- Propensity Modeler (propensity_modeler.py)
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from crewai import Crew, Process

# Import agent and task creators from separate modules
from trait_inferrer import create_trait_agent, create_blueprint_task
from kaggle_pipeline import (
    create_scout_agent, create_evaluator_agent, create_ingestion_agent,
    create_search_task, create_evaluate_task, create_ingest_task
)
from propensity_modeler import create_modeler_agent, create_rank_task

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
    logger.info("🚀 UDiscovery Agentic Pipeline - CrewAI Agents")
    logger.info("=" * 80)
    
    # Initialize LLM - CrewAI expects a string or specific format
    google_key = os.getenv("GOOGLE_API_KEY")
    # For CrewAI, we use the model string directly
    llm_model = "gemini-2.0-flash"
    os.environ["GEMINI_API_KEY"] = google_key
    
    # Create Agent 1: Trait Inferrer
    logger.info("Creating Agent 1: Trait Inferrer...")
    trait_agent = create_trait_agent()
    logger.info("✅ Trait Inferrer Agent created")
    
    # Create Agent 2: Kaggle Scout
    logger.info("Creating Agent 2: Kaggle Scout...")
    scout_agent = create_scout_agent()
    logger.info("✅ Kaggle Scout Agent created")
    
    # Create Agent 3: Dataset Evaluator
    logger.info("Creating Agent 3: Dataset Evaluator...")
    evaluator_agent = create_evaluator_agent()
    logger.info("✅ Dataset Evaluator Agent created")
    
    # Create Agent 4: Data Ingestion
    logger.info("Creating Agent 4: Data Ingestion...")
    ingestion_agent = create_ingestion_agent()
    logger.info("✅ Data Ingestion Agent created")
    
    # Create Agent 5: Propensity Modeler
    logger.info("Creating Agent 5: Propensity Modeler...")
    modeler_agent = create_modeler_agent()
    logger.info("✅ Propensity Modeler Agent created")
    
    # Create Task 1: Create Blueprint
    logger.info("Creating Task 1: Create Blueprint...")
    blueprint_task = create_blueprint_task(trait_agent, university_goal)
    logger.info("✅ Blueprint Task created")
    
    # Create Task 2: Find Datasets
    logger.info("Creating Task 2: Find Datasets...")
    search_task = create_search_task(scout_agent, blueprint_task)
    logger.info("✅ Search Task created")
    
    # Create Task 3: Evaluate Datasets
    logger.info("Creating Task 3: Evaluate Datasets...")
    evaluate_task = create_evaluate_task(evaluator_agent, search_task)
    logger.info("✅ Evaluate Task created")
    
    # Create Task 4: Ingest Data
    logger.info("Creating Task 4: Ingest Data...")
    ingest_task = create_ingest_task(ingestion_agent, evaluate_task)
    logger.info("✅ Ingest Task created")
    
    # Create Task 5: Rank Candidates
    logger.info("Creating Task 5: Rank Candidates...")
    rank_task = create_rank_task(modeler_agent, blueprint_task, ingest_task)
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
