#!/usr/bin/env python3
"""
Propensity Modeler Agent Module
Contains the Admissions Propensity Modeler agent and candidate ranking task.
"""

from crewai import Agent, Task

def create_modeler_agent():
    """Create the Propensity Modeler agent (Admissions Propensity Modeler)"""
    return Agent(
        role="Admissions Propensity Modeler",
        goal="Score and rank top 10 candidates with detailed justifications.",
        backstory="Expert in candidate evaluation and scoring for graduate admissions.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )

def create_rank_task(modeler_agent: Agent, blueprint_task: Task, ingest_task: Task, use_synthetic_data: bool = False):
    """Create the ranking task for scoring and ranking candidates"""
    
    if use_synthetic_data:
        # Task description for synthetic dataset with specific fields
        description = """Score and rank top 10 candidates using the ideal profile from Agent 1 and the candidate data from Agent 4.

The dataset contains candidates with the following fields:
- first_name, last_name (combine for full name)
- current_position (e.g., "K-12 Classroom Teacher", "School or District Leader")
- experience_years, years_work_experience, years_education_experience
- prior_degree_level, prior_degree_field
- interest (education focus area like "Inclusive & Special Education", "Edtech & Digital Learning")
- gpa, gpa_percentile
- state (location)
- age

For each candidate, extract their actual data from the dataset and score them against the ideal profile.

Format EXACTLY as:
"Top 10 Candidates for Harvard Graduate School of Education:

1. [Full Name from dataset: first_name + last_name]
   Score: XX/100
   Background: [Current Position] with [years_work_experience] years of work experience and [years_education_experience] years in education. [Prior Degree Level] in [Prior Degree Field]. Interest: [Interest]. GPA: [GPA]. Located in [State].
   Why they match: [Specific reasons why this candidate matches the ideal profile from Agent 1]

2. [Full Name from dataset]
   Score: XX/100
   Background: [Current Position] with [years_work_experience] years of work experience and [years_education_experience] years in education. [Prior Degree Level] in [Prior Degree Field]. Interest: [Interest]. GPA: [GPA]. Located in [State].
   Why they match: [Detailed explanation]

[Continue for all 10 candidates using ONLY real data from the dataset]"""
    else:
        # Original task description for Kaggle data
        description = """Score and rank top 10 candidates using the ideal profile from Agent 1.

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

[Continue for all 10 candidates]"""
    
    return Task(
        description=description,
        agent=modeler_agent,
        context=[blueprint_task, ingest_task],
        expected_output="Ranked list of 10 candidates with scores, names, backgrounds, and matching explanations"
    )

