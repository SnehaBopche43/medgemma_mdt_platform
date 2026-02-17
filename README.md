# MedGemma MDT Platform: A Multi-Agent AI for Advanced Cancer Care

![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30.0-red.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

> A breakthrough, production-ready AI platform designed to revolutionize Multidisciplinary Tumor Board (MDT) meetings. This system integrates Google's latest medical AI models (MedASR, MedGemma) with a sophisticated **multi-agent architecture** inspired by leading research from Oxford University, Mount Sinai, and AI-MDT China. It provides a complete, safety-first solution for clinical voice intelligence, automated case synthesis, evidence-based decision support, and clinical trial matching.

---

## 🏆 Key Features

| Feature | Description | Competitive Impact |
| --- | --- | --- |
| 🎤 **Voice-to-Brief** | Go from raw audio recording to a structured MDT case brief in minutes. Uses MedASR for transcription and NLP for data extraction. | **Efficiency** |
| 🧠 **Multi-Agent AI** | A team of specialized AI agents (Clinical Summary, Staging, Treatment, Trial Matching) collaborate to analyze cases, reducing errors and providing cross-validated insights. | **Accuracy & Safety** |
| ⚖️ **Clinical Trial Matching** | Automatically matches patients to relevant clinical trials from ClinicalTrials.gov using a sophisticated scoring algorithm, addressing healthcare equity. | **Equity & Access** |
| 📚 **Evidence Knowledge Graph** | Every recommendation is backed by an evidence knowledge graph that auto-updates from NCCN, ASCO, and PubMed, ensuring clinical trust and guideline concordance. | **Trust & Compliance** |
| ⚠️ **Missing Info Detection** | Intelligently identifies and flags missing critical data needed for accurate staging and treatment planning, reducing MDT postponements. | **Practicality** |
| 📈 **Longitudinal Timeline** | Tracks patient journey visually, enabling AI-powered trend detection for tumor response and treatment toxicity. | **Predictive Insights** |
| 🏥 **Multi-Cancer Pipelines** | Includes specialized, end-to-end pipelines for **Breast, Lung, and Colorectal Cancer**, each with unique data requirements and treatment logic. | **Scalability** |
| 🔒 **Safety & Compliance** | Features a robust patient database with audit trails, HITL approval workflows, and a design centered on HIPAA compliance. | **Security** |

---

## 🏗️ System Architecture

The platform uses a multi-agent system orchestrated to provide a comprehensive analysis, which is then presented in a user-friendly Streamlit dashboard.

```
┌─────────────────────────────────────────┐
│        Streamlit Dashboard (UI)          │
│  (Voice / Manual / Patient Selection)    │
└─────────────────────────────────────────┘
      ▲                           │
      │ (Results)                 │ (Case Data)
      ▼                           ▼
┌─────────────────────────────────────────┐
│         Multi-Agent Orchestrator         │
└─────────────────────────────────────────┘
      │               │              │
┌─────┼───────────────┼──────────────┼─────┐
│     │               │              │     │
▼     ▼               ▼              ▼     ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ Clinical  │ │  Staging  │ │ Treatment │ │  Trial    │
│  Summary  │ │   Agent   │ │   Agent   │ │ Matching  │
│   Agent   │ │           │ │           │ │   Agent   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
      │               │              │
      ▼               ▼              ▼
┌─────────────────────────────────────────┐
│      Evidence Knowledge Graph & DB       │
│ (NCCN, PubMed, ClinicalTrials.gov, etc)  │
└─────────────────────────────────────────┘
```

---

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/SnehaBopche43/medgemma_mdt_platform.git
    cd medgemma_mdt_platform
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file from the `.env.example` template and add your API keys (e.g., for Google Generative AI).
    ```bash
    cp .env.example .env
    # now edit .env with your keys
    ```

---

## 🚀 Usage

To run the main dashboard:

```bash
streamlit run app.py
```

Once the app is running, you can:
1.  **Select an Input Mode** from the sidebar (Voice, Manual, or Patient Selection).
2.  **Provide the case data** through the selected interface.
3.  **Click "Analyze"** to trigger the multi-agent system.
4.  **Review the comprehensive results** across the different tabs.
5.  **Download the final MDT Case Brief** for your records.

---

## 🔮 Future Enhancements

-   **Federated Learning**: Implement federated learning to train models across multiple institutions without sharing sensitive patient data, improving model accuracy and generalizability.
-   **Multi-Modal Data Integration**: Incorporate analysis of medical imaging (e.g., pathology slides, CT scans) alongside text-based reports.
-   **Real-Time Collaboration**: Add features for real-time collaboration between MDT members within the platform.

---

## 📜 License

This project is licensed under the **Apache License 2.0**. See the `LICENSE` file for details.

---

## 🙏 Acknowledgments

-   This project was developed by **Sneha Bopche** for the **Building Innovative Tools with AI** competition.
-   Special thanks to Google for providing the groundbreaking **MedASR** and **MedGemma** models.
-   This work is inspired by the pioneering research from Oxford University's TrustedMDT, the AI-MDT platform in China, and Mount Sinai's clinical trial matching system.
