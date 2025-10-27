"""
UDiscovery Agentic Pipeline - Agents Module

This module contains the UDiscoveryAgents class with all 5 agents
for the candidate discovery pipeline using CrewAI framework.
"""

from crewai import Agent
from crewai_tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
import subprocess
import csv
import json

# Define tools as standalone functions for CrewAI
def create_search_tool():
    """Create search_kaggle_datasets tool"""
    @BaseTool("search_kaggle_datasets")
    def search_kaggle_datasets(search_query: str) -> str:
        """Search for Kaggle datasets using the Kaggle CLI."""
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
    
    return search_kaggle_datasets

# Create tools
search_tool = create_search_tool()


class UDiscoveryAgents:
    """
    A class containing all 5 agents for the UDiscovery pipeline.
    Each agent is configured with specific roles, goals, and tools.
    """
    
    def __init__(self, google_api_key: str = None):
        """
        Initialize the agents with Google Gemini LLM.
        
        Args:
            google_api_key (str): Google API key for Gemini access
        """
        # Initialize LLM (you can replace with your preferred model)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            google_api_key=google_api_key
        )
    
    def trait_inferrer_agent(self) -> Agent:
        """
        Agent that analyzes university program goals and creates candidate blueprints.
        
        Returns:
            Agent: Configured CrewAI Agent for trait inference
        """
        return Agent(
            role="University Strategy Analyst",
            goal="""Transform high-level university program goals into a detailed candidate blueprint 
            that includes ideal candidate traits and Kaggle search keywords for data sourcing.""",
            backstory="""You are an expert university strategy analyst with deep experience in 
            graduate admissions and student success patterns. You understand how to translate 
            institutional goals into specific candidate profiles that drive enrollment success. 
            Your expertise lies in identifying the key traits, experiences, and characteristics 
            that predict student success in specific graduate programs.""",
            allow_delegation=False,
            llm=self.llm,
            tools=[]  # No tools needed for this agent
        )
    
    def kaggle_scout_agent(self) -> Agent:
        """
        Agent that searches Kaggle for relevant datasets using provided keywords.
        
        Returns:
            Agent: Configured CrewAI Agent for Kaggle dataset searching
        """
        return Agent(
            role="Data Sourcing Specialist",
            goal="""Use provided search keywords to discover and identify the most relevant 
            Kaggle datasets that contain candidate information matching the university's needs.""",
            backstory="""You are a skilled data sourcing specialist with extensive experience 
            in finding and evaluating datasets across various platforms. You excel at translating 
            search requirements into effective queries and identifying high-quality datasets that 
            contain the specific information needed for candidate analysis.""",
            allow_delegation=False,
            llm=self.llm,
            tools=[search_tool]  # Use CrewAI tool
        )
    
    def dataset_evaluator_agent(self) -> Agent:
        """
        Agent that evaluates dataset quality and selects the best option.
        
        Returns:
            Agent: Configured CrewAI Agent for dataset evaluation
        """
        return Agent(
            role="Dataset Quality Analyst",
            goal="""Evaluate the file contents and structure of multiple datasets to identify 
            the single best dataset that contains the most relevant and comprehensive candidate data.""",
            backstory="""You are a meticulous dataset quality analyst with expertise in evaluating 
            data sources for completeness, relevance, and usability. You have a keen eye for 
            identifying datasets that contain the right mix of candidate attributes and sufficient 
            data quality for meaningful analysis.""",
            allow_delegation=False,
            llm=self.llm,
            tools=[kaggle_tools.inspect_dataset_files]
        )
    
    def data_ingestion_agent(self) -> Agent:
        """
        Agent that handles dataset download and data preparation.
        
        Returns:
            Agent: Configured CrewAI Agent for data ingestion
        """
        return Agent(
            role="Data Engineer",
            goal="""Download the selected dataset, locate the relevant CSV files, and prepare 
            a clean sample of candidate data for analysis and scoring.""",
            backstory="""You are an experienced data engineer specializing in data ingestion and 
            preparation. You excel at downloading datasets, handling various file formats, 
            and preparing clean, structured data for downstream analysis. Your attention to 
            detail ensures data quality and proper formatting.""",
            allow_delegation=False,
            llm=self.llm,
            tools=[
                kaggle_tools.download_kaggle_dataset,
                kaggle_tools.read_csv_data
            ]
        )
    
    def propensity_modeler_agent(self) -> Agent:
        """
        Agent that scores candidates based on ideal profile and produces ranked results.
        
        Returns:
            Agent: Configured CrewAI Agent for candidate scoring
        """
        return Agent(
            role="Admissions Propensity Modeler",
            goal="""Analyze candidate data against the ideal profile blueprint to score and rank 
            candidates, producing a final list of the top 10 most promising candidates with 
            detailed justifications for each score.""",
            backstory="""You are a sophisticated admissions propensity modeler with deep expertise 
            in candidate evaluation and scoring. You understand the nuances of graduate admissions 
            and excel at creating fair, comprehensive scoring models that identify the most 
            promising candidates while providing clear justifications for your assessments.""",
            allow_delegation=False,
            llm=self.llm,
            tools=[]  # No tools needed for this agent
        )
    
    def get_all_agents(self) -> dict:
        """
        Get all agents as a dictionary for easy access.
        
        Returns:
            dict: Dictionary containing all agent instances
        """
        return {
            "trait_inferrer": self.trait_inferrer_agent(),
            "kaggle_scout": self.kaggle_scout_agent(),
            "dataset_evaluator": self.dataset_evaluator_agent(),
            "data_ingestion": self.data_ingestion_agent(),
            "propensity_modeler": self.propensity_modeler_agent()
        }
