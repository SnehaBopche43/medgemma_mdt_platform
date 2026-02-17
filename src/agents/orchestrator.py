"""
Multi-Agent Orchestrator for MedGemma MDT Platform
Coordinates specialized agents for comprehensive cancer case analysis
"""
import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GOOGLE_API_KEY)


class AgentOrchestrator:
    """Orchestrates multiple specialized agents for MDT case analysis"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(Config.MEDGEMMA_MODEL)
        self.agents = {
            'clinical_summary': ClinicalSummaryAgent(),
            'staging': StagingAgent(),
            'treatment': TreatmentPlanningAgent(),
            'trial_matching': TrialMatchingAgent()
        }
    
    def analyze_case(self, case_data, cancer_type):
        """
        Orchestrate multi-agent analysis of a cancer case
        
        Args:
            case_data: Dictionary containing patient and clinical data
            cancer_type: Type of cancer (breast, lung, colorectal)
        
        Returns:
            Comprehensive analysis from all agents
        """
        results = {
            'cancer_type': cancer_type,
            'agents': {}
        }
        
        # 1. Clinical Summary Agent
        print("Running Clinical Summary Agent...")
        results['agents']['clinical_summary'] = self.agents['clinical_summary'].analyze(case_data, cancer_type)
        
        # 2. Staging Agent
        print("Running Staging Agent...")
        results['agents']['staging'] = self.agents['staging'].analyze(case_data, cancer_type)
        
        # 3. Treatment Planning Agent
        print("Running Treatment Planning Agent...")
        results['agents']['treatment'] = self.agents['treatment'].analyze(
            case_data, 
            cancer_type,
            stage=results['agents']['staging'].get('stage')
        )
        
        # 4. Trial Matching Agent
        print("Running Trial Matching Agent...")
        results['agents']['trial_matching'] = self.agents['trial_matching'].analyze(case_data, cancer_type)
        
        # 5. Cross-validation and synthesis
        results['synthesis'] = self._synthesize_results(results)
        
        return results
    
    def _synthesize_results(self, results):
        """Synthesize results from all agents into cohesive recommendations"""
        synthesis = {
            'summary': results['agents']['clinical_summary'].get('summary', ''),
            'stage': results['agents']['staging'].get('stage', 'Unknown'),
            'recommended_treatment': results['agents']['treatment'].get('primary_recommendation', ''),
            'alternative_treatments': results['agents']['treatment'].get('alternatives', []),
            'clinical_trials': results['agents']['trial_matching'].get('top_matches', []),
            'missing_information': self._identify_missing_info(results),
            'confidence_level': self._calculate_confidence(results)
        }
        return synthesis
    
    def _identify_missing_info(self, results):
        """Identify missing critical information across all agents"""
        missing = []
        
        # Check clinical summary
        if 'missing_data' in results['agents']['clinical_summary']:
            missing.extend(results['agents']['clinical_summary']['missing_data'])
        
        # Check staging
        if 'incomplete_staging' in results['agents']['staging']:
            missing.extend(results['agents']['staging']['incomplete_staging'])
        
        return list(set(missing))  # Remove duplicates
    
    def _calculate_confidence(self, results):
        """Calculate overall confidence level based on data completeness"""
        total_fields = 0
        complete_fields = 0
        
        for agent_name, agent_results in results['agents'].items():
            if 'confidence' in agent_results:
                total_fields += 1
                if agent_results['confidence'] > 0.7:
                    complete_fields += 1
        
        if total_fields == 0:
            return 0.5
        
        return complete_fields / total_fields


class ClinicalSummaryAgent:
    """Agent specialized in clinical data summarization"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(Config.MEDGEMMA_MODEL)
    
    def analyze(self, case_data, cancer_type):
        """Generate clinical summary from case data"""
        prompt = f"""You are a clinical summary specialist. Analyze the following {cancer_type} cancer case data and provide a concise clinical summary.

Case Data:
{self._format_case_data(case_data)}

Provide:
1. Patient demographics summary
2. Key clinical findings
3. Relevant medical history
4. Current presentation
5. Any missing critical information

Format as structured JSON."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=Config.MEDGEMMA_TEMPERATURE,
                    max_output_tokens=Config.MEDGEMMA_MAX_TOKENS
                )
            )
            
            return {
                'summary': response.text,
                'confidence': 0.85,
                'missing_data': self._extract_missing_fields(case_data)
            }
        except Exception as e:
            return {
                'summary': f'Error generating summary: {str(e)}',
                'confidence': 0.0,
                'missing_data': []
            }
    
    def _format_case_data(self, case_data):
        """Format case data for prompt"""
        formatted = []
        for key, value in case_data.items():
            formatted.append(f"{key}: {value}")
        return "\n".join(formatted)
    
    def _extract_missing_fields(self, case_data):
        """Identify missing critical fields"""
        required = ['histology', 'tumor_size', 'lymph_node_status', 'biomarkers']
        missing = [field for field in required if field not in case_data or not case_data[field]]
        return missing


class StagingAgent:
    """Agent specialized in cancer staging (AJCC 8th Edition)"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(Config.MEDGEMMA_MODEL)
    
    def analyze(self, case_data, cancer_type):
        """Determine cancer stage based on TNM classification"""
        prompt = f"""You are a cancer staging specialist using AJCC 8th Edition criteria. Analyze the following {cancer_type} cancer case and determine the stage.

Case Data:
{self._format_staging_data(case_data)}

Provide:
1. T stage (Tumor)
2. N stage (Nodes)
3. M stage (Metastasis)
4. Overall AJCC stage
5. Rationale for staging
6. Any missing information needed for accurate staging

Format as structured JSON."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,  # Very low temperature for staging accuracy
                    max_output_tokens=2000
                )
            )
            
            return {
                'stage': self._extract_stage(response.text),
                'tnm': self._extract_tnm(response.text),
                'rationale': response.text,
                'confidence': 0.9,
                'incomplete_staging': []
            }
        except Exception as e:
            return {
                'stage': 'Unknown',
                'tnm': {'T': 'Unknown', 'N': 'Unknown', 'M': 'Unknown'},
                'rationale': f'Error in staging: {str(e)}',
                'confidence': 0.0,
                'incomplete_staging': ['tumor_size', 'lymph_node_status', 'metastasis_status']
            }
    
    def _format_staging_data(self, case_data):
        """Format relevant staging data"""
        staging_fields = ['tumor_size', 'lymph_node_status', 'metastasis_status', 'histology']
        formatted = []
        for field in staging_fields:
            if field in case_data:
                formatted.append(f"{field}: {case_data[field]}")
        return "\n".join(formatted)
    
    def _extract_stage(self, text):
        """Extract stage from response text"""
        # Simple extraction - in production, use more robust parsing
        for stage in Config.AJCC_STAGES:
            if stage in text:
                return stage
        return 'Unknown'
    
    def _extract_tnm(self, text):
        """Extract TNM classification from response"""
        # Placeholder - implement proper extraction
        return {'T': 'T2', 'N': 'N1', 'M': 'M0'}


class TreatmentPlanningAgent:
    """Agent specialized in treatment planning"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(Config.MEDGEMMA_MODEL)
    
    def analyze(self, case_data, cancer_type, stage=None):
        """Generate treatment recommendations"""
        prompt = f"""You are a treatment planning specialist for {cancer_type} cancer. Based on the case data and stage, recommend evidence-based treatment options.

Cancer Type: {cancer_type}
Stage: {stage}

Case Data:
{self._format_treatment_data(case_data)}

Provide:
1. Primary treatment recommendation with rationale
2. Alternative treatment options
3. Sequence of treatments (neoadjuvant, adjuvant)
4. Expected outcomes
5. NCCN guideline references

Format as structured JSON."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=Config.MEDGEMMA_TEMPERATURE,
                    max_output_tokens=Config.MEDGEMMA_MAX_TOKENS
                )
            )
            
            return {
                'primary_recommendation': self._extract_primary_treatment(response.text),
                'alternatives': self._extract_alternatives(response.text),
                'rationale': response.text,
                'confidence': 0.85,
                'guidelines_referenced': ['NCCN']
            }
        except Exception as e:
            return {
                'primary_recommendation': f'Error generating treatment plan: {str(e)}',
                'alternatives': [],
                'rationale': '',
                'confidence': 0.0,
                'guidelines_referenced': []
            }
    
    def _format_treatment_data(self, case_data):
        """Format relevant treatment data"""
        treatment_fields = ['biomarkers', 'histology', 'grade', 'performance_status']
        formatted = []
        for field in treatment_fields:
            if field in case_data:
                formatted.append(f"{field}: {case_data[field]}")
        return "\n".join(formatted)
    
    def _extract_primary_treatment(self, text):
        """Extract primary treatment from response"""
        # Placeholder - implement proper extraction
        return "Surgery followed by adjuvant chemotherapy"
    
    def _extract_alternatives(self, text):
        """Extract alternative treatments from response"""
        # Placeholder - implement proper extraction
        return ["Neoadjuvant chemotherapy followed by surgery", "Radiation therapy"]


class TrialMatchingAgent:
    """Agent specialized in clinical trial matching"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(Config.MEDGEMMA_MODEL)
    
    def analyze(self, case_data, cancer_type):
        """Match patient to relevant clinical trials"""
        # In production, this would query ClinicalTrials.gov API
        # For now, use LLM to suggest trial criteria
        
        prompt = f"""You are a clinical trial matching specialist. Based on the patient's {cancer_type} cancer profile, identify key eligibility criteria for clinical trials.

Case Data:
{self._format_trial_data(case_data)}

Provide:
1. Key eligibility criteria
2. Biomarker requirements
3. Stage requirements
4. Suggested trial types (immunotherapy, targeted therapy, etc.)

Format as structured JSON."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=Config.MEDGEMMA_TEMPERATURE,
                    max_output_tokens=2000
                )
            )
            
            return {
                'top_matches': self._mock_trial_matches(cancer_type),
                'eligibility_criteria': response.text,
                'confidence': 0.75
            }
        except Exception as e:
            return {
                'top_matches': [],
                'eligibility_criteria': f'Error matching trials: {str(e)}',
                'confidence': 0.0
            }
    
    def _format_trial_data(self, case_data):
        """Format relevant trial matching data"""
        trial_fields = ['cancer_type', 'stage', 'biomarkers', 'prior_treatments']
        formatted = []
        for field in trial_fields:
            if field in case_data:
                formatted.append(f"{field}: {case_data[field]}")
        return "\n".join(formatted)
    
    def _mock_trial_matches(self, cancer_type):
        """Mock trial matches - in production, query ClinicalTrials.gov"""
        return [
            {
                'trial_id': 'NCT12345678',
                'title': f'Phase III Study of Novel Therapy for {cancer_type.title()} Cancer',
                'eligibility_score': 0.85,
                'location': 'Multiple sites'
            },
            {
                'trial_id': 'NCT87654321',
                'title': f'Immunotherapy Trial for Advanced {cancer_type.title()} Cancer',
                'eligibility_score': 0.72,
                'location': 'Academic medical centers'
            }
        ]
