# ⚖️ Agentic AI Litigation Workflow

### Multi-Agent Legal Automation Using LangGraph, OpenAI & Streamlit

An AI-powered litigation workflow automation prototype that uses **LangGraph's supervisor-based orchestration** to coordinate specialized agents for court filing validation, matter identification, legal research, document drafting, and litigation task management.

The application provides a **Streamlit frontend** for executing workflows, reviewing AI-generated legal analysis, and approving draft work products.

## 🚀 Key Features

- **Supervisor Agent:** Coordinates agent execution using conditional routing and workflow state.
- **Intake Agent:** Validates incoming court filing information.
- **Matter Agent:** Matches court events to existing litigation matters.
- **Precedent Agent:** Retrieves relevant internal legal documents using keyword matching.
- **Case Law Agent:** Supports optional external legal research through CourtListener.
- **Analysis Agent:** Uses OpenAI to generate preliminary legal analysis.
- **Drafting Agent:** Prepares structured legal memoranda for attorney review.
- **Task Agent:** Generates proposed litigation tasks without automatically assigning legal deadlines.
- **Human Review:** Supports attorney approval or rejection of generated work.
- **Audit Trail:** Records workflow activities and supervisor routing decisions.
- **Word Export:** Generates downloadable Microsoft Word documents.

## 🏗️ System Architecture

```text
                 Court Filing Event
                        |
                        ▼
                  Supervisor
                        |
                        ▼
                   Intake Agent
                        |
                        ▼
                   Matter Agent
                        |
                        ▼
                 Precedent Agent
                        |
                        ▼
                  Case Law Agent
                        |
                        ▼
                  Analysis Agent
                        |
                        ▼
                  Drafting Agent
                        |
                        ▼
                    Task Agent
                        |
                        ▼
                  Attorney Review
                        |
                        ▼
                Word Document Export
```

Each worker returns control to the Supervisor Agent, which determines the next eligible step based on the workflow state.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| LangGraph | Multi-agent orchestration |
| LangChain | LLM integration |
| OpenAI API | AI-powered legal analysis |
| Streamlit | Interactive frontend |
| CourtListener | External case-law research |
| JSON | Local data storage |
| python-docx | Microsoft Word generation |

## 📂 Project Structure

```text
litigation_langgraph/
├── streamlit_app.py       # Streamlit frontend
├── graph.py               # Supervisor and LangGraph workflow
├── agents/
│   ├── __init__.py
│   └── nodes.py           # Specialized agents
├── storage.py             # Local data and audit logging
├── export_docx.py         # Word document generation
├── sample_event.json      # Sample court filing
├── sample_matters.json    # Sample litigation matters
├── sample_precedents.json # Sample legal precedents
├── requirements.txt       # Python dependencies
├── .env.example           # Environment configuration
└── README.md
```

## ⚙️ Installation

**1. Clone the repository**

```bash
git clone <your-repository-url>
cd litigation_langgraph
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4.1-mini
ENABLE_COURTLISTENER=0
COURTLISTENER_TOKEN=
```

**4. Run the application**

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

## 🔄 Workflow

1. Submit a new court filing event.
2. Supervisor dispatches the Intake Agent for validation.
3. Matter Agent identifies the corresponding litigation matter.
4. Research agents retrieve internal precedents and optional external case-law leads.
5. Analysis Agent generates a preliminary legal memorandum.
6. Drafting Agent prepares attorney work product.
7. Task Agent creates proposed litigation activities.
8. Attorney reviews the results and approves or rejects the draft.

## 🔮 Future Enhancements

- Microsoft Outlook integration using Microsoft Graph API.
- iManage integration for enterprise document management.
- RAG-based semantic precedent retrieval.
- Automated court filing monitoring.
- Persistent workflow execution and enhanced human approval.

## ⚠️ Disclaimer

This project is an educational prototype, not a production-ready legal system. AI-generated analysis and legal authorities require attorney verification. The application does not automatically calculate binding court deadlines or submit court filings.

## 📌 Project Type

**Agentic AI | Multi-Agent Systems | LegalTech | LangGraph | Streamlit | LLM Orchestration**

Streamlit Cloud URL: https://litigationlanggraphsupervisorapp-mmgsfndyzyxpoob95hf7cz.streamlit.app/
