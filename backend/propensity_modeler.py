#!/usr/bin/env python3
"""
Prospection Data Model Agent Module
Contains the Graduate Program Application Probability Modeler agent and prediction task.
"""

import json
from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel

# Tool for logistic regression modeling
class LogisticModelInput(BaseModel):
    candidate_data: dict
    program_attributes: dict
    historical_data: list = None

class LogisticModelTool(BaseTool):
    name: str = "logistic_model_tool"
    description: str = """Provides logistic regression utilities. Accepts structured candidate and program data and outputs fitted coefficients and predicted probability. If training data is missing, returns an informative message."""
    args_schema: type[BaseModel] = LogisticModelInput
    
    def _run(self, candidate_data: dict, program_attributes: dict, historical_data: list = None) -> str:
        """Execute logistic regression modeling"""
        try:
            # If historical data is available, we could fit a model
            # For now, return a message indicating theoretical approach
            if historical_data is None or len(historical_data) == 0:
                return json.dumps({
                    "status": "no_historical_data",
                    "message": "No historical training data available. Using theoretical propensity modeling.",
                    "approach": "theoretical"
                })
            
            # If historical data exists, would fit logistic regression here
            # For now, return theoretical approach
            return json.dumps({
                "status": "theoretical",
                "message": "Using theoretical propensity modeling based on candidate and program attributes.",
                "approach": "theoretical"
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

# Tool for data cleaning
class DataCleaningInput(BaseModel):
    candidate_data: dict
    program_attributes: dict

class DataCleaningTool(BaseTool):
    name: str = "data_cleaning_tool"
    description: str = "Cleans and encodes candidate and program attributes. Handles missing values and categorical encoding."
    args_schema: type[BaseModel] = DataCleaningInput
    
    def _run(self, candidate_data: dict, program_attributes: dict) -> str:
        """Clean and encode data"""
        try:
            # Basic cleaning - handle missing values
            cleaned_candidate = {k: v if v is not None and v != '' else 'unknown' for k, v in candidate_data.items()}
            cleaned_program = {k: v if v is not None and v != '' else 'unknown' for k, v in program_attributes.items()}
            
            return json.dumps({
                "cleaned_candidate": cleaned_candidate,
                "cleaned_program": cleaned_program,
                "status": "success"
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

# Create tool instances
logistic_model_tool = LogisticModelTool()
data_cleaning_tool = DataCleaningTool()

def create_prospection_agent():
    """Create the Prospection Agent (Graduate Program Application Probability Modeler)"""
    return Agent(
        role="Graduate Program Application Probability Modeler",
        goal="Estimate probability that a candidate will apply to a given education graduate program using a logistic regression or probabilistic model.",
        backstory="""You are an expert data-modeling agent. Your job is to predict the probability that a candidate applies to a graduate education program (teacher certification or master's in education). You analyze candidate attributes + program attributes and produce a structured probability output.""",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[logistic_model_tool, data_cleaning_tool],
        verbose=False
    )

def create_predict_probability_task(prospection_agent: Agent, blueprint_task: Task, load_task: Task, use_synthetic_data: bool = False):
    """Create the prediction task for computing application probability"""
    
    if use_synthetic_data:
        description = """Using the candidate profiles from the dataset (provided in the previous task) and program attributes from the blueprint,
compute or simulate P(Apply = 1) using logistic modeling logic.

For each candidate in the dataset:

1. Extract candidate attributes:
   - Academic/Professional: years_work_experience, years_education_experience, current_position (prior_role), 
     prior_degree_level, prior_degree_field, gpa_percentile, sat_percentile
   - Demographic/Socioeconomic: age, gender, individual_income_level, parental_education_level,
     state (home_state_or_region), international_candidate, number_of_dependents (is_parent),
     disposable_income_for_university

2. Use program attributes from the blueprint (ideal_profile):
   - Consider selectivity, fit, passion alignment, financial factors

3. If historical_data is provided:
   - Fit logistic regression
   - Use coefficients to compute probability
   - Output prediction + key drivers

4. If NO historical data is available:
   - Do NOT fabricate coefficients
   - Instead output a theoretical high/medium/low propensity
   - Clearly mark it as non-empirical

For the top 10 candidates (ranked by predicted probability), format EXACTLY as:

Top 10 Candidates for Harvard Graduate School of Education:

1. [Full Name: first_name + last_name]
   Predicted Application Probability: [MUST include a number between 0.0 and 1.0, e.g., 0.75, 0.82, 0.65. If theoretical, use an estimated value like 0.7 for high, 0.5 for medium, 0.3 for low]
   Propensity Segment: [high/medium/low]
   Background: [Current Position] with [years_work_experience] years work exp, [years_education_experience] years education exp, [Prior Degree Level] in [Prior Degree Field]. Interest: [Interest]. GPA: [GPA]. Located in [State].
   Key Positive Drivers: [List factors that increase application likelihood]
   Key Negative Drivers: [List factors that decrease application likelihood]
   Assumptions/Warnings: [Any assumptions or warnings about the prediction]

2. [Full Name]
   Predicted Application Probability: [MUST include a number between 0.0 and 1.0, e.g., 0.75, 0.82, 0.65]
   Propensity Segment: [high/medium/low]
   Background: [Current Position] with [years_work_experience] years work exp, [years_education_experience] years education exp, [Prior Degree Level] in [Prior Degree Field]. Interest: [Interest]. GPA: [GPA]. Located in [State].
   Key Positive Drivers: [...]
   Key Negative Drivers: [...]
   Assumptions/Warnings: [...]

[Continue for all 10 candidates]

CRITICAL: You MUST provide a numerical probability value (0.0-1.0) for each candidate. Calculate this based on:
- Candidate attributes (experience, education, GPA, interest alignment)
- Program fit factors (selectivity, financial factors, mission alignment)
- Use theoretical estimates if no historical data: high=0.7-0.9, medium=0.4-0.6, low=0.1-0.3

IMPORTANT: Use ONLY real data from the dataset provided in the previous task."""
    else:
        # Original task description for Kaggle data
        description = """Using the provided candidate profiles and program attributes from the blueprint,
compute or simulate P(Apply = 1) using logistic modeling logic.

If historical_data is provided:
  - Fit logistic regression
  - Use coefficients to compute probability
  - Output prediction + key drivers

If NO historical data is available:
  - Do NOT fabricate coefficients
  - Instead output a theoretical high/medium/low propensity
  - Clearly mark it as non-empirical

For each candidate, return JSON containing:
  - predicted_probability_apply (0–1 or null if theoretical)
  - propensity_segment (high / medium / low)
  - key_positive_drivers
  - key_negative_drivers
  - assumptions_or_warnings

Format EXACTLY as:
"Top 10 Candidates for Harvard Graduate School of Education:

1. [Full Name]
   Predicted Application Probability: [0.0-1.0 or null]
   Propensity Segment: [high/medium/low]
   Background: [Detailed professional background]
   Key Positive Drivers: [List factors]
   Key Negative Drivers: [List factors]
   Assumptions/Warnings: [Any assumptions]

[Continue for all 10 candidates]"""
    
    return Task(
        description=description,
        agent=prospection_agent,
        context=[blueprint_task, load_task],
        expected_output="Ranked list of 10 candidates with predicted application probabilities, propensity segments, key drivers, and assumptions"
    )

# Alias for backward compatibility
def create_modeler_agent():
    """Alias for create_prospection_agent for backward compatibility"""
    return create_prospection_agent()

def create_rank_task(modeler_agent: Agent, blueprint_task: Task, ingest_task: Task, use_synthetic_data: bool = False):
    """Alias for create_predict_probability_task for backward compatibility"""
    return create_predict_probability_task(modeler_agent, blueprint_task, ingest_task, use_synthetic_data)
