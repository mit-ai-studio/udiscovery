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

# Decision thresholds - based on probability of success only
THRESHOLDS = {
    "ADMIT": {"min_probability": 0.75},  # 75% or higher
    "WAITLIST": {"min_probability": 0.60},  # 60-74%
    "NOT_ADMITTED": {"min_probability": 0.40},  # 40-59%
    "NOT_ADMITTED_INELIGIBLE": {"min_probability": 0.0}  # Below 40%
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
        
        Return ONLY a valid JSON object with scores and a brief AI rationale explaining the scoring, no additional text.""",
        agent=create_data_standardization_agent(),
        expected_output="""A JSON object with six integer scores (1-5) for each rubric dimension and an AI rationale:
        {{
            "motivation_values": <integer 1-5>,
            "resilience": <integer 1-5>,
            "leadership": <integer 1-5>,
            "learning_orientation_fit": <integer 1-5>,
            "academic_readiness": <integer 1-5>,
            "life_context": <integer 1-5>,
            "ai_rationale": "<brief 2-3 sentence summary explaining the overall assessment and key strengths/concerns>"
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
        
        Calculations Required:
        1. Extract the six rubric scores (1-5 scale):
           - MV = Motivation & Values
           - RE = Resilience
           - LE = Leadership
           - LO = Learning Orientation/Fit
           - AC = Academic Readiness
           - LC = Life Context
        
        2. Calculate Probability of Success using the logistic regression formula:
           z = -7.0 + 0.7×MV + 0.6×RE + 0.5×LE + 0.65×LO + 0.45×AC - 0.7×LC
           probability_of_success = 1 / (1 + e^(-z))
           
           - Convert probability to percentage (0-100): probability_percentage = probability_of_success × 100
           - Example: if MV=4, RE=4, LE=3, LO=4, AC=4, LC=3
             then: z = -7.0 + 0.7×4 + 0.6×4 + 0.5×3 + 0.65×4 + 0.45×4 - 0.7×3
                   z = -7.0 + 2.8 + 2.4 + 1.5 + 2.6 + 1.8 - 2.1 = 2.0
             probability = 1 / (1 + e^(-2.0)) ≈ 0.88
             probability_percentage = 88%
           - Example with average scores (MV=3, RE=3, LE=3, LO=3, AC=3, LC=3):
             then: z = -7.0 + 0.7×3 + 0.6×3 + 0.5×3 + 0.65×3 + 0.45×3 - 0.7×3
                   z = -7.0 + 2.1 + 1.8 + 1.5 + 1.95 + 1.35 - 2.1 = 0.6
             probability = 1 / (1 + e^(-0.6)) ≈ 0.65
             probability_percentage = 65%
           - Example with good scores (MV=4, RE=4, LE=4, LO=4, AC=4, LC=4):
             then: z = -7.0 + 0.7×4 + 0.6×4 + 0.5×4 + 0.65×4 + 0.45×4 - 0.7×4
                   z = -7.0 + 2.8 + 2.4 + 2.0 + 2.6 + 1.8 - 2.8 = 1.8
             probability = 1 / (1 + e^(-1.8)) ≈ 0.86
             probability_percentage = 86%
           - Example with very good scores (MV=5, RE=4, LE=4, LO=5, AC=5, LC=4):
             then: z = -7.0 + 0.7×5 + 0.6×4 + 0.5×4 + 0.65×5 + 0.45×5 - 0.7×4
                   z = -7.0 + 3.5 + 2.4 + 2.0 + 3.25 + 2.25 - 2.8 = 3.6
             probability = 1 / (1 + e^(-3.6)) ≈ 0.97
             probability_percentage = 97%
           - Example with excellent scores (MV=5, RE=5, LE=5, LO=5, AC=5, LC=4):
             then: z = -7.0 + 0.7×5 + 0.6×5 + 0.5×5 + 0.65×5 + 0.45×5 - 0.7×4
                   z = -7.0 + 3.5 + 3.0 + 2.5 + 3.25 + 2.25 - 2.8 = 4.7
             probability = 1 / (1 + e^(-4.7)) ≈ 0.991
             probability_percentage = 99.1%
        
        IMPORTANT: 
        - Do NOT use GPA, teaching experience, or any other factors in the calculation
        - Only use the six rubric scores (MV, RE, LE, LO, AC, LC) in the formula above
        - Protected attributes (gender, age, country, etc.) must NEVER influence scoring
        
        Return ONLY a valid JSON object with:
        {{
            "probability_of_success": <float between 0 and 100>
        }}
        
        Note: probability_of_success should be a percentage (0-100), not a decimal (0-1).""",
        agent=create_scoring_agent(),
        expected_output="""A JSON object with probability of success as a percentage:
        {{
            "probability_of_success": <float 0-100>
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
        
        Decision Thresholds (based on probability of success only):
        - ADMIT: probability ≥ 0.75 (75% or higher)
        - WAITLIST: 0.60 ≤ probability < 0.75 (60-74%)
        - NOT_ADMITTED: 0.40 ≤ probability < 0.60 (40-59%)
        - NOT_ADMITTED_INELIGIBLE: probability < 0.40 (below 40%)
        
        Note: The probability of success incorporates weighted_rubric_score, normalized_gpa, teaching_experience, AND final_score, ensuring a comprehensive assessment.
        
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
            if 'probability_of_success' not in scoring_results:
                raise ValueError("Missing probability_of_success in scoring results")
            
            # Ensure probability is between 0 and 100
            probability = float(scoring_results.get('probability_of_success', 0))
            if probability < 0 or probability > 100:
                raise ValueError(f"Invalid probability_of_success: {probability} (must be 0-100)")
            
            # Extract additional information for frontend display
            # Location: extract state from city field - use city-to-state mapping
            city = applicant_data.get('city', '').strip() if applicant_data.get('city') else ''
            location = ''
            if city:
                import re
                # State abbreviation to full name mapping
                state_map = {
                    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
                    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
                    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
                    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
                    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
                    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
                    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
                    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
                    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
                    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
                    'DC': 'District of Columbia'
                }
                
                # City to state mapping (major US cities)
                city_to_state = {
                    'Denver': 'Colorado', 'New York': 'New York', 'Los Angeles': 'California', 'Chicago': 'Illinois',
                    'Houston': 'Texas', 'Phoenix': 'Arizona', 'Philadelphia': 'Pennsylvania', 'San Antonio': 'Texas',
                    'San Diego': 'California', 'Dallas': 'Texas', 'San Jose': 'California', 'Austin': 'Texas',
                    'Jacksonville': 'Florida', 'Fort Worth': 'Texas', 'Columbus': 'Ohio', 'Charlotte': 'North Carolina',
                    'San Francisco': 'California', 'Indianapolis': 'Indiana', 'Seattle': 'Washington', 'Boston': 'Massachusetts',
                    'Washington': 'District of Columbia', 'El Paso': 'Texas', 'Nashville': 'Tennessee', 'Detroit': 'Michigan',
                    'Oklahoma City': 'Oklahoma', 'Portland': 'Oregon', 'Las Vegas': 'Nevada', 'Memphis': 'Tennessee',
                    'Louisville': 'Kentucky', 'Baltimore': 'Maryland', 'Milwaukee': 'Wisconsin', 'Albuquerque': 'New Mexico',
                    'Tucson': 'Arizona', 'Fresno': 'California', 'Sacramento': 'California', 'Kansas City': 'Missouri',
                    'Mesa': 'Arizona', 'Atlanta': 'Georgia', 'Omaha': 'Nebraska', 'Colorado Springs': 'Colorado',
                    'Raleigh': 'North Carolina', 'Virginia Beach': 'Virginia', 'Miami': 'Florida', 'Oakland': 'California',
                    'Minneapolis': 'Minnesota', 'Tulsa': 'Oklahoma', 'Cleveland': 'Ohio', 'Wichita': 'Kansas',
                    'Arlington': 'Texas', 'New Orleans': 'Louisiana', 'Tampa': 'Florida', 'Honolulu': 'Hawaii',
                    'Anaheim': 'California', 'Santa Ana': 'California', 'St. Louis': 'Missouri', 'Riverside': 'California',
                    'Corpus Christi': 'Texas', 'Lexington': 'Kentucky', 'Pittsburgh': 'Pennsylvania', 'Anchorage': 'Alaska',
                    'Stockton': 'California', 'Cincinnati': 'Ohio', 'St. Paul': 'Minnesota', 'Toledo': 'Ohio',
                    'Greensboro': 'North Carolina', 'Newark': 'New Jersey', 'Plano': 'Texas', 'Henderson': 'Nevada',
                    'Lincoln': 'Nebraska', 'Buffalo': 'New York', 'Jersey City': 'New Jersey', 'Chula Vista': 'California',
                    'Fort Wayne': 'Indiana', 'Orlando': 'Florida', 'St. Petersburg': 'Florida', 'Chandler': 'Arizona',
                    'Laredo': 'Texas', 'Norfolk': 'Virginia', 'Durham': 'North Carolina', 'Madison': 'Wisconsin',
                    'Lubbock': 'Texas', 'Irvine': 'California', 'Winston-Salem': 'North Carolina', 'Glendale': 'Arizona',
                    'Garland': 'Texas', 'Hialeah': 'Florida', 'Reno': 'Nevada', 'Chesapeake': 'Virginia',
                    'Gilbert': 'Arizona', 'Baton Rouge': 'Louisiana', 'Irving': 'Texas', 'Scottsdale': 'Arizona',
                    'North Las Vegas': 'Nevada', 'Fremont': 'California', 'Boise': 'Idaho', 'Richmond': 'Virginia',
                    'San Bernardino': 'California', 'Birmingham': 'Alabama', 'Spokane': 'Washington', 'Rochester': 'New York',
                    'Des Moines': 'Iowa', 'Modesto': 'California', 'Fayetteville': 'North Carolina', 'Tacoma': 'Washington',
                    'Oxnard': 'California', 'Fontana': 'California', 'Columbus': 'Georgia', 'Montgomery': 'Alabama',
                    'Moreno Valley': 'California', 'Shreveport': 'Louisiana', 'Aurora': 'Illinois', 'Yonkers': 'New York',
                    'Akron': 'Ohio', 'Huntington Beach': 'California', 'Little Rock': 'Arkansas', 'Augusta': 'Georgia',
                    'Amarillo': 'Texas', 'Glendale': 'California', 'Mobile': 'Alabama', 'Grand Rapids': 'Michigan',
                    'Salt Lake City': 'Utah', 'Tallahassee': 'Florida', 'Huntsville': 'Alabama', 'Grand Prairie': 'Texas',
                    'Knoxville': 'Tennessee', 'Worcester': 'Massachusetts', 'Newport News': 'Virginia', 'Brownsville': 'Texas',
                    'Overland Park': 'Kansas', 'Santa Clarita': 'California', 'Providence': 'Rhode Island', 'Garden Grove': 'California',
                    'Chattanooga': 'Tennessee', 'Oceanside': 'California', 'Jackson': 'Mississippi', 'Fort Lauderdale': 'Florida',
                    'Santa Rosa': 'California', 'Rancho Cucamonga': 'California', 'Port St. Lucie': 'Florida', 'Tempe': 'Arizona',
                    'Ontario': 'California', 'Vancouver': 'Washington', 'Sioux Falls': 'South Dakota', 'Peoria': 'Arizona',
                    'Salem': 'Oregon', 'Elk Grove': 'California', 'Corona': 'California', 'Eugene': 'Oregon',
                    'Pembroke Pines': 'Florida', 'Valley Stream': 'New York', 'Lancaster': 'California', 'Salinas': 'California',
                    'Palmdale': 'California', 'Hayward': 'California', 'Frisco': 'Texas', 'Pasadena': 'Texas',
                    'Macon': 'Georgia', 'Alexandria': 'Virginia', 'Pomona': 'California', 'Lakewood': 'Colorado',
                    'Sunnyvale': 'California', 'Escondido': 'California', 'Kansas City': 'Kansas', 'Hollywood': 'Florida',
                    'Clarksville': 'Tennessee', 'Torrance': 'California', 'Rockford': 'Illinois', 'Joliet': 'Illinois',
                    'Paterson': 'New Jersey', 'Bridgeport': 'Connecticut', 'Naperville': 'Illinois', 'Savannah': 'Georgia',
                    'Mesquite': 'Texas', 'Syracuse': 'New York', 'Pasadena': 'California', 'Orange': 'California',
                    'Fullerton': 'California', 'Killeen': 'Texas', 'Dayton': 'Ohio', 'McAllen': 'Texas',
                    'Bellevue': 'Washington', 'Miramar': 'Florida', 'Hampton': 'Virginia', 'West Valley City': 'Utah',
                    'Warren': 'Michigan', 'Olathe': 'Kansas', 'Waco': 'Texas', 'Gainesville': 'Florida',
                    'Cedar Rapids': 'Iowa', 'Visalia': 'California', 'Coral Springs': 'Florida', 'Thousand Oaks': 'California',
                    'Elizabeth': 'New Jersey', 'Stamford': 'Connecticut', 'Concord': 'California', 'Kent': 'Washington',
                    'Lafayette': 'Louisiana', 'New Haven': 'Connecticut', 'Topeka': 'Kansas', 'Simi Valley': 'California',
                    'Santa Clara': 'California', 'Athens': 'Georgia', 'Hartford': 'Connecticut', 'Victorville': 'California',
                    'Abilene': 'Texas', 'Norman': 'Oklahoma', 'Vallejo': 'California', 'Berkeley': 'California',
                    'Round Rock': 'Texas', 'Ann Arbor': 'Michigan', 'Richmond': 'California', 'Everett': 'Washington',
                    'Evansville': 'Indiana', 'Odessa': 'Texas', 'Allentown': 'Pennsylvania', 'Fargo': 'North Dakota',
                    'Beaumont': 'Texas', 'Independence': 'Missouri', 'Surprise': 'Arizona', 'Santa Maria': 'California',
                    'El Monte': 'California', 'Cambridge': 'Massachusetts', 'Clearwater': 'Florida', 'Westminster': 'Colorado',
                    'Rochester': 'Minnesota', 'Waterbury': 'Connecticut', 'Provo': 'Utah', 'West Jordan': 'Utah',
                    'Murfreesboro': 'Tennessee', 'Gresham': 'Oregon', 'Fairfield': 'California', 'Lowell': 'Massachusetts',
                    'San Buenaventura': 'California', 'Pueblo': 'Colorado', 'High Point': 'North Carolina', 'West Covina': 'California',
                    'Richmond': 'Virginia', 'Murrieta': 'California', 'Carrollton': 'Texas', 'Midland': 'Texas',
                    'Charleston': 'South Carolina', 'Waco': 'Texas', 'Sterling Heights': 'Michigan', 'Denton': 'Texas',
                    'Palm Bay': 'Florida', 'Cedar Park': 'Texas', 'Kenosha': 'Wisconsin', 'Lakeland': 'Florida',
                    'Miami Gardens': 'Florida', 'Tyler': 'Texas', 'Lewisville': 'Texas', 'Burbank': 'California',
                    'Renton': 'Washington', 'Davenport': 'Iowa', 'South Bend': 'Indiana', 'Vista': 'California',
                    'Edinburg': 'Texas', 'Tuscaloosa': 'Alabama', 'Carmel': 'Indiana', 'Spokane Valley': 'Washington',
                    'San Mateo': 'California', 'Rialto': 'California', 'Compton': 'California', 'Mission Viejo': 'California',
                    'Boulder': 'Colorado', 'Daly City': 'California', 'Brockton': 'Massachusetts', 'Bellingham': 'Washington',
                    'Green Bay': 'Wisconsin', 'Boca Raton': 'Florida', 'Largo': 'Florida', 'Temecula': 'California',
                    'Meridian': 'Idaho', 'Erie': 'Pennsylvania', 'South Gate': 'California', 'Hillsboro': 'Oregon',
                    'Yuma': 'Arizona', 'Sandy Springs': 'Georgia', 'Federal Way': 'Washington', 'Sparks': 'Nevada',
                    'Santa Monica': 'California', 'Roswell': 'Georgia', 'Lynn': 'Massachusetts', 'Bend': 'Oregon',
                    'Downey': 'California', 'Sandy': 'Utah', 'Tracy': 'California', 'Bryan': 'Texas',
                    'Bremerton': 'Washington', 'Inglewood': 'California', 'Hemet': 'California', 'Nampa': 'Idaho',
                    'Fishers': 'Indiana', 'San Angelo': 'Texas', 'Lakewood': 'Washington', 'Menifee': 'California',
                    'Jurupa Valley': 'California', 'Racine': 'Wisconsin', 'Rio Rancho': 'New Mexico', 'Redding': 'California',
                    'Chico': 'California', 'Tuscaloosa': 'Alabama', 'Billings': 'Montana', 'West Palm Beach': 'Florida',
                    'Broken Arrow': 'Oklahoma', 'Avondale': 'Arizona', 'Layton': 'Utah', 'Miami Beach': 'Florida',
                    'Bellingham': 'Washington', 'Bend': 'Oregon', 'Boulder': 'Colorado', 'Bremerton': 'Washington',
                    'Brockton': 'Massachusetts', 'Bryan': 'Texas', 'Burbank': 'California', 'Cambridge': 'Massachusetts',
                    'Carmel': 'Indiana', 'Carrollton': 'Texas', 'Cedar Park': 'Texas', 'Cedar Rapids': 'Iowa',
                    'Chandler': 'Arizona', 'Charleston': 'South Carolina', 'Chattanooga': 'Tennessee', 'Chico': 'California',
                    'Chula Vista': 'California', 'Cincinnati': 'Ohio', 'Clearwater': 'Florida', 'Clarksville': 'Tennessee',
                    'Cleveland': 'Ohio', 'Colorado Springs': 'Colorado', 'Columbia': 'South Carolina', 'Columbus': 'Georgia',
                    'Compton': 'California', 'Concord': 'California', 'Coral Springs': 'Florida', 'Corona': 'California',
                    'Corpus Christi': 'Texas', 'Dallas': 'Texas', 'Daly City': 'California', 'Davenport': 'Iowa',
                    'Dayton': 'Ohio', 'Denton': 'Texas', 'Des Moines': 'Iowa', 'Detroit': 'Michigan',
                    'Downey': 'California', 'Durham': 'North Carolina', 'Edinburg': 'Texas', 'El Monte': 'California',
                    'El Paso': 'Texas', 'Elk Grove': 'California', 'Elizabeth': 'New Jersey', 'Erie': 'Pennsylvania',
                    'Escondido': 'California', 'Eugene': 'Oregon', 'Evansville': 'Indiana', 'Everett': 'Washington',
                    'Fairfield': 'California', 'Fargo': 'North Dakota', 'Fayetteville': 'North Carolina', 'Federal Way': 'Washington',
                    'Fishers': 'Indiana', 'Fontana': 'California', 'Fort Lauderdale': 'Florida', 'Fort Wayne': 'Indiana',
                    'Fort Worth': 'Texas', 'Fremont': 'California', 'Fresno': 'California', 'Frisco': 'Texas',
                    'Fullerton': 'California', 'Gainesville': 'Florida', 'Garden Grove': 'California', 'Garland': 'Texas',
                    'Gilbert': 'Arizona', 'Glendale': 'Arizona', 'Glendale': 'California', 'Grand Prairie': 'Texas',
                    'Grand Rapids': 'Michigan', 'Greensboro': 'North Carolina', 'Gresham': 'Oregon', 'Hampton': 'Virginia',
                    'Hartford': 'Connecticut', 'Hayward': 'California', 'Hemet': 'California', 'Henderson': 'Nevada',
                    'Hialeah': 'Florida', 'High Point': 'North Carolina', 'Hillsboro': 'Oregon', 'Hollywood': 'Florida',
                    'Honolulu': 'Hawaii', 'Houston': 'Texas', 'Huntington Beach': 'California', 'Huntsville': 'Alabama',
                    'Independence': 'Missouri', 'Indianapolis': 'Indiana', 'Inglewood': 'California', 'Irvine': 'California',
                    'Irving': 'Texas', 'Jackson': 'Mississippi', 'Jacksonville': 'Florida', 'Jersey City': 'New Jersey',
                    'Joliet': 'Illinois', 'Jurupa Valley': 'California', 'Kansas City': 'Kansas', 'Kansas City': 'Missouri',
                    'Kent': 'Washington', 'Killeen': 'Texas', 'Knoxville': 'Tennessee', 'Lafayette': 'Louisiana',
                    'Lakewood': 'Colorado', 'Lakewood': 'Washington', 'Lakeland': 'Florida', 'Lancaster': 'California',
                    'Laredo': 'Texas', 'Las Vegas': 'Nevada', 'Layton': 'Utah', 'Lewisville': 'Texas',
                    'Lexington': 'Kentucky', 'Lincoln': 'Nebraska', 'Little Rock': 'Arkansas', 'Long Beach': 'California',
                    'Los Angeles': 'California', 'Louisville': 'Kentucky', 'Lowell': 'Massachusetts', 'Lubbock': 'Texas',
                    'Lynn': 'Massachusetts', 'Macon': 'Georgia', 'Madison': 'Wisconsin', 'McAllen': 'Texas',
                    'Memphis': 'Tennessee', 'Menifee': 'California', 'Meridian': 'Idaho', 'Mesa': 'Arizona',
                    'Mesquite': 'Texas', 'Miami': 'Florida', 'Miami Beach': 'Florida', 'Miami Gardens': 'Florida',
                    'Midland': 'Texas', 'Milwaukee': 'Wisconsin', 'Minneapolis': 'Minnesota', 'Miramar': 'Florida',
                    'Mission Viejo': 'California', 'Mobile': 'Alabama', 'Modesto': 'California', 'Montgomery': 'Alabama',
                    'Moreno Valley': 'California', 'Murfreesboro': 'Tennessee', 'Murrieta': 'California', 'Nampa': 'Idaho',
                    'Naperville': 'Illinois', 'Nashville': 'Tennessee', 'New Haven': 'Connecticut', 'New Orleans': 'Louisiana',
                    'New York': 'New York', 'Newark': 'New Jersey', 'Newport News': 'Virginia', 'Norfolk': 'Virginia',
                    'Norman': 'Oklahoma', 'North Las Vegas': 'Nevada', 'Oakland': 'California', 'Oceanside': 'California',
                    'Odessa': 'Texas', 'Olathe': 'Kansas', 'Omaha': 'Nebraska', 'Ontario': 'California',
                    'Orange': 'California', 'Orlando': 'Florida', 'Overland Park': 'Kansas', 'Oxnard': 'California',
                    'Palm Bay': 'Florida', 'Palmdale': 'California', 'Pasadena': 'California', 'Pasadena': 'Texas',
                    'Paterson': 'New Jersey', 'Pembroke Pines': 'Florida', 'Peoria': 'Arizona', 'Philadelphia': 'Pennsylvania',
                    'Phoenix': 'Arizona', 'Pittsburgh': 'Pennsylvania', 'Plano': 'Texas', 'Pomona': 'California',
                    'Port St. Lucie': 'Florida', 'Portland': 'Oregon', 'Provo': 'Utah', 'Pueblo': 'Colorado',
                    'Racine': 'Wisconsin', 'Raleigh': 'North Carolina', 'Rancho Cucamonga': 'California', 'Reno': 'Nevada',
                    'Renton': 'Washington', 'Rialto': 'California', 'Richmond': 'California', 'Richmond': 'Virginia',
                    'Riverside': 'California', 'Rochester': 'Minnesota', 'Rochester': 'New York', 'Rockford': 'Illinois',
                    'Roswell': 'Georgia', 'Round Rock': 'Texas', 'Sacramento': 'California', 'Salem': 'Oregon',
                    'Salinas': 'California', 'Salt Lake City': 'Utah', 'San Angelo': 'Texas', 'San Antonio': 'Texas',
                    'San Bernardino': 'California', 'San Buenaventura': 'California', 'San Diego': 'California',
                    'San Francisco': 'California', 'San Jose': 'California', 'San Mateo': 'California', 'Santa Ana': 'California',
                    'Santa Clara': 'California', 'Santa Clarita': 'California', 'Santa Maria': 'California',
                    'Santa Monica': 'California', 'Santa Rosa': 'California', 'Savannah': 'Georgia', 'Scottsdale': 'Arizona',
                    'Seattle': 'Washington', 'Shreveport': 'Louisiana', 'Sioux Falls': 'South Dakota', 'South Bend': 'Indiana',
                    'South Gate': 'California', 'Spokane': 'Washington', 'Spokane Valley': 'Washington', 'Springfield': 'Missouri',
                    'St. Louis': 'Missouri', 'St. Paul': 'Minnesota', 'St. Petersburg': 'Florida', 'Stamford': 'Connecticut',
                    'Sterling Heights': 'Michigan', 'Stockton': 'California', 'Sunnyvale': 'California', 'Surprise': 'Arizona',
                    'Syracuse': 'New York', 'Tacoma': 'Washington', 'Tallahassee': 'Florida', 'Tampa': 'Florida',
                    'Temecula': 'California', 'Tempe': 'Arizona', 'Thousand Oaks': 'California', 'Topeka': 'Kansas',
                    'Torrance': 'California', 'Tracy': 'California', 'Tucson': 'Arizona', 'Tulsa': 'Oklahoma',
                    'Tuscaloosa': 'Alabama', 'Tyler': 'Texas', 'Vallejo': 'California', 'Valley Stream': 'New York',
                    'Vancouver': 'Washington', 'Victorville': 'California', 'Virginia Beach': 'Virginia', 'Visalia': 'California',
                    'Vista': 'California', 'Waco': 'Texas', 'Warren': 'Michigan', 'Washington': 'District of Columbia',
                    'Waterbury': 'Connecticut', 'West Covina': 'California', 'West Jordan': 'Utah', 'West Palm Beach': 'Florida',
                    'West Valley City': 'Utah', 'Westminster': 'Colorado', 'Wichita': 'Kansas', 'Winston-Salem': 'North Carolina',
                    'Worcester': 'Massachusetts', 'Yonkers': 'New York', 'Yuma': 'Arizona'
                }
                
                # Normalize city name (remove extra spaces, convert to title case for matching)
                city_normalized = ' '.join(city.split()).title()
                
                # First, try to find state abbreviation in city string
                state_abbr_patterns = [
                    r',\s*([A-Z]{2})\b',  # "City, ST"
                    r'\b([A-Z]{2})\s*$',  # "ST" at end
                    r'^\s*([A-Z]{2})\s*$'  # Just "ST"
                ]
                
                state_abbr = None
                for pattern in state_abbr_patterns:
                    match = re.search(pattern, city.upper())
                    if match:
                        potential_abbr = match.group(1)
                        if potential_abbr in state_map:
                            state_abbr = potential_abbr
                            break
                
                if state_abbr:
                    location = state_map[state_abbr]
                elif city_normalized in city_to_state:
                    # Use city-to-state mapping
                    location = city_to_state[city_normalized]
                else:
                    # Check if city contains a full state name (check longest names first)
                    state_names = ['New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 
                                  'North Dakota', 'Rhode Island', 'South Carolina', 'South Dakota', 'West Virginia',
                                  'District of Columbia', 'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 
                                  'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 
                                  'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 
                                  'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 
                                  'Nebraska', 'Nevada', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Tennessee', 
                                  'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'Wisconsin', 'Wyoming']
                    
                    # Sort by length (longest first) to match multi-word states correctly
                    state_names.sort(key=len, reverse=True)
                    for state in state_names:
                        if state in city:
                            location = state
                            break
            
            # GPA formatting
            gpa = applicant_data.get('gpa', None)
            grading_scale = applicant_data.get('grading_scale', None)
            gpa_display = None
            if gpa is not None:
                try:
                    gpa_float = float(gpa)
                    if grading_scale and float(grading_scale) == 10.0:
                        # Convert 10-point scale to 4-point scale for display
                        gpa_display = f"{gpa_float / 2.5:.2f}"
                    else:
                        gpa_display = f"{gpa_float:.2f}"
                except (ValueError, TypeError):
                    gpa_display = None
            
            # Extract GRE/test score if available
            gre_score = applicant_data.get('language_test_score', None)
            teaching_exp = applicant_data.get('teaching_experience_years', None)
            
            # Extract AI rationale and rubric scores from standardization result
            ai_rationale = rubric_scores.get('ai_rationale', '')
            
            # Return probability of success with additional display info
            result = {
                "application_id": application_id,
                "name": applicant_data.get('name', 'N/A'),
                "probability_of_success": probability,
                "location": location,
                "gpa": gpa_display,
                "gre_score": gre_score,
                "teaching_experience_years": teaching_exp,
                "rubric_scores": {
                    "motivation_values": rubric_scores.get('motivation_values'),
                    "resilience": rubric_scores.get('resilience'),
                    "leadership": rubric_scores.get('leadership'),
                    "learning_orientation_fit": rubric_scores.get('learning_orientation_fit'),
                    "academic_readiness": rubric_scores.get('academic_readiness'),
                    "life_context": rubric_scores.get('life_context')
                },
                "ai_rationale": ai_rationale
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

def execute_admission_pipeline(dataset_path: str = "dataset/synt_admission.csv", num_applications: int = None, batch_size: int = 50):
    """Execute the admission assessment pipeline with batch processing
    
    Args:
        dataset_path: Path to the admission dataset CSV
        num_applications: Maximum number of applications to process (None for all)
        batch_size: Number of applications to process per batch (default 50)
    """
    logger.info("=" * 80)
    logger.info("🚀 Admission Assessment Pipeline - Batch Processing")
    logger.info("=" * 80)
    
    # Load data
    df = load_admission_data(dataset_path, num_applications)
    total_applications = len(df)
    
    logger.info(f"✅ Loaded {total_applications} applications from dataset")
    logger.info(f"📦 Processing in batches of {batch_size} applications...")
    
    # Split into batches
    batches = []
    for i in range(0, total_applications, batch_size):
        batch_end = min(i + batch_size, total_applications)
        batches.append((i, batch_end))
    
    total_batches = len(batches)
    logger.info(f"✅ Created {total_batches} batches for processing")
    logger.info("=" * 80)
    logger.info(f"🔄 Processing {total_batches} batches...")
    logger.info("=" * 80)
    
    # Process each batch
    all_results = []
    
    for batch_num, (batch_start, batch_end) in enumerate(batches, 1):
        logger.info("")
        logger.info(f"📊 Processing Batch {batch_num}/{total_batches} (applications {batch_start + 1}-{batch_end})...")
        
        # Add delay between batches to avoid rate limits (except for first batch)
        if batch_num > 1:
            delay_seconds = 30  # 30 second delay between batches
            logger.info(f"⏳ Waiting {delay_seconds} seconds before processing next batch to avoid rate limits...")
            time.sleep(delay_seconds)
        
        # Process each application in this batch
        batch_results = []
        for idx in range(batch_start, batch_end):
            row = df.iloc[idx]
            applicant_data = row.to_dict()
            
            # Retry logic for individual applications
            max_retries = 3
            retry_delay = 10
            application_success = False
            
            for attempt in range(max_retries):
                try:
                    result = assess_application(applicant_data)
                    batch_results.append(result)
                    application_success = True
                    break
                except Exception as e:
                    error_str = str(e)
                    is_rate_limit = '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'rate limit' in error_str.lower()
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"⚠️ Rate limit hit on application {idx + 1}, attempt {attempt + 1}/{max_retries}. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Error processing application {idx + 1}: {e}")
                        if not is_rate_limit:
                            # For non-rate-limit errors, add error result and continue
                            batch_results.append({
                                "application_id": applicant_data.get('application_id', f'unknown_{idx}'),
                                "name": applicant_data.get('name', 'N/A'),
                                "error": str(e)
                            })
                            break
            
            # Small delay between applications within a batch
            if (idx - batch_start + 1) % 5 == 0:
                time.sleep(1)
        
        all_results.extend(batch_results)
        logger.info(f"✅ Batch {batch_num}/{total_batches} completed ({len(batch_results)} applications processed)")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 All batches processed successfully!")
    logger.info(f"✅ Processed {total_applications} applications across {total_batches} batches")
    logger.info("=" * 80)
    
    # Return combined results
    return {
        "total_applications": len(all_results),
        "results": all_results
    }

if __name__ == "__main__":
    # Test with a small number of applications
    result = execute_admission_pipeline(num_applications=5)
    print(json.dumps(result, indent=2))

