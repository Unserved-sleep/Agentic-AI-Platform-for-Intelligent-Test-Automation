import streamlit as st
import requests
import json
import pandas as pd
from pathlib import Path
import sys

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from ingestion.parser import DocumentParser
from rag.pipeline import RAGPipeline
from agents.requirement_agent import RequirementAgent
from agents.test_scenario_agent import TestScenarioAgent
from agents.script_agent import PlaywrightScriptAgent
from agents.failure_agent import FailureAnalysisAgent
from agents.self_healing_agent import SelfHealingAgent
from agents.report_agent import ReportAgent
from execution.runner import execution_runner
from orchestration.graph import orchestrator
from database.connection import ensure_database_exists
from database.assertions import DBAssertionHelper
from database.persistence import DBPersistenceHelper
from shared.schemas import TestScenario

# Ensure PostgreSQL database and tables exist on dashboard startup
try:
    ensure_database_exists()
except Exception as e:
    pass

st.set_page_config(
    page_title="Agentic AI Test Automation Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(120deg, #3b82f6, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Agentic AI Platform for Intelligent Test Automation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Live SauceDemo UI Automation & FastAPI Backend API Testing with PostgreSQL DB Assertions</div>', unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/isometric/100/bot.png", width=70)
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Select Module:",
    [
        "📊 Dashboard Overview",
        "📄 Requirement Ingestion & RAG",
        "🧪 Test Scenario Generator",
        "💻 Playwright Script Studio",
        "🚀 Execution & Self-Healing",
        "📈 Analytics & Reports"
    ]
)

# Initialize Session State
if "parsed_req" not in st.session_state:
    st.session_state.parsed_req = None
if "req_analysis" not in st.session_state:
    st.session_state.req_analysis = None
if "scenarios" not in st.session_state:
    st.session_state.scenarios = []
if "scripts" not in st.session_state:
    st.session_state.scripts = []
if "execution_results" not in st.session_state:
    st.session_state.execution_results = []
if "current_doc_name" not in st.session_state:
    st.session_state.current_doc_name = None
if "last_uploaded_filename" not in st.session_state:
    st.session_state.last_uploaded_filename = None
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = RAGPipeline()


# --- Module 1: Dashboard Overview ---
if menu == "📊 Dashboard Overview":
    st.subheader("System Architecture & Live Services Status")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Database", "PostgreSQL 17", delta="agentic_test_db")
    with col2:
        st.metric("LLM Provider", "Groq AI", delta="Llama 3.3 70B")
    with col3:
        st.metric("UI Target", "SauceDemo", delta="saucedemo.com")
    with col4:
        st.metric("Self-Healing", "LangGraph", delta="Active")

    st.divider()

    st.subheader("🗄️ Live PostgreSQL Database Repository Summary")
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    d_col1.metric("Ingested Documents", DBPersistenceHelper.get_documents_count())
    d_col2.metric("Saved Scenarios", DBPersistenceHelper.get_scenarios_count())
    d_col3.metric("Saved Scripts", DBPersistenceHelper.get_scripts_count())
    
    # Executions Count
    from database.connection import SessionLocal
    from database.models import ExecutionModel
    db = SessionLocal()
    exec_count = db.query(ExecutionModel).count()
    db.close()
    d_col4.metric("Executions Logged", exec_count)

    st.info("""
    **Playwright Execution & Tracing Highlights**:
    - 🌐 **UI Web Automation**: Executes live against [https://www.saucedemo.com/](https://www.saucedemo.com/). Opens actual browser window!
    - 📸 **Screenshots**: Automatically captured and saved in `artifacts/screenshots/`.
    - 🔍 **Traces**: Playwright zip traces stored in `artifacts/traces/`.
    - 🎥 **Video Recording**: Recorded Playwright browser video saved in `artifacts/videos/`.
    - ⚡ **Backend API Testing**: Executed against FastAPI backend endpoints with read-only PostgreSQL DB state assertions.
    - 🗄️ **PostgreSQL Persistence**: Ingested documents, generated scenarios, scripts, execution records, and self-healing audit logs are automatically persisted to PostgreSQL.
    """)

    st.subheader("Sample Database Verification Check")
    if st.button("Run Live PostgreSQL Connection Assertion"):
        res1 = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
        res2 = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
        st.json({"claim_status_check": res1, "payout_record_check": res2})


# --- Module 2: Requirement Ingestion & RAG ---
elif menu == "📄 Requirement Ingestion & RAG":
    st.subheader("Document Ingestion & Context Engineering")
    
    uploaded_file = st.file_uploader("Upload Business Requirement Document (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        if st.button("Ingest Sample Claims BRD Document"):
            # Clear previous document-specific session state
            st.session_state.scenarios = []
            st.session_state.scripts = []
            st.session_state.execution_results = []
            
            parsed = DocumentParser.parse_file("docs/claims_brd.md")
            st.session_state.rag_pipeline.ingest_document(parsed.document_name, parsed.raw_text, replace_existing=True)
            
            req_agent = RequirementAgent()
            analysis = req_agent.process_requirement(parsed, rag_pipeline=st.session_state.rag_pipeline)
            
            st.session_state.parsed_req = parsed
            st.session_state.req_analysis = analysis
            st.session_state.current_doc_name = "claims_brd.md"
            if uploaded_file:
                st.session_state.last_uploaded_filename = uploaded_file.name
            
            st.success("Successfully ingested sample BRD document and built RAG vector index!")

    if uploaded_file:
        if st.session_state.get("last_uploaded_filename") != uploaded_file.name:
            save_path = BASE_DIR / "docs" / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            parsed = DocumentParser.parse_file(str(save_path))
            st.session_state.rag_pipeline.ingest_document(parsed.document_name, parsed.raw_text, replace_existing=True)
            
            req_agent = RequirementAgent()
            analysis = req_agent.process_requirement(parsed, rag_pipeline=st.session_state.rag_pipeline)
            
            st.session_state.parsed_req = parsed
            st.session_state.req_analysis = analysis
            st.session_state.current_doc_name = uploaded_file.name
            st.session_state.last_uploaded_filename = uploaded_file.name
            st.session_state.scenarios = []
            st.session_state.scripts = []
            st.session_state.execution_results = []
            
            st.success(f"Uploaded, parsed, and analyzed {uploaded_file.name}")

    if st.session_state.parsed_req:
        st.markdown(f"#### 📜 Document: `{st.session_state.parsed_req.document_name}`")
        st.text_area("Extracted Requirements Text", st.session_state.parsed_req.raw_text, height=200)
        
        if st.session_state.req_analysis:
            st.markdown("#### 🎯 Domain Analysis")
            st.json(st.session_state.req_analysis)


# --- Module 3: Test Scenario Generator ---
elif menu == "🧪 Test Scenario Generator":
    st.subheader("AI Test Scenario Matrix Generation (SauceDemo UI + FastAPI API)")
    
    if st.button("✨ Generate Test Scenarios (UI + API)"):
        agent = TestScenarioAgent()
        context = st.session_state.req_analysis or (
            {
                "title": st.session_state.parsed_req.title,
                "document_name": st.session_state.parsed_req.document_name,
                "workflows": st.session_state.parsed_req.workflows,
                "validations": st.session_state.parsed_req.validations,
                "api_endpoints": st.session_state.parsed_req.api_endpoints
            } if st.session_state.parsed_req else {}
        )
        scenarios = agent.generate_scenarios(context)
        st.session_state.scenarios = scenarios
        st.success(f"Generated {len(scenarios)} test scenarios!")

    if st.session_state.scenarios:
        for idx, sc in enumerate(st.session_state.scenarios):
            with st.expander(f"{sc.id}: {sc.title} ({sc.category.upper()} - {sc.test_type})"):
                st.write(f"**Description**: {sc.description}")
                st.write(f"**Expected Result**: {sc.expected_result}")
                st.write("**Steps**:")
                for step in sc.steps:
                    st.markdown(f"- {step}")
                if sc.db_assertions:
                    st.info(f"**PostgreSQL Assertions**: {sc.db_assertions}")


# --- Module 4: Playwright Script Studio ---
elif menu == "💻 Playwright Script Studio":
    st.subheader("Playwright Code Generator (SauceDemo POM, Video & Tracing)")
    
    if st.button("🔨 Generate Playwright Python Test Scripts"):
        if not st.session_state.scenarios:
            sc_agent = TestScenarioAgent()
            st.session_state.scenarios = sc_agent.generate_scenarios({})
            
        script_agent = PlaywrightScriptAgent()
        generated_list = []
        for sc in st.session_state.scenarios:
            script_obj = script_agent.generate_script(sc)
            generated_list.append(script_obj)
        st.session_state.scripts = generated_list
        st.success(f"Generated {len(generated_list)} Playwright Python test scripts!")

    if st.session_state.scripts:
        script_names = [f"{s.scenario_id}: {s.title}" for s in st.session_state.scripts]
        selected_idx = st.selectbox("Select Script to View Code", range(len(script_names)), format_func=lambda i: script_names[i])
        
        sel_script = st.session_state.scripts[selected_idx]
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**File Path**: `{sel_script.file_path}`")
            st.markdown(f"**Type**: `{sel_script.test_type}` | **DB Assertions**: `{sel_script.db_checks_included}`")
            st.code(sel_script.script_code, language="python")
        with col2:
            st.markdown("**Page Object Model Structure**")
            if sel_script.page_object_code:
                st.code(sel_script.page_object_code, language="python")
            else:
                st.info("API Direct Request Script (No browser POM required).")


# --- Module 5: Execution & Self-Healing ---
elif menu == "🚀 Execution & Self-Healing":
    st.subheader("Browser Execution & Playwright Artifact Studio")
    
    col_x, col_y = st.columns([1, 1])
    
    with col_x:
        if st.button("▶️ Run Playwright UI & API Test Suite"):
            if not st.session_state.scripts:
                sc_agent = TestScenarioAgent()
                scs = sc_agent.generate_scenarios({})
                script_agent = PlaywrightScriptAgent()
                st.session_state.scripts = [script_agent.generate_script(s) for s in scs]

            results = []
            progress_bar = st.progress(0)
            for idx, scr in enumerate(st.session_state.scripts):
                res = execution_runner.run_test(scr.file_path, test_type=scr.test_type)
                results.append(res)
                progress_bar.progress((idx + 1) / len(st.session_state.scripts))
                
            st.session_state.execution_results = results
            st.success("Test execution completed!")

    with col_y:
        if st.button("⚡ Run Full Orchestrated LangGraph Loop"):
            with st.spinner("Running LangGraph Planner -> Generate -> Execute -> Observe -> Repair Loop..."):
                output = orchestrator.run_workflow(st.session_state.req_analysis or {})
                st.success("LangGraph Loop Finished!")
                st.json(output)

    if st.session_state.execution_results:
        st.markdown("### Execution Results & Artifact Viewer")
        for res in st.session_state.execution_results:
            status_color = "🟢" if res.status == "PASSED" else "🔴"
            with st.expander(f"{status_color} Run {res.run_id} - {res.test_type} ({res.status}) - {res.duration_seconds}s"):
                st.write(f"**Script**: `{res.script_path}`")
                
                screenshot_file = getattr(res, "screenshot_path", None)
                trace_file = getattr(res, "trace_path", None)
                video_file = getattr(res, "video_path", None)

                # Render Captured Playwright Artifacts
                art_col1, art_col2, art_col3 = st.columns(3)
                
                with art_col1:
                    st.markdown("**📸 Screenshot Artifact**")
                    if screenshot_file and Path(screenshot_file).exists():
                        st.image(screenshot_file, caption=Path(screenshot_file).name, use_container_width=True)
                    else:
                        st.caption("No screenshot captured.")

                with art_col2:
                    st.markdown("**🔍 Playwright Trace Zip**")
                    if trace_file and Path(trace_file).exists():
                        with open(trace_file, "rb") as tf:
                            st.download_button(
                                label=f"📥 Download Trace ({Path(trace_file).name})",
                                data=tf,
                                file_name=Path(trace_file).name,
                                mime="application/zip",
                                key=f"trace_{res.run_id}"
                            )
                    else:
                        st.caption("No trace file captured.")

                with art_col3:
                    st.markdown("**🎥 Recorded Video**")
                    if video_file and Path(video_file).exists():
                        st.video(video_file)
                        with open(video_file, "rb") as vf:
                            st.download_button(
                                label=f"📥 Download Video",
                                data=vf,
                                file_name=Path(video_file).name,
                                mime="video/webm",
                                key=f"video_{res.run_id}"
                            )
                    else:
                        st.caption("No video recording available.")

                st.divider()
                st.text_area("Console Stdout", res.stdout, height=100, key=f"out_{res.run_id}")
                if res.stderr:
                    st.text_area("Console Stderr", res.stderr, height=100, key=f"err_{res.run_id}")
                if res.db_assertion_results:
                    st.markdown("**PostgreSQL DB Assertion Outcomes:**")
                    st.json(res.db_assertion_results)
                
                # Self-Healing Action Button for Failed Tests
                if res.status in ["FAILED", "ERROR"]:
                    if st.button(f"🛠️ Trigger Self-Healing for {res.run_id}", key=f"heal_{res.run_id}"):
                        healer = SelfHealingAgent()
                        heal_res = healer.heal_test(res, execution_runner)
                        st.markdown("### 🩹 Self-Healing Repair Diagnostic")
                        st.write(f"**Category**: `{heal_res.failure_category}`")
                        st.write(f"**Patch Explanation**: {heal_res.patch_explanation}")
                        st.code(heal_res.repaired_code, language="python")
                        if heal_res.retry_execution_result:
                            st.success(f"Retry Execution Status: {heal_res.retry_execution_result.status}")


# --- Module 6: Analytics & Reports ---
elif menu == "📈 Analytics & Reports":
    st.subheader("QA Analytics & Executive Reports")
    
    rep_agent = ReportAgent()
    report = rep_agent.generate_report()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Executions", report.total_tests)
    c2.metric("Pass Rate", f"{report.pass_rate_percentage}%")
    c3.metric("UI Tests Passed", f"{report.ui_passed} / {report.ui_tests_count}")
    c4.metric("API Tests Passed", f"{report.api_passed} / {report.api_tests_count}")

    st.divider()

    st.markdown("### AI QA Recommendations")
    for rec in report.recommendations:
        st.info(f"💡 {rec}")

    st.markdown("### 🗄️ PostgreSQL Database Inspector")
    tab_exec, tab_heal, tab_doc, tab_scen, tab_scr, tab_claim = st.tabs([
        "🚀 Executions",
        "🩹 Healing Logs",
        "📄 Documents",
        "🧪 Scenarios",
        "💻 Scripts",
        "🏥 Claims & Payouts"
    ])

    with tab_exec:
        if report.execution_history:
            data = []
            for r in report.execution_history:
                shot_name = Path(r.screenshot_path).name if getattr(r, "screenshot_path", None) else "None"
                trace_name = Path(r.trace_path).name if getattr(r, "trace_path", None) else "None"
                vid_name = Path(r.video_path).name if getattr(r, "video_path", None) else "None"
                
                data.append({
                    "Run ID": r.run_id,
                    "Type": r.test_type,
                    "Status": r.status,
                    "Duration (s)": r.duration_seconds,
                    "Screenshot": shot_name,
                    "Trace Zip": trace_name,
                    "Video": vid_name,
                    "Timestamp": r.timestamp
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No execution records found in PostgreSQL yet.")

    with tab_heal:
        from database.connection import SessionLocal
        from database.models import HealingLogModel, Claim, Payout
        db = SessionLocal()
        try:
            h_logs = db.query(HealingLogModel).order_by(HealingLogModel.created_at.desc()).all()
            if h_logs:
                h_data = [{
                    "ID": h.id,
                    "Run ID": h.run_id,
                    "Failure Category": h.failure_category,
                    "Patch Explanation": h.patch_explanation,
                    "Healed Successfully": h.healed_successfully,
                    "Timestamp": str(h.created_at)
                } for h in h_logs]
                st.dataframe(pd.DataFrame(h_data), use_container_width=True)
            else:
                st.info("No self-healing logs recorded in PostgreSQL yet.")
        finally:
            db.close()

    with tab_doc:
        docs = DBPersistenceHelper.get_all_documents()
        if docs:
            st.dataframe(pd.DataFrame(docs), use_container_width=True)
        else:
            st.info("No document records saved in PostgreSQL yet.")

    with tab_scen:
        scs = DBPersistenceHelper.get_all_scenarios()
        if scs:
            st.dataframe(pd.DataFrame(scs), use_container_width=True)
        else:
            st.info("No scenario records saved in PostgreSQL yet.")

    with tab_scr:
        scrs = DBPersistenceHelper.get_all_scripts()
        if scrs:
            st.dataframe(pd.DataFrame(scrs), use_container_width=True)
        else:
            st.info("No script records saved in PostgreSQL yet.")

    with tab_claim:
        db = SessionLocal()
        try:
            claims = db.query(Claim).all()
            payouts = db.query(Payout).all()
            st.markdown("**Claims Table:**")
            if claims:
                st.dataframe(pd.DataFrame([{
                    "ID": c.id,
                    "Claim Number": c.claim_number,
                    "Policy Number": c.policy_number,
                    "Claimant Name": c.claimant_name,
                    "Amount": c.claim_amount,
                    "Status": c.status,
                    "Created At": str(c.created_at)
                } for c in claims]), use_container_width=True)
            st.markdown("**Payouts Table:**")
            if payouts:
                st.dataframe(pd.DataFrame([{
                    "ID": p.id,
                    "Claim ID": p.claim_id,
                    "Payout Amount": p.payout_amount,
                    "Status": p.status,
                    "Processed At": str(p.processed_at)
                } for p in payouts]), use_container_width=True)
        finally:
            db.close()
