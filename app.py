"""
MedGemma MDT Platform - Main Streamlit Dashboard
Comprehensive MDT case preparation with voice/manual/patient selection modes
"""
import streamlit as st
import os
from datetime import datetime
from config import Config
from src.database.db_manager import DatabaseManager
from src.cancer_pipelines.cancer_selector import CancerSelector
from src.integration_adapter import IntegrationAdapter

# Page configuration
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager(Config.DATABASE_PATH)
if 'cancer_selector' not in st.session_state:
    st.session_state.cancer_selector = CancerSelector()
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = IntegrationAdapter()
if 'current_case' not in st.session_state:
    st.session_state.current_case = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None


def main():
    """Main application"""
    
    # Header
    st.title(f"{Config.APP_ICON} {Config.APP_TITLE}")
    st.markdown("### AI-Powered Multidisciplinary Team Case Preparation")
    st.markdown("---")
    
    # Sidebar - Input Mode Selection
    with st.sidebar:
        st.header("📋 Input Mode")
        input_mode = st.radio(
            "Select how to input case data:",
            ["🎤 Voice Recording", "✍️ Manual Entry", "👤 Select Patient", "🔬 Cancer Type"],
            index=1
        )
        
        st.markdown("---")
        st.header("ℹ️ About")
        st.info("""
        **MedGemma MDT Platform** streamlines MDT case preparation using:
        - MedASR for medical transcription
        - MedGemma multi-agent AI
        - Evidence-based recommendations
        - Clinical trial matching
        - HITL approval workflow
        """)
    
    # Main content based on input mode
    if input_mode == "🎤 Voice Recording":
        voice_recording_mode()
    elif input_mode == "✍️ Manual Entry":
        manual_entry_mode()
    elif input_mode == "👤 Select Patient":
        patient_selection_mode()
    elif input_mode == "🔬 Cancer Type":
        cancer_type_info_mode()


def voice_recording_mode():
    """Voice recording transcription mode"""
    st.header("🎤 Voice Recording Transcription")
    st.markdown("Upload audio recording of MDT discussion or clinical notes")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Cancer type selection
        cancer_type = st.selectbox(
            "Select Cancer Type",
            Config.CANCER_TYPES,
            format_func=lambda x: x.title()
        )
        
        # Audio file upload
        audio_file = st.file_uploader(
            "Upload Audio File",
            type=['mp3', 'wav', 'mp4', 'webm', 'm4a'],
            help="Supported formats: MP3, WAV, MP4, WebM, M4A"
        )
        
        if audio_file:
            st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
            
            if st.button("🎯 Transcribe & Analyze", type="primary"):
                with st.spinner("Processing audio..."):
                    # Save uploaded file
                    audio_path = os.path.join(Config.UPLOADS_DIR, audio_file.name)
                    with open(audio_path, 'wb') as f:
                        f.write(audio_file.getbuffer())
                    
                    # Transcribe using MedASR
                    st.info("🎤 Transcribing with MedASR...")
                    transcription = transcribe_audio(audio_path)
                    
                    # Display transcription
                    st.success("✅ Transcription Complete")
                    with st.expander("📝 View Transcription", expanded=True):
                        st.text_area("Transcription", transcription, height=200)
                    
                    # Extract structured data from transcription
                    st.info("🔍 Extracting clinical data...")
                    case_data = extract_clinical_data(transcription, cancer_type)
                    
                    # Run multi-agent analysis
                    st.info("🤖 Running multi-agent analysis...")
                    results = st.session_state.orchestrator.analyze_case(case_data, cancer_type)
                    st.session_state.analysis_results = results
                    
                    # Display results
                    display_analysis_results(results)
    
    with col2:
        st.info("""
        **MedASR Features:**
        - 4.6% Word Error Rate
        - Medical terminology optimized
        - PHI redaction
        - HIPAA compliant
        
        **Supported Audio:**
        - MDT discussions
        - Clinical notes
        - Patient consultations
        """)


def manual_entry_mode():
    """Manual data entry mode"""
    st.header("✍️ Manual Case Entry")
    st.markdown("Enter patient and clinical data manually")
    
    # Cancer type selection
    cancer_type = st.selectbox(
        "Select Cancer Type",
        Config.CANCER_TYPES,
        format_func=lambda x: x.title(),
        key="manual_cancer_type"
    )
    
    # Get pipeline for selected cancer type
    pipeline = st.session_state.cancer_selector.get_pipeline(cancer_type)
    
    # Patient Information
    st.subheader("👤 Patient Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        patient_id = st.text_input("Patient ID", key="manual_patient_id")
        first_name = st.text_input("First Name", key="manual_first_name")
    with col2:
        last_name = st.text_input("Last Name", key="manual_last_name")
        dob = st.date_input("Date of Birth", key="manual_dob")
    with col3:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="manual_gender")
        diagnosis_date = st.date_input("Diagnosis Date", key="manual_diagnosis_date")
    
    st.markdown("---")
    
    # Clinical Data based on cancer type
    st.subheader(f"🔬 {cancer_type.title()} Cancer Clinical Data")
    
    case_data = {}
    
    if cancer_type == "breast":
        col1, col2 = st.columns(2)
        with col1:
            case_data['tumor_size'] = st.text_input("Tumor Size (cm)", key="tumor_size")
            case_data['histology'] = st.selectbox("Histology", 
                ["Invasive Ductal Carcinoma", "Invasive Lobular Carcinoma", "DCIS", "Other"],
                key="histology")
            case_data['grade'] = st.selectbox("Grade", ["Grade 1", "Grade 2", "Grade 3"], key="grade")
        with col2:
            case_data['lymph_node_status'] = st.text_input("Lymph Node Status", key="lymph_nodes")
            case_data['er_status'] = st.selectbox("ER Status", ["Positive", "Negative"], key="er")
            case_data['pr_status'] = st.selectbox("PR Status", ["Positive", "Negative"], key="pr")
            case_data['her2_status'] = st.selectbox("HER2 Status", ["Positive", "Negative", "Equivocal"], key="her2")
    
    elif cancer_type == "lung":
        col1, col2 = st.columns(2)
        with col1:
            case_data['histology'] = st.selectbox("Histology",
                ["Adenocarcinoma", "Squamous Cell Carcinoma", "Small Cell", "Other"],
                key="lung_histology")
            case_data['tumor_size'] = st.text_input("Tumor Size (cm)", key="lung_tumor_size")
            case_data['lymph_node_status'] = st.text_input("Lymph Node Status", key="lung_lymph_nodes")
        with col2:
            case_data['metastasis_status'] = st.selectbox("Metastasis", ["M0", "M1a", "M1b", "M1c"], key="lung_mets")
            case_data['egfr_mutation'] = st.selectbox("EGFR Mutation", ["Positive", "Negative", "Unknown"], key="egfr")
            case_data['alk_status'] = st.selectbox("ALK Status", ["Positive", "Negative", "Unknown"], key="alk")
            case_data['pdl1_expression'] = st.number_input("PD-L1 Expression (%)", 0, 100, key="pdl1")
    
    elif cancer_type == "colorectal":
        col1, col2 = st.columns(2)
        with col1:
            case_data['tumor_location'] = st.selectbox("Tumor Location",
                ["Colon - Right", "Colon - Left", "Rectum", "Other"],
                key="crc_location")
            case_data['histology'] = st.selectbox("Histology",
                ["Adenocarcinoma", "Mucinous", "Signet Ring", "Other"],
                key="crc_histology")
            case_data['tumor_size'] = st.text_input("Tumor Size (cm)", key="crc_tumor_size")
        with col2:
            case_data['lymph_node_status'] = st.text_input("Lymph Node Status", key="crc_lymph_nodes")
            case_data['kras_mutation'] = st.selectbox("KRAS Mutation", ["Mutated", "Wild-type", "Unknown"], key="kras")
            case_data['msi_status'] = st.selectbox("MSI Status", ["MSI-H", "MSS", "Unknown"], key="msi")
            case_data['cea_level'] = st.number_input("CEA Level (ng/mL)", 0.0, 1000.0, key="cea")
    
    st.markdown("---")
    
    # Additional Clinical Notes
    st.subheader("📝 Additional Clinical Notes")
    case_data['clinical_notes'] = st.text_area("Clinical Notes", height=150, key="clinical_notes")
    
    # Analyze button
    if st.button("🎯 Analyze Case", type="primary"):
        if not patient_id:
            st.error("Please enter Patient ID")
        else:
            with st.spinner("Running multi-agent analysis..."):
                # Add patient info to case data
                case_data['patient_id'] = patient_id
                case_data['cancer_type'] = cancer_type
                
                # Run analysis
                results = st.session_state.orchestrator.analyze_case(case_data, cancer_type)
                st.session_state.analysis_results = results
                st.session_state.current_case = case_data
                
                # Display results
                display_analysis_results(results)


def patient_selection_mode():
    """Patient selection from database mode"""
    st.header("👤 Select Existing Patient")
    st.markdown("Search and select patient from database")
    
    # Search patients
    search_term = st.text_input("🔍 Search by Patient ID or Name", key="patient_search")
    
    if search_term:
        patients = st.session_state.db_manager.search_patients(search_term)
    else:
        patients = st.session_state.db_manager.get_all_patients()
    
    if patients:
        st.success(f"Found {len(patients)} patient(s)")
        
        # Display patients in table
        patient_data = []
        for p in patients:
            patient_data.append({
                'Patient ID': p.patient_id,
                'Name': f"{p.first_name} {p.last_name}",
                'DOB': p.date_of_birth,
                'Gender': p.gender
            })
        
        selected_patient = st.selectbox(
            "Select Patient",
            range(len(patients)),
            format_func=lambda i: f"{patients[i].patient_id} - {patients[i].first_name} {patients[i].last_name}"
        )
        
        if selected_patient is not None:
            patient = patients[selected_patient]
            
            # Display patient details
            st.subheader("Patient Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Patient ID", patient.patient_id)
                st.metric("Name", f"{patient.first_name} {patient.last_name}")
            with col2:
                st.metric("DOB", patient.date_of_birth)
                st.metric("Gender", patient.gender)
            with col3:
                st.metric("Contact", patient.contact_phone or "N/A")
            
            # Get patient cases
            cases = st.session_state.db_manager.get_patient_cases(patient.patient_id)
            
            if cases:
                st.subheader(f"Cancer Cases ({len(cases)})")
                for case in cases:
                    with st.expander(f"{case.cancer_type.title()} Cancer - {case.diagnosis_date}"):
                        st.write(f"**Stage:** {case.stage}")
                        st.write(f"**Histology:** {case.histology}")
                        st.write(f"**Status:** {case.status}")
                        
                        if st.button(f"Analyze This Case", key=f"analyze_{case.id}"):
                            # Load case data and analyze
                            case_data = {
                                'patient_id': patient.patient_id,
                                'cancer_type': case.cancer_type,
                                'stage': case.stage,
                                'histology': case.histology,
                                'biomarkers': case.biomarkers
                            }
                            
                            with st.spinner("Running analysis..."):
                                results = st.session_state.orchestrator.analyze_case(case_data, case.cancer_type)
                                st.session_state.analysis_results = results
                                display_analysis_results(results)
            else:
                st.info("No cancer cases found for this patient")
                if st.button("➕ Add New Case"):
                    st.session_state.selected_patient = patient
                    st.rerun()
    else:
        st.info("No patients found. Add a new patient using Manual Entry mode.")


def cancer_type_info_mode():
    """Cancer type information and pipeline details"""
    st.header("🔬 Cancer Type Information")
    st.markdown("View cancer-specific pipelines and requirements")
    
    cancer_type = st.selectbox(
        "Select Cancer Type",
        Config.CANCER_TYPES,
        format_func=lambda x: x.title()
    )
    
    pipeline = st.session_state.cancer_selector.get_pipeline(cancer_type)
    
    if pipeline:
        st.subheader(f"{cancer_type.title()} Cancer Pipeline")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Required Clinical Fields")
            for field in pipeline.required_fields:
                st.markdown(f"- {field.replace('_', ' ').title()}")
        
        with col2:
            st.markdown("### Key Biomarkers")
            for biomarker in pipeline.biomarkers:
                st.markdown(f"- {biomarker}")
        
        st.markdown("---")
        st.markdown(f"### Staging System")
        st.info(f"**{pipeline.staging_system}**")
        
        # Mock treatment options
        st.markdown("### Treatment Modalities")
        mock_stage = "Stage II"
        mock_biomarkers = {}
        treatments = pipeline.get_treatment_options(mock_stage, mock_biomarkers)
        for treatment in treatments:
            st.markdown(f"- {treatment}")


def display_analysis_results(results):
    """Display comprehensive analysis results"""
    st.markdown("---")
    st.header("📊 Multi-Agent Analysis Results")
    
    # Tabs for different agents
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Summary", 
        "🎯 Staging", 
        "💊 Treatment Plan", 
        "🔬 Clinical Trials",
        "📄 Case Brief"
    ])
    
    with tab1:
        st.subheader("Clinical Summary")
        if 'clinical_summary' in results['agents']:
            summary = results['agents']['clinical_summary']
            st.markdown(summary.get('summary', 'No summary available'))
            
            if summary.get('missing_data'):
                st.warning("⚠️ Missing Information:")
                for item in summary['missing_data']:
                    st.markdown(f"- {item}")
    
    with tab2:
        st.subheader("Cancer Staging (AJCC 8th Edition)")
        if 'staging' in results['agents']:
            staging = results['agents']['staging']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Stage", staging.get('stage', 'Unknown'))
            with col2:
                st.metric("T Stage", staging.get('tnm', {}).get('T', 'Unknown'))
            with col3:
                st.metric("N Stage", staging.get('tnm', {}).get('N', 'Unknown'))
            with col4:
                st.metric("M Stage", staging.get('tnm', {}).get('M', 'Unknown'))
            
            st.markdown("**Rationale:**")
            st.info(staging.get('rationale', 'No rationale provided'))
    
    with tab3:
        st.subheader("Treatment Recommendations")
        if 'treatment' in results['agents']:
            treatment = results['agents']['treatment']
            st.markdown("**Primary Recommendation:**")
            st.success(treatment.get('primary_recommendation', 'No recommendation available'))
            
            st.markdown("**Alternative Options:**")
            for alt in treatment.get('alternatives', []):
                st.markdown(f"- {alt}")
            
            st.markdown("**Rationale:**")
            with st.expander("View detailed rationale"):
                st.markdown(treatment.get('rationale', 'No rationale provided'))
    
    with tab4:
        st.subheader("Clinical Trial Matches")
        if 'trial_matching' in results['agents']:
            trials = results['agents']['trial_matching']
            for trial in trials.get('top_matches', []):
                with st.expander(f"🔬 {trial['trial_id']} - Score: {trial['eligibility_score']:.0%}"):
                    st.markdown(f"**Title:** {trial['title']}")
                    st.markdown(f"**Location:** {trial['location']}")
                    st.markdown(f"**Eligibility Score:** {trial['eligibility_score']:.0%}")
    
    with tab5:
        st.subheader("MDT Case Brief")
        if 'synthesis' in results:
            synthesis = results['synthesis']
            
            # Generate case brief
            brief = f"""
# MDT Case Brief

**Cancer Type:** {results['cancer_type'].title()}
**Date:** {datetime.now().strftime('%Y-%m-%d')}

## Clinical Summary
{synthesis.get('summary', 'N/A')}

## Staging
**Stage:** {synthesis.get('stage', 'Unknown')}

## Recommended Treatment
{synthesis.get('recommended_treatment', 'N/A')}

## Alternative Treatments
{chr(10).join(['- ' + alt for alt in synthesis.get('alternative_treatments', [])])}

## Clinical Trials
{chr(10).join(['- ' + trial['trial_id'] + ': ' + trial['title'] for trial in synthesis.get('clinical_trials', [])])}

## Missing Information
{chr(10).join(['- ' + item for item in synthesis.get('missing_information', [])]) or 'None'}

## Confidence Level
{synthesis.get('confidence_level', 0):.0%}
"""
            
            st.markdown(brief)
            
            # Download button
            st.download_button(
                label="📥 Download Case Brief",
                data=brief,
                file_name=f"mdt_case_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )


def transcribe_audio(audio_path):
    """Transcribe audio using MedASR (placeholder)"""
    # In production, integrate actual MedASR transcription
    return "Sample transcription: Patient presents with invasive ductal carcinoma, tumor size 2.5cm, ER positive, PR positive, HER2 negative, Grade 2..."


def extract_clinical_data(transcription, cancer_type):
    """Extract structured clinical data from transcription (placeholder)"""
    # In production, use NLP to extract structured data
    return {
        'transcription': transcription,
        'cancer_type': cancer_type,
        'tumor_size': '2.5cm',
        'histology': 'Invasive Ductal Carcinoma',
        'grade': 'Grade 2'
    }


if __name__ == "__main__":
    main()
