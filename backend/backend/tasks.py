"""
UDiscovery Agentic Pipeline - Tasks Module

This module contains the UDiscoveryTasks class with all 5 tasks
for the candidate discovery pipeline using CrewAI framework.
"""

from crewai import Task
from typing import List


class UDiscoveryTasks:
    """
    A class containing all 5 tasks for the UDiscovery pipeline.
    Each task is configured with specific agents, contexts, and expected outputs.
    """
    
    def create_blueprint_task(self, human_input: str, agent) -> Task:
        """
        Task for creating a candidate blueprint from university program goals.
        
        Args:
            human_input (str): The university's program goals and requirements
            agent: The trait_inferrer_agent
            
        Returns:
            Task: Configured CrewAI Task for blueprint creation
        """
        return Task(
            description=f"""
            Analyze the following university program goals and requirements:
            
            {human_input}
            
            Create a comprehensive candidate blueprint as a JSON object with exactly two keys:
            1. "ideal_profile": A detailed description of the ideal candidate traits, including:
               - Academic qualifications and background
               - Professional experience requirements
               - Skills and competencies needed
               - Personal characteristics and attributes
               - Geographic preferences
               - Any specific requirements or preferences
            
            2. "kaggle_search_keywords": A list of 5-10 search terms that would help find 
               relevant datasets containing candidate information, such as:
               - Professional titles and roles
               - Industry keywords
               - Educational background terms
               - Geographic locations
               - Skills and technologies
            
            The blueprint should be comprehensive yet specific enough to guide effective 
            data sourcing and candidate evaluation.
            """,
            expected_output="""
            A JSON object with two keys:
            - "ideal_profile": Detailed description of ideal candidate traits
            - "kaggle_search_keywords": List of 5-10 search terms for dataset discovery
            """,
            agent=agent
        )
    
    def find_datasets_task(self, agent) -> Task:
        """
        Task for finding relevant Kaggle datasets using search keywords.
        
        Args:
            agent: The kaggle_scout_agent
            
        Returns:
            Task: Configured CrewAI Task for dataset discovery
        """
        return Task(
            description="""
            Using the kaggle_search_keywords from the blueprint, search Kaggle for relevant 
            datasets that contain candidate information matching the university's needs.
            
            For each search keyword, use the search_kaggle_datasets tool to find datasets.
            Compile a comprehensive list of all discovered dataset slugs (in username/dataset-name format).
            
            Focus on datasets that likely contain:
            - Professional profiles and resumes
            - Educational backgrounds
            - Skills and competencies
            - Geographic information
            - Industry experience data
            
            Provide a ranked list of the most promising datasets with brief explanations 
            of why each dataset is relevant to the candidate search.
            """,
            expected_output="""
            A ranked list of dataset slugs (username/dataset-name format) with brief 
            explanations of their relevance to the candidate search criteria.
            """,
            agent=agent,
            context=[self.create_blueprint_task]  # Depends on blueprint task
        )
    
    def evaluate_datasets_task(self, agent) -> Task:
        """
        Task for evaluating and selecting the best dataset.
        
        Args:
            agent: The dataset_evaluator_agent
            
        Returns:
            Task: Configured CrewAI Task for dataset evaluation
        """
        return Task(
            description="""
            Evaluate the datasets found by the scout agent to select the single best dataset 
            for candidate analysis.
            
            For each dataset slug provided, use the inspect_dataset_files tool to examine 
            the file structure and contents.
            
            Evaluate datasets based on:
            - File types and formats (prefer CSV files with structured data)
            - File sizes and completeness
            - Relevance to candidate profiles
            - Data quality indicators
            - Ease of processing
            
            Select the single best dataset slug that contains the most comprehensive and 
            relevant candidate information for the university's needs.
            
            Provide a clear justification for your selection.
            """,
            expected_output="""
            A single dataset slug (username/dataset-name format) with a clear justification 
            for why this dataset is the best choice for candidate analysis.
            """,
            agent=agent,
            context=[self.find_datasets_task]  # Depends on dataset discovery task
        )
    
    def ingest_data_task(self, agent) -> Task:
        """
        Task for downloading and preparing candidate data.
        
        Args:
            agent: The data_ingestion_agent
            
        Returns:
            Task: Configured CrewAI Task for data ingestion
        """
        return Task(
            description="""
            Download the selected dataset and prepare the candidate data for analysis.
            
            Use the download_kaggle_dataset tool to download the chosen dataset.
            Then use the read_csv_data tool to read the CSV file and prepare a sample 
            of candidate data.
            
            Ensure the data is properly formatted and ready for candidate scoring.
            Provide a summary of the data structure and key fields available.
            """,
            expected_output="""
            A JSON string containing the candidate data (first 50 rows) along with a 
            summary of the data structure and available fields.
            """,
            agent=agent,
            context=[self.evaluate_datasets_task]  # Depends on dataset evaluation task
        )
    
    def rank_candidates_task(self, agent) -> Task:
        """
        Task for scoring and ranking candidates.
        
        Args:
            agent: The propensity_modeler_agent
            
        Returns:
            Task: Configured CrewAI Task for candidate ranking
        """
        return Task(
            description="""
            Score and rank candidates based on the ideal profile blueprint and candidate data.
            
            Analyze each candidate against the ideal_profile criteria and assign scores based on:
            - Academic qualifications match
            - Professional experience relevance
            - Skills and competencies alignment
            - Geographic preferences
            - Overall fit with program goals
            
            Create a comprehensive scoring system and rank candidates accordingly.
            Provide detailed justifications for each score.
            
            Return the top 10 most promising candidates with:
            - Candidate ID/identifier
            - Overall score (0-100)
            - Detailed scoring breakdown
            - Justification for the score
            - Key strengths and potential concerns
            """,
            expected_output="""
            A ranked list of the top 10 candidates with:
            - Candidate identifier
            - Overall score (0-100)
            - Detailed scoring breakdown
            - Justification for the score
            - Key strengths and potential concerns
            """,
            agent=agent,
            context=[self.create_blueprint_task, self.ingest_data_task]  # Depends on both blueprint and data
        )
    
    def get_all_tasks(self, agents: dict, human_input: str) -> List[Task]:
        """
        Get all tasks as a list for easy access.
        
        Args:
            agents (dict): Dictionary containing all agent instances
            human_input (str): The university's program goals and requirements
            
        Returns:
            List[Task]: List containing all task instances
        """
        return [
            self.create_blueprint_task(human_input, agents["trait_inferrer"]),
            self.find_datasets_task(agents["kaggle_scout"]),
            self.evaluate_datasets_task(agents["dataset_evaluator"]),
            self.ingest_data_task(agents["data_ingestion"]),
            self.rank_candidates_task(agents["propensity_modeler"])
        ]
