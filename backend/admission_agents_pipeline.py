#!/usr/bin/env python3
"""
UDiscovery Admission Pipeline - Admission Assessment System
This module orchestrates the admission assessment pipeline using the synthetic admission dataset.
Implements a 4-agent system: Data Standardization, Scoring, Decision, and Explanation Generation.
"""

import os
import sys
import json
import logging
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

# Load environment variables
load_dotenv()

# Set up logging
log_filename = f"udiscovery_admission_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stderr)  # Send logs to stderr to keep stdout clean for JSON
    ]
)

logger = logging.getLogger(__name__)

# Rubric dimensions and weights
RUBRIC_DIMENSIONS = [
    "Motivation & Values",
    "Resilience",
    "Leadership",
    "Learning Orientation/Fit",
    "Academic Readiness",
    "Life Context"
]

RUBRIC_WEIGHTS = {
    "Motivation & Values": 0.20,
    "Resilience": 0.15,
    "Leadership": 0.15,
    "Learning Orientation/Fit": 0.20,
    "Academic Readiness": 0.15,
    "Life Context": 0.15
}

# Decision thresholds
THRESHOLDS = {
    "ADMIT": {"min_final_score": 3.5, "min_probability": 0.70},
    "WAITLIST": {"min_final_score": 3.0, "min_probability": 0.60},
    "NOT_ADMITTED": {"min_final_score": 2.5, "min_probability": 0.50},
    "NOT_ADMITTED_INELIGIBLE": {"min_final_score": 0.0, "min_probability": 0.0}  # Special case
}

def load_admission_data(dataset_path: str = "dataset/synt_admission.csv", num_rows: int = None):
    """Load admission dataset"""
    try:
        # Get absolute path
        if not os.path.isabs(dataset_path):
            # Assume it's relative to the backend directory
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            dataset_path = os.path.join(backend_dir, "..", dataset_path)
            dataset_path = os.path.normpath(dataset_path)
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
        
        df = pd.read_csv(dataset_path, nrows=num_rows)
        logger.info(f"Loaded {len(df)} admission applications from {dataset_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading admission data: {e}")
        raise

def create_data_standardization_agent():
    """Create the data standardization agent that extracts structured rubric scores"""
    return Agent(
        role="Data Standardization Specialist",
        goal="Extract and standardize structured rubric scores (1-5 scale) from raw applicant materials",
        backstory="""You are an expert in educational assessment who specializes in extracting 
        structured evaluation data from unstructured applicant materials. You carefully read 
        essays, CVs, recommendations, and other materials to assign scores on a 1-5 scale for 
        each of the six rubric dimensions: Motivation & Values, Resilience, Leadership, 
        Learning Orientation/Fit, Academic Readiness, and Life Context. You are objective, 
        consistent, and never use protected attributes like gender, age, or race in your scoring.""",
        verbose=False,  # Disable verbose output to keep stdout clean
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash"  # Use stable model instead of experimental
    )

def create_scoring_agent():
    """Create the scoring agent that computes weighted scores and probabilities"""
    return Agent(
        role="Admissions Scoring Specialist",
        goal="Compute weighted rubric scores, probability of program success, and final admissions score",
        backstory="""You are a quantitative assessment expert who calculates weighted rubric scores 
        and uses logistic regression to predict program success. You combine rubric scores with 
        probability estimates to produce a final admissions score. You ensure all calculations are 
        accurate and follow the specified formulas.""",
        verbose=False,  # Disable verbose output to keep stdout clean
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash"  # Use stable model instead of experimental
    )

def create_decision_agent():
    """Create the decision agent that assigns admission outcomes"""
    return Agent(
        role="Admissions Decision Specialist",
        goal="Assign one of four outcomes (ADMIT, WAITLIST, NOT_ADMITTED, NOT_ADMITTED_INELIGIBLE) based on thresholds",
        backstory="""You are an admissions officer who makes consistent, fair decisions based on 
        clear thresholds. You classify applicants using fixed criteria and never make exceptions 
        or use protected attributes. You identify strengths (all rubric dimensions ≥4), growth 
        areas (all ≤2), and risk bands based on probability of success.""",
        verbose=False,  # Disable verbose output to keep stdout clean
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash"  # Use stable model instead of experimental
    )

def create_explanation_agent():
    """Create the explanation generation agent"""
    return Agent(
        role="Admissions Explanation Writer",
        goal="Generate concise, human-readable justifications for admission decisions",
        backstory="""You are a clear and empathetic communicator who writes explanations for 
        admission decisions. You use templates for each decision outcome and incorporate 
        computed strengths, growth areas, and risk bands. Your explanations are honest, 
        constructive, and help applicants understand the decision.""",
        verbose=False,  # Disable verbose output to keep stdout clean
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash"  # Use stable model instead of experimental
    )

def create_standardization_task(applicant_data: dict):
    """Create task for data standardization agent"""
    applicant_text = f"""
    Application ID: {applicant_data.get('application_id', 'N/A')}
    Name: {applicant_data.get('name', 'N/A')}
    
    Essays:
    - Mission & Values: {applicant_data.get('essays_mission_values', 'N/A')}
    - Resilience: {applicant_data.get('essays_resilience', 'N/A')}
    - Leadership: {applicant_data.get('essays_leadership', 'N/A')}
    - Learning Orientation: {applicant_data.get('essays_learning_orientation', 'N/A')}
    
    CV: {applicant_data.get('cv', 'N/A')}
    
    Recommendations: {applicant_data.get('recommendation_forms', 'N/A')}
    
    Academic Info:
    - GPA: {applicant_data.get('gpa', 'N/A')} (Scale: {applicant_data.get('grading_scale', 'N/A')})
    - Highest Degree: {applicant_data.get('highest_degree', 'N/A')}
    - Field of Study: {applicant_data.get('field_of_study', 'N/A')}
    - Teaching Experience: {applicant_data.get('teaching_experience_years', 'N/A')} years
    
    Life Context:
    - Work Hours/Week: {applicant_data.get('hours_work_per_week', 'N/A')}
    - Study Hours Available/Week: {applicant_data.get('study_hours_available_per_week', 'N/A')}
    - Care Responsibilities: {applicant_data.get('care_responsibilities', 'None')}
    - Financial Plan: {applicant_data.get('financial_plan', 'N/A')}
    """
    
    return Task(
        description=f"""Extract and standardize rubric scores from the following applicant materials.
        
        {applicant_text}
        
        For each of the six rubric dimensions, assign a score from 1 to 5:
        1. Motivation & Values - Assess alignment with program mission and educational values
        2. Resilience - Evaluate ability to handle challenges and adapt
        3. Leadership - Assess leadership experience and potential
        4. Learning Orientation/Fit - Evaluate learning style and program fit
        5. Academic Readiness - Assess academic preparation (GPA, degree, coursework)
        6. Life Context - Evaluate life circumstances (work hours, study time, responsibilities, financial plan)
        
        Scoring Guidelines:
        - 5: Exceptional evidence, clearly exceeds expectations
        - 4: Strong evidence, meets expectations well
        - 3: Adequate evidence, meets basic expectations
        - 2: Limited evidence, below expectations
        - 1: Insufficient evidence, well below expectations
        
        IMPORTANT: 
        - Base scores ONLY on the provided materials
        - Do NOT use protected attributes (gender, age, race, etc.)
        - Be objective and consistent
        - Return scores as a JSON object with keys: motivation_values, resilience, leadership, 
          learning_orientation_fit, academic_readiness, life_context
        - Each score must be an integer between 1 and 5
        
        Return ONLY a valid JSON object, no additional text.""",
        agent=create_data_standardization_agent(),
        expected_output="""A JSON object with six integer scores (1-5) for each rubric dimension:
        {{
            "motivation_values": <integer 1-5>,
            "resilience": <integer 1-5>,
            "leadership": <integer 1-5>,
            "learning_orientation_fit": <integer 1-5>,
            "academic_readiness": <integer 1-5>,
            "life_context": <integer 1-5>
        }}"""
    )

def create_scoring_task(rubric_scores: dict, applicant_data: dict):
    """Create task for scoring agent"""
    return Task(
        description=f"""Compute weighted rubric score, probability of success, and final admissions score.
        
        Rubric Scores (1-5 scale):
        - Motivation & Values: {rubric_scores.get('motivation_values', 'N/A')}
        - Resilience: {rubric_scores.get('resilience', 'N/A')}
        - Leadership: {rubric_scores.get('leadership', 'N/A')}
        - Learning Orientation/Fit: {rubric_scores.get('learning_orientation_fit', 'N/A')}
        - Academic Readiness: {rubric_scores.get('academic_readiness', 'N/A')}
        - Life Context: {rubric_scores.get('life_context', 'N/A')}
        
        Weights:
        - Motivation & Values: 0.20
        - Resilience: 0.15
        - Leadership: 0.15
        - Learning Orientation/Fit: 0.20
        - Academic Readiness: 0.15
        - Life Context: 0.15
        
        Additional Context:
        - GPA: {applicant_data.get('gpa', 'N/A')} (Scale: {applicant_data.get('grading_scale', 'N/A')})
        - Teaching Experience: {applicant_data.get('teaching_experience_years', 'N/A')} years
        - Study Hours Available: {applicant_data.get('study_hours_available_per_week', 'N/A')} hours/week
        
        Calculations Required:
        1. Weighted Rubric Score = Σ(score × weight) for all six dimensions
        2. Probability of Success = 1 / (1 + e^(-(-2.5 + 0.8 × weighted_rubric_score + 0.3 × normalized_gpa + 0.2 × min(teaching_experience_years, 10))))
           - Normalize GPA to 0-1 scale: if grading_scale is 10, divide gpa by 10; if grading_scale is 4, divide gpa by 4
           - Cap teaching_experience_years at 10 for the calculation
           - Example: if weighted_rubric_score = 3.5, normalized_gpa = 0.85, teaching_experience = 5 years
             then: z = -2.5 + 0.8×3.5 + 0.3×0.85 + 0.2×5 = -2.5 + 2.8 + 0.255 + 1.0 = 1.555
             probability = 1 / (1 + e^(-1.555)) = 1 / (1 + 0.211) ≈ 0.826
        3. Final Score = 0.6 × weighted_rubric_score + 0.4 × probability_of_success
        
        Return ONLY a valid JSON object with:
        {{
            "weighted_rubric_score": <float>,
            "probability_of_success": <float between 0 and 1>,
            "final_score": <float>
        }}""",
        agent=create_scoring_agent(),
        expected_output="""A JSON object with three float values:
        {{
            "weighted_rubric_score": <float>,
            "probability_of_success": <float 0-1>,
            "final_score": <float>
        }}"""
    )

def create_decision_task(rubric_scores: dict, scoring_results: dict):
    """Create task for decision agent"""
    return Task(
        description=f"""Assign an admission decision based on thresholds and identify strengths/growth areas.
        
        Rubric Scores:
        - Motivation & Values: {rubric_scores.get('motivation_values', 'N/A')}
        - Resilience: {rubric_scores.get('resilience', 'N/A')}
        - Leadership: {rubric_scores.get('leadership', 'N/A')}
        - Learning Orientation/Fit: {rubric_scores.get('learning_orientation_fit', 'N/A')}
        - Academic Readiness: {rubric_scores.get('academic_readiness', 'N/A')}
        - Life Context: {rubric_scores.get('life_context', 'N/A')}
        
        Scoring Results:
        - Final Score: {scoring_results.get('final_score', 'N/A')}
        - Probability of Success: {scoring_results.get('probability_of_success', 'N/A')}
        
        Decision Thresholds:
        - ADMIT: final_score ≥ 3.5 AND probability ≥ 0.70
        - WAITLIST: final_score ≥ 3.0 AND probability ≥ 0.60 (but doesn't meet ADMIT criteria)
        - NOT_ADMITTED: final_score ≥ 2.5 AND probability ≥ 0.50 (but doesn't meet WAITLIST criteria)
        - NOT_ADMITTED_INELIGIBLE: final_score < 2.5 OR probability < 0.50
        
        Additional Classifications:
        - Strengths: All rubric dimensions where score ≥ 4
        - Growth Areas: All rubric dimensions where score ≤ 2
        - Risk Band: 
          * Low Risk: probability ≥ 0.75
          * Medium Risk: 0.60 ≤ probability < 0.75
          * High Risk: probability < 0.60
        
        Return ONLY a valid JSON object with:
        {{
            "decision": "<ADMIT|WAITLIST|NOT_ADMITTED|NOT_ADMITTED_INELIGIBLE>",
            "strengths": ["<list of dimension names with score ≥4>"],
            "growth_areas": ["<list of dimension names with score ≤2>"],
            "risk_band": "<Low Risk|Medium Risk|High Risk>"
        }}""",
        agent=create_decision_agent(),
        expected_output="""A JSON object with decision, strengths, growth areas, and risk band:
        {{
            "decision": "<ADMIT|WAITLIST|NOT_ADMITTED|NOT_ADMITTED_INELIGIBLE>",
            "strengths": ["<dimension names>"],
            "growth_areas": ["<dimension names>"],
            "risk_band": "<Low Risk|Medium Risk|High Risk>"
        }}"""
    )

def create_explanation_task(applicant_data: dict, rubric_scores: dict, scoring_results: dict, decision_results: dict):
    """Create task for explanation generation agent"""
    return Task(
        description=f"""Generate a concise, human-readable explanation for the admission decision.
        
        Applicant: {applicant_data.get('name', 'N/A')} ({applicant_data.get('application_id', 'N/A')})
        
        Decision: {decision_results.get('decision', 'N/A')}
        
        Rubric Scores:
        - Motivation & Values: {rubric_scores.get('motivation_values', 'N/A')}/5
        - Resilience: {rubric_scores.get('resilience', 'N/A')}/5
        - Leadership: {rubric_scores.get('leadership', 'N/A')}/5
        - Learning Orientation/Fit: {rubric_scores.get('learning_orientation_fit', 'N/A')}/5
        - Academic Readiness: {rubric_scores.get('academic_readiness', 'N/A')}/5
        - Life Context: {rubric_scores.get('life_context', 'N/A')}/5
        
        Final Score: {scoring_results.get('final_score', 'N/A')}
        Probability of Success: {scoring_results.get('probability_of_success', 'N/A')}
        
        Strengths: {', '.join(decision_results.get('strengths', []))}
        Growth Areas: {', '.join(decision_results.get('growth_areas', []))}
        Risk Band: {decision_results.get('risk_band', 'N/A')}
        
        Use the following template based on the decision:
        
        ADMIT Template:
        "We are pleased to offer you admission to the program. Your application demonstrates 
        strong performance across multiple dimensions, particularly in [strengths]. Your 
        [probability] probability of success and [risk_band] risk profile indicate strong 
        readiness for the program. We look forward to your contributions."
        
        WAITLIST Template:
        "We have placed you on our waitlist. While your application shows promise, particularly 
        in [strengths], there are areas for growth in [growth_areas]. Your [probability] 
        probability of success and [risk_band] risk profile suggest potential, but we need 
        to see how the full applicant pool shapes up. We will notify you of any changes."
        
        NOT_ADMITTED Template:
        "After careful review, we are unable to offer you admission at this time. While you 
        show strengths in [strengths if any], there are significant areas for growth in 
        [growth_areas]. Your [probability] probability of success and [risk_band] risk profile 
        indicate that additional preparation would strengthen a future application."
        
        NOT_ADMITTED_INELIGIBLE Template:
        "We are unable to offer you admission as your application does not meet the minimum 
        eligibility requirements. Your [probability] probability of success and [risk_band] 
        risk profile indicate that significant additional preparation is needed. We encourage 
        you to strengthen your application in [growth_areas] before reapplying."
        
        Fill in the template with the actual values. Be specific, honest, and constructive.
        Keep the explanation to 2-3 sentences.
        
        Return ONLY the explanation text, no JSON wrapper.""",
        agent=create_explanation_agent(),
        expected_output="A concise 2-3 sentence explanation of the admission decision"
    )

def parse_json_output(output: str):
    """Parse JSON from agent output, handling markdown code blocks"""
    output = output.strip()
    # Remove markdown code blocks if present
    if output.startswith("```json"):
        output = output[7:]
    elif output.startswith("```"):
        output = output[3:]
    if output.endswith("```"):
        output = output[:-3]
    output = output.strip()
    
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.error(f"Output was: {output[:500]}")
        # Try to extract JSON from the text
        import re
        json_match = re.search(r'\{[^{}]*\}', output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        raise

def assess_application(applicant_data: dict, max_retries: int = 3):
    """Assess a single application through the full pipeline"""
    application_id = applicant_data.get('application_id', 'N/A')
    
    for attempt in range(max_retries):
        try:
            # Step 1: Data Standardization
            logger.info(f"Assessing application {application_id} (attempt {attempt + 1})")
            standardization_task = create_standardization_task(applicant_data)
            standardization_crew = Crew(
                agents=[create_data_standardization_agent()],
                tasks=[standardization_task],
                process=Process.sequential,
                verbose=False  # Disable verbose output to keep stdout clean
            )
            standardization_result = standardization_crew.kickoff()
            rubric_scores = parse_json_output(str(standardization_result))
            logger.info(f"Rubric scores: {rubric_scores}")
            
            # Validate rubric scores
            required_keys = ['motivation_values', 'resilience', 'leadership', 
                           'learning_orientation_fit', 'academic_readiness', 'life_context']
            for key in required_keys:
                if key not in rubric_scores:
                    raise ValueError(f"Missing rubric score: {key}")
                if not (1 <= rubric_scores[key] <= 5):
                    raise ValueError(f"Invalid rubric score for {key}: {rubric_scores[key]} (must be 1-5)")
            
            # Step 2: Scoring
            scoring_task = create_scoring_task(rubric_scores, applicant_data)
            scoring_crew = Crew(
                agents=[create_scoring_agent()],
                tasks=[scoring_task],
                process=Process.sequential,
                verbose=False  # Disable verbose output to keep stdout clean
            )
            scoring_result = scoring_crew.kickoff()
            scoring_results = parse_json_output(str(scoring_result))
            logger.info(f"Scoring results: {scoring_results}")
            
            # Validate scoring results
            required_scoring_keys = ['weighted_rubric_score', 'probability_of_success', 'final_score']
            for key in required_scoring_keys:
                if key not in scoring_results:
                    raise ValueError(f"Missing scoring result: {key}")
            
            # Step 3: Decision
            decision_task = create_decision_task(rubric_scores, scoring_results)
            decision_crew = Crew(
                agents=[create_decision_agent()],
                tasks=[decision_task],
                process=Process.sequential,
                verbose=False  # Disable verbose output to keep stdout clean
            )
            decision_result = decision_crew.kickoff()
            decision_results = parse_json_output(str(decision_result))
            logger.info(f"Decision results: {decision_results}")
            
            # Validate decision results
            if 'decision' not in decision_results:
                raise ValueError("Missing decision in decision results")
            valid_decisions = ['ADMIT', 'WAITLIST', 'NOT_ADMITTED', 'NOT_ADMITTED_INELIGIBLE']
            if decision_results['decision'] not in valid_decisions:
                raise ValueError(f"Invalid decision: {decision_results['decision']}")
            
            # Step 4: Explanation
            explanation_task = create_explanation_task(applicant_data, rubric_scores, scoring_results, decision_results)
            explanation_crew = Crew(
                agents=[create_explanation_agent()],
                tasks=[explanation_task],
                process=Process.sequential,
                verbose=False  # Disable verbose output to keep stdout clean
            )
            explanation_result = explanation_crew.kickoff()
            explanation = str(explanation_result).strip()
            # Remove markdown code blocks if present
            if explanation.startswith("```"):
                explanation = explanation.split("```")[1] if len(explanation.split("```")) > 1 else explanation
                explanation = explanation.strip()
            logger.info(f"Explanation: {explanation}")
            
            # Combine all results
            result = {
                "application_id": application_id,
                "name": applicant_data.get('name', 'N/A'),
                "rubric_scores": rubric_scores,
                "weighted_rubric_score": scoring_results.get('weighted_rubric_score'),
                "probability_of_success": scoring_results.get('probability_of_success'),
                "final_score": scoring_results.get('final_score'),
                "decision": decision_results.get('decision'),
                "strengths": decision_results.get('strengths', []),
                "growth_areas": decision_results.get('growth_areas', []),
                "risk_band": decision_results.get('risk_band'),
                "explanation": explanation
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error assessing application {application_id} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                import traceback
                logger.error(traceback.format_exc())
                return {
                    "application_id": application_id,
                    "name": applicant_data.get('name', 'N/A'),
                    "error": str(e)
                }
            # Wait before retry with exponential backoff
            time.sleep(2 ** attempt)

def execute_admission_pipeline(dataset_path: str = "dataset/synt_admission.csv", num_applications: int = None):
    """Execute the admission assessment pipeline"""
    logger.info("Starting admission assessment pipeline")
    
    # Load data
    df = load_admission_data(dataset_path, num_applications)
    
    # Process each application
    results = []
    for idx, row in df.iterrows():
        applicant_data = row.to_dict()
        result = assess_application(applicant_data)
        results.append(result)
        
        # Add delay to avoid rate limits
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} applications")
            time.sleep(2)
    
    logger.info(f"Completed assessment of {len(results)} applications")
    
    # Return combined results
    return {
        "total_applications": len(results),
        "results": results
    }

if __name__ == "__main__":
    # Test with a small number of applications
    result = execute_admission_pipeline(num_applications=5)
    print(json.dumps(result, indent=2))

