#!/usr/bin/env python3
"""
UDiscovery Pipeline - Synthetic Dataset Orchestrator
This module orchestrates the pipeline using the synthetic candidate dataset instead of Kaggle.
"""

import os
import sys
import json
import logging
import time
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

def run_pipeline_with_goal(university_goal: str, batch_size: int = 500, max_candidates: int = None):
    """
    Run the UDiscovery pipeline with a custom university goal using synthetic dataset.
    This function is called by the frontend via demo_runner.py
    
    Args:
        university_goal: The university's program goal/prompt
        batch_size: Number of candidates to process per batch (default 500, reduce to 250 if hitting rate limits)
        max_candidates: Maximum number of candidates to process (None for all, set to 1000 for testing)
        
    Returns:
        The final result from the pipeline execution (combined from all batches)
    """
    # For production, limit to 1000 candidates to avoid rate limits
    # Remove this line to process all 5000 candidates
    if max_candidates is None:
        max_candidates = 1000  # Process 1000 candidates by default to avoid rate limits
    
    return execute_pipeline(university_goal, batch_size=batch_size, max_candidates=max_candidates)

def split_data_into_batches(data_info: dict, batch_size: int = 500):
    """Split the full dataset into batches for processing"""
    all_data = json.loads(data_info['data'])
    total_candidates = len(all_data)
    batches = []
    
    for i in range(0, total_candidates, batch_size):
        batch_data = all_data[i:i + batch_size]
        batch_json = json.dumps(batch_data)
        
        batch_info = {
            'success': True,
            'data': batch_json,
            'columns': data_info['columns'],
            'total_rows': data_info['total_rows'],  # Keep original total for reference
            'sample_size': len(batch_data),
            'batch_start': i + 1,
            'batch_end': min(i + batch_size, total_candidates),
            'batch_number': (i // batch_size) + 1,
            'total_batches': (total_candidates + batch_size - 1) // batch_size
        }
        batches.append(batch_info)
    
    return batches

def execute_pipeline(university_goal=None, batch_size: int = 500, max_candidates: int = None):
    """Execute the UDiscovery pipeline with a specific university goal using synthetic dataset.
    Processes all candidates in batches to avoid token limits.
    
    Args:
        university_goal: The university's program goal/prompt
        batch_size: Number of candidates to process per batch (default 500)
        max_candidates: Maximum number of candidates to process (None for all)
    """
    
    if university_goal is None:
        # Default HGSE goal if not provided
        university_goal = """
    Our primary objective is to build a diverse and mission-driven cohort across all Harvard Graduate School of Education (HGSE) master's programs. We are not just looking for academics; we are looking for future **leaders, innovators, and changemakers** who want to have a systemic impact on the field of education.

    Ideal candidates often have **3-10 years of professional experience** and come from a wide range of backgrounds, including **K-12 teaching, school administration, non-profit management, education policy, and ed-tech**.

    We want to find individuals who demonstrate a deep commitment to **equity, social justice, and innovation**. Your task is to analyze candidate profiles for these signals. Look for candidates with leadership experience, initiative, and a desire to solve complex educational problems, such as 'program manager,' 'department head,' 'founder,' 'principal,' or active involvement in 'community engagement,' 'policy writing,' or 'curriculum development'.
    """
    
    logger.info("=" * 80)
    logger.info("🚀 UDiscovery Agentic Pipeline - Synthetic Dataset (Batch Processing)")
    logger.info("=" * 80)
    
    # Initialize LLM - CrewAI expects a string or specific format
    google_key = os.getenv("GOOGLE_API_KEY")
    # For CrewAI, we use the model string directly
    llm_model = "gemini-2.0-flash"
    os.environ["GEMINI_API_KEY"] = google_key
    
    # Load synthetic data first
    logger.info("Loading synthetic candidate dataset...")
    num_rows_to_load = max_candidates if max_candidates else None
    full_data_info = load_synthetic_data("dataset/synt_prospect_5k.csv", num_rows=num_rows_to_load)
    if not full_data_info["success"]:
        logger.error(f"Failed to load dataset: {full_data_info.get('error', 'Unknown error')}")
        return None
    
    total_candidates = full_data_info['total_rows']
    candidates_to_process = full_data_info['sample_size']
    logger.info(f"✅ Loaded {total_candidates} total candidates in dataset")
    if max_candidates:
        logger.info(f"📊 Processing {candidates_to_process} candidates (limited for testing)")
    else:
        logger.info(f"📊 Processing all {candidates_to_process} candidates")
    logger.info(f"Available fields: {', '.join(full_data_info['columns'][:10])}...")
    
    # Split into batches
    logger.info(f"📦 Splitting dataset into batches of {batch_size} candidates...")
    batches = split_data_into_batches(full_data_info, batch_size)
    total_batches = len(batches)
    logger.info(f"✅ Created {total_batches} batches for processing")
    
    # Process each batch (each batch runs the full pipeline: blueprint + data load + prediction)
    logger.info("=" * 80)
    logger.info(f"🔄 Processing {total_batches} batches...")
    logger.info("=" * 80)
    
    all_results = []
    
    for batch_num, batch_info in enumerate(batches, 1):
        logger.info("")
        logger.info(f"📊 Processing Batch {batch_num}/{total_batches} (candidates {batch_info['batch_start']}-{batch_info['batch_end']})...")
        
        # Add delay between batches to avoid rate limits (except for first batch)
        if batch_num > 1:
            delay_seconds = 30  # 30 second delay between batches to avoid rate limits
            logger.info(f"⏳ Waiting {delay_seconds} seconds before processing next batch to avoid rate limits...")
            time.sleep(delay_seconds)
        
        # Create all agents for this batch
        trait_agent = create_trait_agent()
        data_loader_agent = create_data_loader_agent()
        prospection_agent = create_prospection_agent()
        
        # Create all tasks for this batch (full pipeline)
        blueprint_task = create_blueprint_task(trait_agent, university_goal)
        load_task = create_load_data_task(data_loader_agent, batch_info)
        predict_task = create_predict_probability_task(
            prospection_agent, blueprint_task, load_task, use_synthetic_data=True
        )
        
        # Create crew for this batch (full pipeline)
        batch_crew = Crew(
            agents=[trait_agent, data_loader_agent, prospection_agent],
            tasks=[blueprint_task, load_task, predict_task],
            process=Process.sequential,
            verbose=False
        )
        
        # Retry logic for rate limits
        max_retries = 3
        retry_delay = 30  # 30 seconds for rate limit errors
        batch_success = False
        
        for attempt in range(max_retries):
            try:
                batch_result = batch_crew.kickoff()
                
                # Extract result text - we only want the final prediction results, not the blueprint
                if hasattr(batch_result, 'raw'):
                    batch_text = batch_result.raw
                elif hasattr(batch_result, 'content'):
                    batch_text = batch_result.content
                else:
                    batch_text = str(batch_result)
                
                # Extract only the candidate predictions part (skip blueprint section if present)
                # The prospection agent's output should contain the candidates
                all_results.append(batch_text)
                logger.info(f"✅ Batch {batch_num}/{total_batches} completed successfully")
                batch_success = True
                break
                
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                is_rate_limit = '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'rate limit' in error_str.lower()
                
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)  # Exponential backoff
                    logger.warning(f"⚠️ Rate limit hit on batch {batch_num}, attempt {attempt + 1}/{max_retries}. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Error processing batch {batch_num}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    if not is_rate_limit:
                        # For non-rate-limit errors, skip this batch
                        break
        
        if not batch_success:
            logger.warning(f"⚠️ Skipping batch {batch_num} after {max_retries} attempts")
            continue
    
    # Combine all results
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔗 Combining results from all batches...")
    logger.info("=" * 80)
    
    if not all_results:
        logger.error("❌ No batches were processed successfully")
        return None
    
    # Combine all batch results into a single output
    # Add a header indicating this is a combined result from multiple batches
    successful_batches = len(all_results)
    header = f"Candidates for Harvard Graduate School of Education:\n(Processed {total_candidates} candidates across {successful_batches} batches)\n\n"
    combined_result = header + "\n\n".join(all_results)
    
    # Create a result object that mimics CrewAI's result format
    class CombinedResult:
        def __init__(self, content):
            self.content = content
            self.raw = content
        
        def __str__(self):
            return self.content
    
    final_result = CombinedResult(combined_result)
    
    logger.info("=" * 80)
    logger.info("🎉 All batches processed successfully!")
    logger.info(f"✅ Processed {total_candidates} candidates across {total_batches} batches")
    logger.info("=" * 80)
    
    return final_result

def run_pipeline():
    """Run the UDiscovery pipeline with default HGSE goal using synthetic dataset"""
    return execute_pipeline()

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not set")
        sys.exit(1)
    
    run_pipeline()

