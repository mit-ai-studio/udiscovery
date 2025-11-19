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

def create_rank_task(modeler_agent: Agent, blueprint_task: Task, ingest_task: Task):
    """Create the ranking task for scoring and ranking candidates"""
    return Task(
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

