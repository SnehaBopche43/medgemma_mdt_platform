import json
import os
from src.agents.orchestrator import AgentOrchestrator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check API Key
if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not found in .env file")
    exit()

# Load sample case
print("Loading breast cancer sample case...")
with open('data/sample_cases/breast_cancer_case.json', 'r') as f:
    case = json.load(f)

case_data = case['cancer_case']
case_data.update(case['patient_info'])

# Initialize orchestrator
print("Initializing Multi-Agent Orchestrator...")
orchestrator = AgentOrchestrator()

# Run analysis - FIXED: use analyze_case() with cancer_type parameter
print("Running analysis...")
results = orchestrator.analyze_case(case_data, cancer_type='breast')

# Print results
print("\n" + "="*80)
print("ANALYSIS RESULTS:")
print("="*80)
print(json.dumps(results, indent=2))
print("="*80)
print("\nTest complete!")
