#!/usr/bin/env python3
"""
Trait Inferrer Agent Module
Contains the University Strategy Analyst agent and blueprint creation task.
"""

from crewai import Agent, Task

def create_trait_agent():
    """Create the Trait Inferrer agent (University Strategy Analyst)"""
    return Agent(
        role="University Strategy Analyst",
        goal="Transform university goals into candidate blueprint with ideal traits and Kaggle search keywords.",
        backstory="Expert in graduate admissions who translates institutional goals into specific candidate profiles.",
        allow_delegation=False,
        llm="gemini/gemini-2.0-flash",
        tools=[],
        verbose=False
    )

def create_blueprint_task(trait_agent: Agent, university_goal: str):
    """Create the blueprint task for analyzing university goals"""
    return Task(
        description=f"""Analyze these university goals and create a candidate blueprint:

{university_goal}

Return JSON with:
- "ideal_profile": Description of ideal candidate traits
- "kaggle_search_keywords": 5-10 general search terms (use: "resumes", "employees", "workers", "profiles", "careers", "professional", "linkedin", "job market")""",
        agent=trait_agent,
        expected_output="JSON: ideal_profile and kaggle_search_keywords list"
    )

