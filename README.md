# AI-Powered Interview Trainer Agent

**Problem Statement No. 22 – Interview Trainer Agent**


## 📌 Project Overview
The **Interview Trainer Agent** is a multi-agent, AI-powered system designed to prepare users for job interviews by generating tailored question sets and preparation strategies. By leveraging **Retrieval-Augmented Generation (RAG)** and **IBM Granite**, the system assesses both technical proficiency and soft skills to build candidate confidence and identify skill gaps in real-time.

## 🚀 Key Features
*   **Tailored Question Generation:** Users input their resume or job title, and the agent generates targeted questions based on identified skill gaps and experience levels.
*   **RAG Knowledge Retrieval:** Fetches actual industry expectations, HR guidelines, and behavioral scenarios from external databases to ground the AI responses.
*   **Comprehensive Assessment:** Supports both technical (coding/domain knowledge) and soft skill assessments, explicitly utilizing the STAR method for behavioral rounds.
*   **Multi-Modal & Anti-Cheat Environment:** Integrates voice-based answering (IBM Watson Speech-to-Text) and strict anti-cheat mechanisms, including disabling copy-paste and webcam focus tracking.
*   **Real-Time Feedback & Model Answers:** Provides instant scores (out of 10), highlights missing points in candidate answers, and generates ideal model answers.
*   **Dashboard & Roadmap:** Provides visual analytics (e.g., radar charts) and generates a downloadable personalized preparation roadmap based on interview performance.

## 🧠 Multi-Agent Architecture
The solution relies on a specialized multi-agent ecosystem:
1.  **Profile Agent:** Analyzes resumes, experience levels, and target job roles.
2.  **Question Agent:** Retrieves and adapts role-specific technical and behavioral questions.
3.  **Evaluation & Feedback Agent:** Analyzes answers, provides scores, highlights missing points, and generates ideal model answers.

## 🛠️ Mandatory Technology Stack
The solution is built strictly using the following infrastructure:
*   **IBM Cloud Lite Services:** For hosting, scaling, and orchestrating workflows.
*   **IBM Granite Model:** To power the core AI generation, reasoning, model answers, and natural language understanding capabilities.
*   **IBM watsonx.ai:** For secure model deployment, embeddings, and AI governance.
*   **Vector Database (FAISS/Chroma):** For storing embedded job descriptions and interview question banks.
*   **Application Backend:** Django / Django REST Framework.
*   **Computer Vision:** OpenCV and MediaPipe (for posture/liveness tracking).

## 📂 Repository Structure (Submission Requirements)
Ensure the following files are present in the repository root for the AICTE IBM SkillsBuild submission:
*   `All Agent relevant files` (Source code for Django backend, RAG pipeline, and IBM service integrations)
*   `yourproblemstatement.pdf` (The generated PDF detailing the exact problem statement)
*   `projectpresentation.pptx` (The final PowerPoint presentation containing architecture and solution details)

## ⚙️ Installation & Setup (Local Development)

**1. Clone the repository:**
```bash
git clone https://github.com/yourusername/interview-trainer-agent.git
cd interview-trainer-agent
```

**2. Create and activate a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts ctivate`
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables:**
Create a `.env` file in the root directory and add your IBM Cloud credentials:
```env
IBM_WATSONX_API_KEY=your_api_key_here
IBM_WATSONX_PROJECT_ID=your_project_id_here
IBM_SPEECH_TO_TEXT_API_KEY=your_stt_api_key
IBM_SPEECH_TO_TEXT_URL=your_stt_url
```

**5. Run Database Migrations:**
```bash
python manage.py migrate
```

**6. Start the Server:**
```bash
python manage.py runserver
```

## 📝 Usage
1. Open the web interface and upload your PDF Resume and a target Job Description.
2. Allow webcam and microphone permissions for the anti-cheat and voice-answering features.
3. Complete the 3-phase interview (Introduction, Technical, Behavioral).
4. Review your live score out of 10 and the IBM Granite-generated model answers after each question.
5. Download your personalized PDF preparation roadmap from the final dashboard.
