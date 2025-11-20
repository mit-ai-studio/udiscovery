#!/usr/bin/env python3
"""
UDiscovery Pipeline - Synthetic Dataset Orchestrator
This module orchestrates the pipeline using the synthetic candidate dataset instead of Kaggle.
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from crewai import Crew, Process

# Import agent and task creators from separate modules
from trait_inferrer import create_trait_agent, create_blueprint_task
from synthetic_pipeline import (
    load_synthetic_data,
    create_data_loader_agent,
    create_load_data_task
)
from propensity_modeler import create_prospection_agent, create_predict_probability_task

# Load environment variables
load_dotenv()

# Set up logging
log_filename = f"udiscovery_synthetic_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
    Run the UDiscovery pipeline with a custom university goal using synthetic dataset.
    This function is called by the frontend via demo_runner.py
    
    Args:
        university_goal: The university's program goal/prompt
        
    Returns:
        The final result from the pipeline execution
    """
    return execute_pipeline(university_goal)

def execute_pipeline(university_goal=None):
    """Execute the UDiscovery pipeline with a specific university goal using synthetic dataset"""
    
    if university_goal is None:
        # Default HGSE goal if not provided
        university_goal = """
    Our primary objective is to build a diverse and mission-driven cohort across all Harvard Graduate School of Education (HGSE) master's programs. We are not just looking for academics; we are looking for future **leaders, innovators, and changemakers** who want to have a systemic impact on the field of education.

    Ideal candidates often have **3-10 years of professional experience** and come from a wide range of backgrounds, including **K-12 teaching, school administration, non-profit management, education policy, and ed-tech**.

    We want to find individuals who demonstrate a deep commitment to **equity, social justice, and innovation**. Your task is to analyze candidate profiles for these signals. Look for candidates with leadership experience, initiative, and a desire to solve complex educational problems, such as 'program manager,' 'department head,' 'founder,' 'principal,' or active involvement in 'community engagement,' 'policy writing,' or 'curriculum development'.
    """
    
    logger.info("=" * 80)
    logger.info("🚀 UDiscovery Agentic Pipeline - Synthetic Dataset")
    logger.info("=" * 80)
    
    # Initialize LLM - CrewAI expects a string or specific format
    google_key = os.getenv("GOOGLE_API_KEY")
    # For CrewAI, we use the model string directly
    llm_model = "gemini-2.0-flash"
    os.environ["GEMINI_API_KEY"] = google_key
    
    # Load synthetic data first
    logger.info("Loading synthetic candidate dataset...")
    data_info = load_synthetic_data("dataset/synt_prospec.csv", num_rows=50)  # Load first 50 to reduce token usage
    if not data_info["success"]:
        logger.error(f"Failed to load dataset: {data_info.get('error', 'Unknown error')}")
        return None
    
    logger.info(f"✅ Loaded {data_info['total_rows']} total candidates (using {data_info['sample_size']} for analysis)")
    logger.info(f"Available fields: {', '.join(data_info['columns'][:10])}...")
    
    # Create Agent 1: Trait Inferrer
    logger.info("Creating Agent 1: Trait Inferrer...")
    trait_agent = create_trait_agent()
    logger.info("✅ Trait Inferrer Agent created")
    
    # Create Agent 2: Data Loader (replaces Kaggle Scout/Evaluator/Ingestion)
    logger.info("Creating Agent 2: Data Loader...")
    data_loader_agent = create_data_loader_agent()
    logger.info("✅ Data Loader Agent created")
    
    # Create Agent 3: Prospection Agent
    logger.info("Creating Agent 3: Prospection Agent...")
    prospection_agent = create_prospection_agent()
    logger.info("✅ Prospection Agent created")
    
    # Create Task 1: Create Blueprint
    logger.info("Creating Task 1: Create Blueprint...")
    blueprint_task = create_blueprint_task(trait_agent, university_goal)
    logger.info("✅ Blueprint Task created")
    
    # Create Task 2: Load Data (with actual data embedded)
    logger.info("Creating Task 2: Load Data...")
    load_task = create_load_data_task(data_loader_agent, data_info)
    logger.info("✅ Load Data Task created")
    
    # Create Task 3: Predict Application Probability
    logger.info("Creating Task 3: Predict Application Probability...")
    predict_task = create_predict_probability_task(prospection_agent, blueprint_task, load_task, use_synthetic_data=True)
    logger.info("✅ Predict Probability Task created")
    
    # Create Crew
    logger.info("Creating Crew...")
    crew = Crew(
        agents=[trait_agent, data_loader_agent, prospection_agent],
        tasks=[blueprint_task, load_task, predict_task],
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
    """Run the UDiscovery pipeline with default HGSE goal using synthetic dataset"""
    return execute_pipeline()

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not set")
        sys.exit(1)
    
    run_pipeline()

