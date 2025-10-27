"""
UDiscovery Agentic Pipeline - Main Execution Script

This script orchestrates the complete UDiscovery pipeline using CrewAI
to find prospective candidates for university graduate programs.
"""

import os
from dotenv import load_dotenv
from crewai import Crew, Process
from agents import UDiscoveryAgents
from tasks import UDiscoveryTasks

# Load environment variables from .env file
load_dotenv()


def main():
    """
    Main execution function for the UDiscovery pipeline.
    """
    
    # Define the university's program goals and requirements
    UNIVERSITY_GOAL = """
    Find candidates for our Master's in Education Leadership program. We are looking for 
    experienced educators who have demonstrated leadership potential and want to advance 
    their careers in educational administration. Ideal candidates should have:
    
    - At least 3 years of teaching experience
    - Some leadership experience (department head, committee chair, etc.)
    - Strong communication and interpersonal skills
    - Interest in educational policy and administration
    - Geographic preference for candidates in the Northeast US
    - Commitment to equity and inclusion in education
    
    We want to identify candidates who are likely to apply and succeed in our program, 
    with particular focus on those who can contribute to our mission of developing 
    transformative educational leaders.
    """
    
    print("🚀 Starting UDiscovery Agentic Pipeline...")
    print(f"📋 University Goal: {UNIVERSITY_GOAL.strip()}")
    print("-" * 80)
    
    # Initialize agents and tasks
    print("🤖 Initializing agents...")
    agents_manager = UDiscoveryAgents(google_api_key=os.getenv("GOOGLE_API_KEY"))
    tasks_manager = UDiscoveryTasks()
    
    # Create all 5 agent instances
    print("👥 Creating agent instances...")
    agents = agents_manager.get_all_agents()
    
    # Create all 5 task instances with proper context dependencies
    print("📋 Creating task instances...")
    tasks = tasks_manager.get_all_tasks(agents, UNIVERSITY_GOAL)
    
    # Create the Crew with sequential processing
    print("🔧 Setting up Crew with sequential processing...")
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    # Execute the pipeline
    print("⚡ Starting pipeline execution...")
    print("=" * 80)
    
    try:
        result = crew.kickoff()
        
        print("=" * 80)
        print("🎉 Pipeline execution completed successfully!")
        print("=" * 80)
        print("📊 FINAL RESULTS:")
        print("=" * 80)
        print(result)
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ Error during pipeline execution: {str(e)}")
        print("🔍 Please check your OpenAI API key and Kaggle CLI configuration.")
        return None


def run_with_custom_goal(custom_goal: str):
    """
    Run the pipeline with a custom university goal.
    
    Args:
        custom_goal (str): Custom university program goals and requirements
    """
    global UNIVERSITY_GOAL
    UNIVERSITY_GOAL = custom_goal
    return main()


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set.")
        print("   Please set your Google API key: export GOOGLE_API_KEY='your-key-here'")
        print("   Or add it to your .env file: GOOGLE_API_KEY=your-key-here")
        print()
    
    # Check for Kaggle CLI
    try:
        import subprocess
        subprocess.run(["kaggle", "--version"], capture_output=True, check=True)
        print("✅ Kaggle CLI is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Warning: Kaggle CLI not found or not configured.")
        print("   Please install and configure Kaggle CLI:")
        print("   1. pip install kaggle")
        print("   2. Set up your Kaggle API credentials")
        print()
    
    # Run the main pipeline
    result = main()
    
    if result:
        print("\n🎯 Pipeline completed successfully!")
        print("📈 Check the results above for your top candidate recommendations.")
    else:
        print("\n❌ Pipeline failed. Please check the error messages above.")
