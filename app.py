"""
MedGemma MDT Platform - Main Streamlit Dashboard
Comprehensive MDT case preparation with voice/manual/patient selection modes
NOW SUPPORTS 8 CANCER TYPES!
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
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False


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
    
    # ========== NEW CANCER TYPES START HERE ==========
    
    elif cancer_type == "prostate":
        col1, col2 = st.columns(2)
        with col1:
            case_data['psa_level'] = st.number_input("PSA Level (ng/mL)", 0.0, 500.0, key="psa")
            case_data['gleason_score'] = st.selectbox("Gleason Score",
                ["6 (3+3)", "7 (3+4)", "7 (4+3)", "8 (4+4)", "9 (4+5)", "9 (5+4)", "10 (5+5)"],
                key="gleason")
            case_data['clinical_stage'] = st.selectbox("Clinical T Stage",
                ["T1a", "T1b", "T1c", "T2a", "T2b", "T2c", "T3a", "T3b", "T4"],
                key="prostate_t_stage")
        with col2:
            case_data['lymph_node_status'] = st.selectbox("Lymph Node Status",
                ["N0", "N1", "Unknown"],
                key="prostate_lymph_nodes")
            case_data['metastasis_status'] = st.selectbox("Metastasis Status",
                ["M0", "M1a", "M1b", "M1c", "Unknown"],
                key="prostate_mets")
            case_data['genomic_testing'] = st.selectbox("Genomic Testing",
                ["Not Done", "Oncotype DX", "Decipher", "Prolaris", "Other"],
                key="prostate_genomic")
            case_data['brca_status'] = st.selectbox("BRCA1/2 Status",
                ["Not Tested", "Negative", "BRCA1 Positive", "BRCA2 Positive"],
                key="prostate_brca")
    
    elif cancer_type == "ovarian":
        col1, col2 = st.columns(2)
        with col1:
            case_data['histology'] = st.selectbox("Histology",
                ["High-Grade Serous", "Low-Grade Serous", "Endometrioid", "Clear Cell", "Mucinous", "Other"],
                key="ovarian_histology")
            case_data['figo_stage'] = st.selectbox("FIGO Stage",
                ["IA", "IB", "IC1", "IC2", "IC3", "IIA", "IIB", "IIIA1", "IIIA2", "IIIB", "IIIC", "IVA", "IVB"],
                key="figo_stage")
            case_data['ca125_level'] = st.number_input("CA-125 Level (U/mL)", 0.0, 10000.0, key="ca125")
        with col2:
            case_data['residual_disease'] = st.selectbox("Residual Disease After Surgery",
                ["No Residual", "<1 cm", "1-2 cm", ">2 cm", "Not Applicable"],
                key="residual_disease")
            case_data['brca_status'] = st.selectbox("BRCA1/2 Status",
                ["Not Tested", "Negative", "BRCA1 Positive", "BRCA2 Positive"],
                key="ovarian_brca")
            case_data['hrd_status'] = st.selectbox("HRD Status",
                ["Not Tested", "HRD Positive", "HRD Negative"],
                key="hrd")
            case_data['platinum_sensitivity'] = st.selectbox("Platinum Sensitivity",
                ["Not Applicable", "Sensitive", "Resistant", "Refractory"],
                key="platinum")
    
    elif cancer_type == "cervical":
        col1, col2 = st.columns(2)
        with col1:
            case_data['histology'] = st.selectbox("Histology",
                ["Squamous Cell Carcinoma", "Adenocarcinoma", "Adenosquamous", "Other"],
                key="cervical_histology")
            case_data['figo_stage'] = st.selectbox("FIGO Stage (2018)",
                ["IA1", "IA2", "IB1", "IB2", "IB3", "IIA1", "IIA2", "IIB", "IIIA", "IIIB", "IIIC1", "IIIC2", "IVA", "IVB"],
                key="cervical_figo")
            case_data['tumor_size'] = st.text_input("Tumor Size (cm)", key="cervical_tumor_size")
        with col2:
            case_data['hpv_status'] = st.selectbox("HPV Status",
                ["Positive", "Negative", "Unknown"],
                key="hpv")
            case_data['lymph_node_status'] = st.selectbox("Lymph Node Involvement",
                ["Negative", "Pelvic Nodes", "Para-aortic Nodes", "Both", "Unknown"],
                key="cervical_lymph_nodes")
            case_data['parametrial_involvement'] = st.selectbox("Parametrial Involvement",
                ["No", "Yes", "Unknown"],
                key="parametrial")
            case_data['pdl1_expression'] = st.number_input("PD-L1 CPS Score", 0, 100, key="cervical_pdl1")
    
    elif cancer_type == "uterine":
        col1, col2 = st.columns(2)
        with col1:
            case_data['histology'] = st.selectbox("Histology",
                ["Endometrioid", "Serous", "Clear Cell", "Carcinosarcoma", "Mixed", "Other"],
                key="uterine_histology")
            case_data['figo_stage'] = st.selectbox("FIGO Stage (2023)",
                ["IA", "IB", "II", "IIIA", "IIIB", "IIIC1", "IIIC2", "IVA", "IVB"],
                key="uterine_figo")
            case_data['grade'] = st.selectbox("Grade",
                ["Grade 1", "Grade 2", "Grade 3"],
                key="uterine_grade")
        with col2:
            case_data['molecular_classification'] = st.selectbox("Molecular Classification (ProMisE)",
                ["Not Done", "POLE Mutated", "MMR Deficient", "p53 Abnormal", "NSMP"],
                key="molecular_class")
            case_data['msi_status'] = st.selectbox("MSI/MMR Status",
                ["Not Tested", "MSI-H/dMMR", "MSS/pMMR"],
                key="uterine_msi")
            case_data['myometrial_invasion'] = st.selectbox("Myometrial Invasion",
                ["<50%", "≥50%", "Unknown"],
                key="myometrial")
            case_data['lymphovascular_invasion'] = st.selectbox("Lymphovascular Invasion",
                ["Absent", "Present", "Unknown"],
                key="lvsi")
    
    elif cancer_type == "esophageal":
        col1, col2 = st.columns(2)
        with col1:
            case_data['histology'] = st.selectbox("Histology",
                ["Adenocarcinoma", "Squamous Cell Carcinoma", "Other"],
                key="esoph_histology")
            case_data['tumor_location'] = st.selectbox("Tumor Location",
                ["Upper Third", "Middle Third", "Lower Third", "GE Junction"],
                key="esoph_location")
            case_data['clinical_stage'] = st.selectbox("Clinical T Stage",
                ["T1a", "T1b", "T2", "T3", "T4a", "T4b"],
                key="esoph_t_stage")
        with col2:
            case_data['lymph_node_status'] = st.selectbox("Lymph Node Status",
                ["N0", "N1", "N2", "N3", "Unknown"],
                key="esoph_lymph_nodes")
            case_data['metastasis_status'] = st.selectbox("Metastasis Status",
                ["M0", "M1", "Unknown"],
                key="esoph_mets")
            case_data['her2_status'] = st.selectbox("HER2 Status (Adenocarcinoma)",
                ["Not Tested", "Positive", "Negative"],
                key="esoph_her2")
            case_data['pdl1_cps'] = st.number_input("PD-L1 CPS Score", 0, 100, key="esoph_pdl1")
    
    # ========== NEW CANCER TYPES END HERE ==========
    
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
        # Display patients in a table
        st.subheader(f"Found {len(patients)} patient(s)")
        
        for patient in patients:
            with st.expander(f"👤 {patient['first_name']} {patient['last_name']} - {patient['patient_id']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Patient ID:** {patient['patient_id']}")
                    st.markdown(f"**Name:** {patient['first_name']} {patient['last_name']}")
                with col2:
                    st.markdown(f"**DOB:** {patient.get('dob', 'N/A')}")
                    st.markdown(f"**Gender:** {patient.get('gender', 'N/A')}")
                with col3:
                    st.markdown(f"**Cancer Type:** {patient.get('cancer_type', 'N/A').title()}")
                    st.markdown(f"**Diagnosis Date:** {patient.get('diagnosis_date', 'N/A')}")
                
                if st.button(f"Select Patient {patient['patient_id']}", key=f"select_{patient['patient_id']}"):
                    st.session_state.current_case = patient
                    st.success(f"Selected patient: {patient['first_name']} {patient['last_name']}")
                    
                    # Run analysis for selected patient
                    with st.spinner("Running multi-agent analysis..."):
                        results = st.session_state.orchestrator.analyze_case(
                            patient,
                            patient.get('cancer_type', 'breast')
                        )
                        st.session_state.analysis_results = results
                        display_analysis_results(results)
    else:
        st.info("No patients found. Add patients using Manual Entry mode.")


def cancer_type_info_mode():
    """Display cancer type information"""
    st.header("🔬 Cancer Type Information")
    st.markdown("View supported cancer types and their clinical parameters")
    
    cancer_type = st.selectbox(
        "Select Cancer Type",
        Config.CANCER_TYPES,
        format_func=lambda x: x.title(),
        key="info_cancer_type"
    )
    
    pipeline = st.session_state.cancer_selector.get_pipeline(cancer_type)
    
    st.subheader(f"{cancer_type.title()} Cancer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Required Clinical Fields")
        if hasattr(pipeline, 'required_fields'):
            for field in pipeline.required_fields:
                st.markdown(f"- {field.replace('_', ' ').title()}")
        else:
            st.info("Field information not available")
    
    with col2:
        st.markdown("### Key Biomarkers")
        if hasattr(pipeline, 'biomarkers'):
            for biomarker in pipeline.biomarkers:
                st.markdown(f"- {biomarker}")
        else:
            st.info("Biomarker information not available")
    
    st.markdown("---")
    st.markdown("### Staging System")
    if hasattr(pipeline, 'staging_system'):
        st.info(pipeline.staging_system)
    else:
        st.info("Staging information not available")


def display_analysis_results(results):
    """Display multi-agent analysis results"""
    st.markdown("---")
    st.header("📊 Multi-Agent Analysis Results")
    
    # Edit mode toggle
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("✏️ Edit Results" if not st.session_state.edit_mode else "💾 Save Changes"):
            st.session_state.edit_mode = not st.session_state.edit_mode
            st.rerun()
    
    # Create tabs for different analysis components
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Summary",
        "🎯 Staging",
        "💊 Treatment Plan",
        "🔬 Clinical Trials",
        "📚 References",
        "📋 Case Brief"
    ])
    
    with tab1:
        st.subheader("Clinical Summary")
        if 'agents' in results and 'clinical_summary' in results['agents']:
            summary_data = results['agents']['clinical_summary']
            
            if st.session_state.edit_mode:
                edited_summary = st.text_area(
                    "Edit Summary",
                    summary_data.get('summary', ''),
                    height=200,
                    key="edit_summary"
                )
                summary_data['summary'] = edited_summary
            else:
                st.markdown(summary_data.get('summary', 'No summary available'))
            
            st.markdown("---")
            st.markdown("**Key Findings:**")
            findings = summary_data.get('key_findings', [])
            if findings:
                for finding in findings:
                    st.markdown(f"- {finding}")
            else:
                st.info("No key findings identified")
        else:
            st.info("Clinical summary not available")
    
    with tab2:
        st.subheader("Cancer Staging (AJCC 8th Edition)")
        if 'agents' in results and 'staging' in results['agents']:
            staging_data = results['agents']['staging']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Stage", staging_data.get('stage', 'Unknown'))
            with col2:
                st.metric("T Stage", staging_data.get('tnm', {}).get('T', 'Unknown'))
            with col3:
                st.metric("N Stage", staging_data.get('tnm', {}).get('N', 'Unknown'))
            with col4:
                st.metric("M Stage", staging_data.get('tnm', {}).get('M', 'Unknown'))
            
            st.markdown("---")
            st.markdown("**Rationale:**")
            
            if st.session_state.edit_mode:
                edited_rationale = st.text_area(
                    "Edit Staging Rationale",
                    staging_data.get('rationale', ''),
                    height=150,
                    key="edit_staging_rationale"
                )
                staging_data['rationale'] = edited_rationale
            else:
                st.markdown(staging_data.get('rationale', 'No rationale provided'))
        else:
            st.info("Staging information not available")
    
    with tab3:
        st.subheader("Treatment Plan")
        if 'agents' in results and 'treatment' in results['agents']:
            treatment_data = results['agents']['treatment']
            
            st.markdown("### Primary Recommendation")
            if st.session_state.edit_mode:
                edited_primary = st.text_area(
                    "Edit Primary Recommendation",
                    treatment_data.get('primary_recommendation', ''),
                    height=100,
                    key="edit_primary_treatment"
                )
                treatment_data['primary_recommendation'] = edited_primary
            else:
                st.markdown(treatment_data.get('primary_recommendation', 'No recommendation available'))
            
            st.markdown("---")
            st.markdown("### Alternative Treatments")
            alternatives = treatment_data.get('alternatives', [])
            if alternatives:
                for i, alt in enumerate(alternatives, 1):
                    st.markdown(f"{i}. {alt}")
            else:
                st.info("No alternative treatments identified")
            
            st.markdown("---")
            st.markdown("**Rationale:**")
            if st.session_state.edit_mode:
                edited_treatment_rationale = st.text_area(
                    "Edit Treatment Rationale",
                    treatment_data.get('rationale', ''),
                    height=150,
                    key="edit_treatment_rationale"
                )
                treatment_data['rationale'] = edited_treatment_rationale
            else:
                st.markdown(treatment_data.get('rationale', 'No rationale provided'))
        else:
            st.info("Treatment plan not available")
    
    with tab4:
        st.subheader("Clinical Trial Matches")
        if 'trial_matching' in results.get('agents', {}):
            trial_data = results['agents']['trial_matching']
            trials = trial_data.get('matching_trials', [])
            
            if trials:
                for trial in trials:
                    with st.expander(f"🔬 {trial.get('trial_id', 'N/A')} - {trial.get('title', 'Untitled')} (Eligibility: {trial.get('eligibility_score', 0):.0%})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Phase:** {trial.get('phase', 'N/A')}")
                            st.markdown(f"**Status:** {trial.get('status', 'N/A')}")
                        with col2:
                            st.markdown(f"**Location:** {trial.get('location', 'N/A')}")
                            st.markdown(f"**Eligibility Score:** {trial.get('eligibility_score', 0):.0%}")
                        
                        if st.session_state.edit_mode:
                            st.markdown("---")
                            st.markdown("*Trial details can be edited in the database*")
            else:
                st.info("No matching clinical trials found for this case.")
        else:
            st.info("Clinical trial matching data not available.")
    
    with tab5:
        st.subheader("📚 References")
        if 'synthesis' in results and 'references' in results['synthesis']:
            references = results['synthesis']['references']
            
            if st.session_state.edit_mode:
                st.markdown("**Edit References (one per line):**")
                references_text = '\n'.join(references)
                edited_references = st.text_area(
                    "References",
                    references_text,
                    height=200,
                    key="edit_references"
                )
                results['synthesis']['references'] = [ref.strip() for ref in edited_references.split('\n') if ref.strip()]
            else:
                if references:
                    for i, ref in enumerate(references, 1):
                        st.markdown(f"{i}. {ref}")
                else:
                    st.info("No references available")
        else:
            st.info("References not available")
    
    with tab6:
        st.subheader("MDT Case Brief")
        if 'synthesis' in results:
            synthesis = results['synthesis']
            
            # Generate case brief
            brief = f"""# MDT Case Brief

**Cancer Type:** {results.get('cancer_type', 'N/A').title()}
**Date:** {datetime.now().strftime('%Y-%m-%d')}

## Clinical Summary
{synthesis.get('summary', 'N/A')}

## Staging
**Stage:** {synthesis.get('stage', 'Unknown')}

Here's the reasoning:

The key information pointing to {synthesis.get('stage', 'Unknown')} is:

{synthesis.get('summary', 'Clinical analysis provided above')}

## Recommended Treatment
{synthesis.get('recommended_treatment', 'N/A')}

## Alternative Treatments
{chr(10).join(['- ' + alt for alt in synthesis.get('alternative_treatments', [])])}

## Clinical Trials
{chr(10).join(['- ' + trial.get('trial_id', 'N/A') + ': ' + trial.get('title', 'N/A') for trial in synthesis.get('clinical_trials', [])])}

## Missing Information
{chr(10).join(['- ' + item for item in synthesis.get('missing_information', [])]) or 'None'}

## References
{chr(10).join([f'{i}. {ref}' for i, ref in enumerate(synthesis.get('references', []), 1)])}

## Confidence Level
{synthesis.get('confidence_level', 0):.0%}
"""
            
            if st.session_state.edit_mode:
                edited_brief = st.text_area("Edit Case Brief", brief, height=600, key="edit_brief")
                brief = edited_brief
            else:
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
