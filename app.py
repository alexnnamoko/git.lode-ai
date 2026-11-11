from __future__ import annotations
import html, json, os, mimetypes, hashlib
from io import BytesIO
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
# Streamlit Community Cloud stores credentials in st.secrets; expose the key to the AI client.
try:
    if not os.getenv("GROQ_API_KEY") and st.secrets.get("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"])
except Exception:
    pass
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from lode.engine.beam import design_beam
from lode.engine.slab import design_one_way_slab
from lode.engine.column import design_short_axially_loaded_column
from lode.knowledge.retrieval import search_knowledge, readable_record, format_retrieval_context
from lode.knowledge.audit import audit_knowledge_datasets
from lode.verification.engine import verify_design_result
from lode.drawing.extract import extract_pdf_pages, render_pdf_page, candidate_dimensions
from lode.drawing.ocr import configure_tesseract, image_ocr
from lode.drawing.preprocess import enhance_for_ocr
from lode.analysis.beam_analysis import analyse_simply_supported_beam
from lode.analysis.frame_model import build_regular_frame
from lode.analysis.frame2d import analyse_frame_2d
from lode.detailing.schedule import beam_schedule
from lode.ai.client import DEFAULT_MODEL, analyse_image, ask_text, parse_json_response, test_connection
from lode.ai.context import build_project_context
from lode.drawing.validation import normalise_vision_response, merge_review_observations
from lode.harness import HarnessController, ToolRouter, build_execution_context

APP_VERSION = "0.11.2-beta"
WARNING = ("ACADEMIC RESEARCH PROTOTYPE — NOT FOR CONSTRUCTION. All drawing interpretations, "
           "loads, assumptions, calculations, code references and reinforcement details require "
           "independent verification by a qualified structural engineer against the complete applicable standards.")
PAGES = ["Overview", "Projects", "Drawing Studio", "Engineer Verification", "Developer & Evaluation", "Structural Modelling",
         "Structural Analysis", "Beam Statics", "Beam Design", "Slab Design", "Column Design",
         "Reinforcement Detailing", "Engineering Adviser", "Reports & Exports", "Scope & Limitations"]

st.set_page_config(page_title="LODE.ai | Atlas.ai", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{--navy:#0b1728;--blue:#173a5e;--cyan:#3bc4c9;--ink:#17283d;--muted:#68788c;--line:#e3eaf1;--panel:#f5f8fb}
.block-container{padding:1.35rem 2.1rem 2.4rem;max-width:1380px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1728 0%,#10243b 100%)}
[data-testid="stSidebar"] *{color:#eaf2f9}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:7px 8px;border-radius:8px;margin:2px 0}[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:rgba(255,255,255,.08)}
.hero{background:linear-gradient(120deg,#0b1728 0%,#173a5e 72%,#1e6875 100%);border:1px solid #294d70;border-radius:18px;padding:20px 24px;color:white;margin-bottom:16px;box-shadow:0 8px 22px rgba(10,29,50,.12)}
.hero h1{font-size:2.1rem;letter-spacing:-.04em;margin:0;font-weight:750}.hero p{color:#d3e2ee;margin:.45rem 0 0;font-size:.98rem}
.eyebrow{color:#62d6d4;text-transform:uppercase;letter-spacing:.16em;font-size:.72rem;font-weight:700}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 15px;height:100%;box-shadow:0 2px 8px rgba(18,42,66,.035)}
.card h3{font-size:1.02rem;margin:0 0 7px;color:var(--ink)}.card p{color:var(--muted);font-size:.9rem;margin:0;line-height:1.5}
.pill{display:inline-block;border:1px solid #d6e8eb;background:#eef9f9;color:#17666b;border-radius:999px;padding:4px 9px;font-size:.74rem;font-weight:650}
.section-title{font-size:1.45rem;font-weight:720;letter-spacing:-.025em;color:var(--ink);margin:0 0 4px}
.section-sub{color:var(--muted);margin:0 0 22px;max-width:900px}.stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{padding:9px 13px}
div.stButton>button[kind="primary"]{background:#116b78;border-color:#116b78}
[data-testid="stMetric"]{background:#f7f9fb;border:1px solid #e8edf2;padding:9px 11px;border-radius:10px}
[data-testid="stExpander"]{border:1px solid #e7edf2;border-radius:10px}
[data-testid="stMarkdownContainer"] p{line-height:1.58}
.stAlert{border-radius:12px}
hr{border-color:#e5ebf1}
</style>
<div class="hero"><div class="eyebrow">Engineering intelligence workspace</div><h1>LODE.ai <span style="font-weight:350;color:#b6d6e5">/ Atlas.ai</span></h1><p>Multimodal engineering assistant for reinforced-concrete design and structural analysis · BS 8110 research prototype</p></div>
""", unsafe_allow_html=True)


def init_state():
    defaults = {"project_name":"Untitled project", "project_notes":"", "verified_data":[], "design_results":{},
                "analysis":None, "frame_model":None, "frame_analysis":None, "detail":None, "drawing_analysis":None, "drawing_name":"", "drawing_page":1,
                "knowledge_hits":[], "last_answer_query":"", "ai_chat":[], "model":DEFAULT_MODEL, "report_notes":"", "ocr_text":"", "adviser_messages":[], "last_answer_sources":[], "drawing_validation_warnings":[], "developer_diagnostics":[]}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
init_state()


def harness_run(task, tool_name, tool_fn, inputs, **tool_kwargs):
    """Execute a fixed application tool through the Atlas harness controller."""
    router = ToolRouter()
    router.register(tool_name, tool_fn)
    controller = HarnessController(router, audit_sink=lambda record: st.session_state.setdefault("harness_audit", []).append(record))
    context = build_execution_context(
        task=task,
        project_name=st.session_state.get("project_name", ""),
        project_notes=st.session_state.get("project_notes", ""),
        verified_observations=st.session_state.get("verified_data", []),
    )
    return controller.execute(task=task, tool=tool_name, inputs=inputs, context=context, **tool_kwargs)

with st.sidebar:
    st.markdown("<div style='font-size:1.35rem;font-weight:800;letter-spacing:-.04em'>LODE<span style='color:#62d6d4'>.ai</span></div><div style='font-size:.75rem;color:#a9c3d6;margin-bottom:12px'>ATLAS.AI · STRUCTURAL DESIGN</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:.68rem;color:#88a9c2;letter-spacing:.14em;font-weight:700;margin:12px 0 5px'>NAVIGATION</div>", unsafe_allow_html=True)
    page = st.radio("WORKSPACE", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("Engineering research workspace")
    st.divider()
    st.caption("Prototype · Independent engineering review required")


def heading(title, subtitle=""):
    st.markdown(f"<div class='section-title'>{html.escape(title)}</div><div class='section-sub'>{html.escape(subtitle)}</div>", unsafe_allow_html=True)


def show_warning(): st.warning(WARNING, icon="⚠️")


def report_error(area: str, exc: Exception, user_message: str):
    """Keep implementation details out of ordinary workflows; retain them for developers."""
    diagnostics = st.session_state.setdefault("developer_diagnostics", [])
    diagnostics.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "area": area,
        "exception_type": type(exc).__name__,
        "details": str(exc)[:4000],
    })
    st.error(user_message)
    st.caption("If this continues, share the time and workflow name with the project developer.")


def show_result(result, key):
    result["verification"] = verify_design_result(result)
    st.session_state.design_results[key] = result
    status = result["verification"]["overall_status"]
    if status.startswith("PASS"):
        st.success("Selected arithmetic checks passed. This is not a code-compliance certificate.")
    elif status == "FAIL":
        st.error("The independent arithmetic check found a discrepancy. Do not rely on this result.")
    else:
        st.warning("Verification is partial or unavailable. Review the stated limitations.")
    member_name = str(result.get("member", "")).lower()
    if "beam" in member_name:
        fields = [("MEd_kNm", "Design moment", "kN·m"), ("VEd_kN", "Support shear", "kN"),
                  ("d_mm", "Effective depth", "mm"), ("As_required_mm2", "Required tension steel", "mm²")]
    elif "slab" in member_name:
        fields = [("MEd_kNm_per_m", "Design moment per metre", "kN·m/m"),
                  ("d_mm", "Effective depth", "mm"), ("As_required_mm2", "Required main steel", "mm²"),
                  ("approx_spacing_mm", "Approximate bar spacing", "mm")]
    elif "column" in member_name:
        fields = [("NEd_kN", "Applied axial load", "kN"),
                  ("Nu_capacity_kN", "Calculated axial capacity expression", "kN"),
                  ("As_provided_mm2", "Provided longitudinal steel", "mm²"),
                  ("steel_percentage", "Steel ratio", "%")]
    else:
        fields = []
    available = [(key, label, unit) for key, label, unit in fields if isinstance(result.get(key), (int, float))]
    if available:
        cols = st.columns(len(available))
        for col, (key, label, unit) in zip(cols, available):
            col.metric(label, f"{result[key]:,.2f} {unit}")
    verification = result.get("verification", {})
    with st.expander("Independent verification checks", expanded=False):
        st.write(verification.get("overall_status", "NOT CHECKED"))
        st.caption(verification.get("scope", "No verification scope supplied."))
        if verification.get("checks"):
            st.dataframe(pd.DataFrame(verification["checks"]), hide_index=True, use_container_width=True)
        st.warning(verification.get("required_review", "Engineer review required."))
    with st.expander("View calculation details", expanded=False):
        rows=[]
        for k,v in result.items():
            if isinstance(v,(dict,list)): rows.append({"Parameter":k.replace("_"," ").title(),"Value":json.dumps(v,ensure_ascii=False)[:1000]})
            else: rows.append({"Parameter":k.replace("_"," ").title(),"Value":str(v)})
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    show_warning()


def make_report():
    buffer=BytesIO(); doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=34,leftMargin=34,topMargin=36,bottomMargin=36)
    styles=getSampleStyleSheet(); story=[Paragraph("LODE.ai — Project Engineering Report",styles["Title"]),
        Paragraph("Atlas.ai · Academic research prototype · BS 8110-1:1997 knowledge resources",styles["Normal"]),Spacer(1,12),
        Paragraph("Project: "+html.escape(st.session_state.project_name),styles["Heading2"]),
        Paragraph("Generated: "+datetime.now().strftime("%Y-%m-%d %H:%M"),styles["Normal"]),Spacer(1,12)]
    def section(title, data):
        story.append(Paragraph(html.escape(title),styles["Heading2"]))
        if not data: story.append(Paragraph("No saved data.",styles["BodyText"])); return
        rows=[["Parameter","Value"]]
        for k,v in data.items(): rows.append([str(k).replace("_"," "),str(v)[:450]])
        table=Table(rows,colWidths=[150,370],repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#173a5e")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#cbd5df")),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP")])); story.extend([table,Spacer(1,10)])
    section("Structural analysis",st.session_state.analysis or {})
    for name,data in st.session_state.design_results.items(): section("Design — "+name,data)
    section("Preliminary reinforcement",st.session_state.detail or {})
    if st.session_state.verified_data:
        story.append(Paragraph("Drawing observations and engineer verification",styles["Heading2"]))
        for row in st.session_state.verified_data: story.append(Paragraph(html.escape(json.dumps(row,ensure_ascii=False)),styles["BodyText"]))
    story.extend([Spacer(1,12),Paragraph(html.escape(st.session_state.project_notes or "No project notes."),styles["BodyText"]),Spacer(1,12),Paragraph(WARNING,styles["Italic"])])
    doc.build(story); return buffer.getvalue()


def plot_sfd_bmd(result):
    fig,axes=plt.subplots(2,1,figsize=(9,5),sharex=True)
    axes[0].plot(result["x_m"],result["shear_kN"]); axes[0].axhline(0,lw=.8); axes[0].set_ylabel("Shear (kN)"); axes[0].grid(alpha=.25)
    axes[1].plot(result["x_m"],result["moment_kNm"]); axes[1].axhline(0,lw=.8); axes[1].set_ylabel("Moment (kN·m)"); axes[1].set_xlabel("Distance along span (m)"); axes[1].grid(alpha=.25)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)


def draw_model_boxes(image_bytes, observations):
    """Overlay approximate model-proposed normalised boxes for human review."""
    image=Image.open(BytesIO(image_bytes)).convert("RGB")
    draw=ImageDraw.Draw(image)
    width,height=image.size
    for item in observations:
        box=item.get("bbox_normalized")
        if not isinstance(box,(list,tuple)) or len(box)!=4: continue
        try:
            x1,y1,x2,y2=[float(v) for v in box]
            if not all(0.0 <= v <= 1.0 for v in (x1,y1,x2,y2)) or x2<=x1 or y2<=y1: continue
            coords=(int(x1*width),int(y1*height),int(x2*width),int(y2*height))
            label=str(item.get("label") or item.get("element_type") or "proposal")[:45]
            draw.rectangle(coords,outline=(0,190,190),width=max(2,width//500))
            draw.text((coords[0]+3,max(0,coords[1]-15)),label,fill=(0,110,120))
        except Exception: continue
    return image


def render_analysis_json(obj):
    st.markdown("**Page summary**"); st.write(obj.get("page_summary","No summary supplied."))
    observations=obj.get("observations",[])
    if observations:
        st.markdown("**Drawing observations · awaiting engineer review**")
        display_rows=[]
        for item in observations:
            display_rows.append({
                "Element": str(item.get("element_type", "unknown")).replace("_", " ").title(),
                "Label": item.get("label", "UNKNOWN"),
                "Observed value": item.get("value", "UNKNOWN"),
                "Unit": item.get("unit", "UNKNOWN"),
                "Location on drawing": item.get("location_description", "Not clear"),
                "Model certainty (unvalidated)": str(item.get("model_certainty", "unknown")).title(),
                "Evidence": item.get("evidence", ""),
                "Review status": item.get("verification_status", "Pending engineer verification")
            })
        st.dataframe(pd.DataFrame(display_rows),hide_index=True,use_container_width=True)
    uncertain=obj.get("uncertain_or_missing",[])
    if uncertain: st.markdown("**Uncertain or missing**"); [st.write("• "+str(x)) for x in uncertain]
    if obj.get("validation_warnings"):
        for warning in obj["validation_warnings"]:
            st.warning(warning)
    st.caption(obj.get("safety_note", "All observations require engineer verification."))
    st.info("The model-reported certainty is qualitative only. It is not a calibrated probability or proof of correct interpretation.")


if page=="Overview":
    heading("Project overview", "A clear workspace for reviewing drawing evidence and exploring preliminary reinforced-concrete design workflows.")
    a,b,c=st.columns(3)
    a.metric("Design modules", "03")
    b.metric("Knowledge records", "335")
    c.metric("Assistant", "Atlas.ai")

    st.markdown("### Engineering workflow")
    cards=[
        ("01 · Drawing input", "Upload PDF or image drawings and review the source pages."),
        ("02 · Drawing interpretation", "Extract printed text and request AI-assisted observations from selected drawing pages."),
        ("03 · Engineer verification", "Review, correct and verify drawing observations before using them as engineering inputs."),
        ("04 · Analysis and design", "Explore supported beam analysis and preliminary BS 8110 beam, slab and column workflows."),
        ("05 · Reports and records", "Review reinforcement schedules and export the current project session and reports."),
    ]
    cols=st.columns(3)
    for i,(title,desc) in enumerate(cards):
        with cols[i%3]:
            st.markdown(f"<div class='card'><h3>{title}</h3><p>{desc}</p></div>", unsafe_allow_html=True)

    st.markdown("### Getting started")
    st.markdown("1. Open **Projects** and enter the project description and design basis.\n2. Use **Drawing Studio** to upload and inspect drawing information.\n3. Review proposed observations in **Engineer Verification**.\n4. Open the relevant design or analysis workspace and check every input and assumption.\n5. Use **Reports & Exports** to retain a record of the session.")
    st.info("Atlas.ai is an academic research prototype. AI interpretations, retrieved references, assumptions, calculations and reinforcement details require independent review by a qualified structural engineer. Do not use this prototype for construction or professional approval.")

elif page=="Projects":
    heading("Project register","Project metadata and current-session engineering evidence.")
    st.text_input("Project name",key="project_name"); st.text_area("Project description / design basis",key="project_notes",height=100)
    a,b=st.columns(2); a.metric("Verified observations",len(st.session_state.verified_data)); b.metric("Saved calculations",len(st.session_state.design_results))
    payload={"project_name":st.session_state.project_name,"project_notes":st.session_state.project_notes,"verified_data":st.session_state.verified_data,"design_results":st.session_state.design_results,"analysis":st.session_state.analysis,"created_export":datetime.now().isoformat()}
    st.download_button("Export project session (JSON)",json.dumps(payload,indent=2,default=str),file_name="lode_project_session.json",mime="application/json")
    imp=st.file_uploader("Import a previous LODE project JSON",type=["json"],key="project_import")
    if imp and st.button("Load project JSON"):
        try:
            loaded=json.loads(imp.getvalue()); st.session_state.project_name=loaded.get("project_name","Imported project"); st.session_state.project_notes=loaded.get("project_notes",""); st.session_state.verified_data=loaded.get("verified_data",[]); st.session_state.design_results=loaded.get("design_results",{}); st.session_state.analysis=loaded.get("analysis"); st.success("Project session loaded.")
        except Exception as e: report_error("Project import", e, "This project file could not be loaded. Check that it is a valid LODE.ai project export.")
    st.info("This is a local/session-based project register. No cloud database, login or multi-user synchronisation is included.")

elif page=="Drawing Studio":
    heading("Drawing Studio","Review drawing evidence, extract printed text and request an AI-assisted visual interpretation.")
    uploaded=st.file_uploader("Upload PDF, PNG or JPEG",type=["pdf","png","jpg","jpeg","webp"])
    if uploaded:
        raw=uploaded.getvalue(); fname=uploaded.name; st.session_state.drawing_name=fname
        drawing_hash=hashlib.sha256(raw).hexdigest()
        active_file_key=f"{drawing_hash}:{fname}"
        if st.session_state.get("_active_drawing_file") != active_file_key:
            st.session_state.drawing_analysis=None; st.session_state.ocr_text=""; st.session_state.pop("ocr_words",None)
            st.session_state["_active_drawing_file"]=active_file_key
        is_pdf=fname.lower().endswith(".pdf") or uploaded.type=="application/pdf"
        page_image=None; page_text=""; page_words=[]; page_no=1
        if is_pdf:
            try:
                pages=extract_pdf_pages(raw)
                page_no=st.selectbox("Select drawing page",list(range(1,len(pages)+1)),format_func=lambda n:f"Page {n} of {len(pages)}")
                page_key=f"{active_file_key}:{page_no}"
                if st.session_state.get("_active_drawing_page") != page_key:
                    st.session_state.drawing_analysis=None; st.session_state.ocr_text=""; st.session_state.pop("ocr_words",None)
                    st.session_state["_active_drawing_page"]=page_key
                p=pages[page_no-1]; page_text=p["text"]; page_words=p["words"]
                page_image=render_pdf_page(raw,page_no,2.0)
                st.image(page_image,caption=f"{fname} · Page {page_no}",use_container_width=True)
                st.caption(f"Page size: {p['width_pt']:.1f} × {p['height_pt']:.1f} pt · Embedded words: {len(page_words)}")
            except Exception as e:
                report_error("PDF processing", e, "This PDF could not be processed. Try another file or export the page as an image.")
                st.stop()
        else:
            page_image=raw; page_no=1; st.image(raw,caption=fname,use_container_width=True)
        use_enhanced=st.checkbox("Enhance contrast / denoise for OCR (OpenCV)",value=False)
        if st.button("Run Tesseract OCR on selected page",type="secondary"):
            try:
                ocr_input=enhance_for_ocr(page_image) if use_enhanced else page_image
                img=Image.open(BytesIO(ocr_input)).convert("RGB")
                ocr=image_ocr(img); st.session_state.ocr_text=ocr["text"]
                st.session_state["ocr_words"]=ocr["words"]
                st.success("Text extraction completed. Review every recognised value against the original drawing.")
                with st.expander("OCR engine details"):
                    st.caption(f"Tesseract {ocr['engine']['version']}")
            except Exception as e: report_error("Workflow", e, "This operation could not be completed. Check the inputs and try again.")
        if page_text:
            with st.expander("Review searchable text embedded in this PDF"):
                st.text_area("PDF text",page_text,height=130,disabled=True)
        if st.session_state.ocr_text:
            with st.expander("Review extracted text (not yet verified)", expanded=True):
                st.text_area("Recognised drawing text",st.session_state.ocr_text,height=150,disabled=True)
                if st.session_state.get("ocr_words"):
                    with st.expander("Technical OCR diagnostics"):
                        st.dataframe(pd.DataFrame(st.session_state.ocr_words),hide_index=True,use_container_width=True)
        st.caption("OCR is text recognition only. It does not identify structural elements or confirm engineering meaning.")
        st.divider()
        prompt=st.text_area("Vision task",value="Identify only clearly visible structural labels, dimensions, grid labels and member annotations. Do not infer missing values. Flag anything uncertain.",height=90)
        if st.button("Analyse drawing with Atlas.ai vision",type="primary"):
            try:
                with st.spinner("Sending selected page to the Groq-hosted vision model…"):
                    mime="image/png" if is_pdf else (uploaded.type or mimetypes.guess_type(fname)[0] or "image/png")
                    raw_response=harness_run("drawing_vision", "groq_vision", analyse_image, {"image_bytes":page_image,"mime_type":mime,"prompt":prompt}, image_bytes=page_image,mime_type=mime,prompt=prompt,ocr_text=st.session_state.ocr_text,model=st.session_state.model)
                    parsed=parse_json_response(raw_response)
                    normalised=normalise_vision_response(parsed)
                    st.session_state.drawing_analysis=normalised
                    st.session_state.drawing_validation_warnings=normalised.get("validation_warnings", [])
                    st.session_state.drawing_page=page_no
                st.success("Drawing review proposals received. Nothing is treated as verified until an engineer confirms it.")
            except Exception as e: report_error("Drawing interpretation", e, "Atlas could not complete the drawing review. Check the connection and image, then try again.")
        if st.session_state.drawing_analysis:
            st.markdown("### Latest vision interpretation")
            render_analysis_json(st.session_state.drawing_analysis)
            obs=st.session_state.drawing_analysis.get("observations",[])
            if any(isinstance(x.get("bbox_normalized"),(list,tuple)) for x in obs):
                st.markdown("**Approximate model-proposed regions** (review visually; not ground-truth boxes)")
                st.image(draw_model_boxes(page_image,obs),use_container_width=True)
            if obs and st.button("Send proposals to engineer review", type="primary"):
                updated, added = merge_review_observations(
                    st.session_state.verified_data, obs,
                    page=st.session_state.drawing_page, source_drawing=fname,
                )
                st.session_state.verified_data = updated
                st.success(f"Sent {added} new proposals to Engineer Verification. Review and confirm each item before using it as an input.")
    else:
        st.markdown("<div class='card'><h3>Start with a drawing</h3><p>Upload a clear structural plan, beam detail or a sample drawing. For scanned pages, run Tesseract OCR first, then request multimodal interpretation.</p></div>",unsafe_allow_html=True)


elif page=="Engineer Verification":
    heading("Engineer verification","Review, correct and approve every extracted observation before it is used as an engineering input.")
    if not st.session_state.verified_data:
        st.info("No observations have been sent here yet. Run a drawing through Drawing Studio and send the proposals to engineer review.")
    else:
        frame=pd.DataFrame(st.session_state.verified_data)
        edited=st.data_editor(frame, num_rows="dynamic", use_container_width=True, key="verification_editor",
            column_config={"status":st.column_config.SelectboxColumn("Verification status",options=["Pending engineer verification","Verified by engineer","Rejected","Requires clarification"]),
                           "model_certainty":st.column_config.SelectboxColumn("Model-reported certainty (unvalidated)",options=["high","medium","low","unknown"])})
        if st.button("Save verification edits",type="primary"):
            st.session_state.verified_data=edited.to_dict(orient="records")
            st.success("Verification register updated for this session.")
        st.caption("Model-reported certainty is not a probability. The application does not independently validate an engineer's approval; record reviewer identity and supporting evidence in the formal project workflow.")
        st.download_button("Export verification register (CSV)",edited.to_csv(index=False),file_name="lode_engineer_verification.csv",mime="text/csv")
    show_warning()


elif page=="Developer & Evaluation":
    heading("Developer & evaluation centre","Technical diagnostics, dataset structure checks and controlled evaluation tools. These tools are separate from normal engineering workflows.")
    st.markdown("#### 1 · Tesseract engine status")
    ok,info=configure_tesseract()
    if ok:
        st.success("Tesseract is available"); st.write(f"Version: {info['version']}"); st.write("Languages: "+", ".join(info["languages"]))
    else: st.warning(f"Tesseract not ready: {info}")
    st.markdown("#### 2 · Explicit vision encoder — CLIP ViT-B/32")
    st.caption("Model: openai/clip-vit-base-patch32. The first run downloads model weights and may take several minutes. Requires requirements-vision.txt.")
    clip_file=st.file_uploader("Choose an image for encoder test",type=["png","jpg","jpeg","webp"],key="clip_image")
    if clip_file:
        st.image(clip_file.getvalue(),caption="Encoder input",width=420)
        if st.button("Run CLIP image encoder test",type="primary"):
            try:
                from lode.vision.clip_encoder import encode_image
                with st.spinner("Loading CLIP and encoding image…"):
                    result=encode_image(clip_file.getvalue())
                st.success(result["status"]); a,b,c=st.columns(3); a.metric("Embedding dimensions",result["embedding_dimension"]); b.metric("Embedding L2 norm",f"{result['embedding_norm']:.4f}"); c.metric("Model", "ViT-B/32")
                with st.expander("Developer diagnostics"):
                    st.write({k:v for k,v in result.items() if k!="embedding_preview"})
                    st.caption("Embedding preview (first 12 values): "+str(result["embedding_preview"]))
            except Exception as e: report_error("Workflow", e, "This operation could not be completed. Check the inputs and try again.")
        prompts=st.text_area("Optional text prompts for image–text similarity (one per line)","a reinforced concrete beam detail\na reinforced concrete column cross-section\na reinforced concrete slab reinforcement plan\na building elevation").splitlines()
        if st.button("Compare image against text prompts"):
            try:
                from lode.vision.clip_encoder import compare_image_text
                with st.spinner("Computing relative similarities…"): scores=compare_image_text(clip_file.getvalue(),[x.strip() for x in prompts if x.strip()])
                st.dataframe(pd.DataFrame(scores),hide_index=True,use_container_width=True)
                st.info("These are relative CLIP similarities among the supplied prompts. They are not calibrated probabilities and do not establish whether a structural object was correctly detected.")
            except Exception as e: report_error("Workflow", e, "This operation could not be completed. Check the inputs and try again.")
    st.markdown("#### 3 · Knowledge dataset structure")
    audit = audit_knowledge_datasets()
    audit_rows=[]
    for kind, details in audit["summary"].items():
        audit_rows.append({"Dataset": "Design rules" if kind == "rule" else "Question & answer",
            "Records": details["records"],"Unique clause references": details["unique_clause_references"],
            "Missing IDs": details["missing_ids"],"Missing clause references": details["missing_clause_references"],
            "Missing primary content": details["missing_primary_content"],
            "Duplicate IDs": len(details["duplicate_ids"])})
    st.dataframe(pd.DataFrame(audit_rows),hide_index=True,use_container_width=True)
    st.caption("Structural audit only. It does not validate the engineering accuracy, completeness or legal status of dataset content.")
    with st.expander("Developer diagnostics — audit findings and limitations"):
        for finding in audit["findings"]:
            st.warning(finding)
        for limitation in audit["limitations"]:
            st.write("• " + limitation)
    with st.expander("Application diagnostics", expanded=False):
        diagnostics = st.session_state.get("developer_diagnostics", [])
        if diagnostics:
            st.dataframe(pd.DataFrame(diagnostics), hide_index=True, use_container_width=True)
            if st.button("Clear diagnostic history"):
                st.session_state.developer_diagnostics = []
                st.rerun()
        else:
            st.caption("No application errors have been recorded in this session.")
    st.markdown("#### 4 · Harness execution records")
    st.caption("Records successful, rejected and failed harness executions in this browser session. Raw drawing bytes and credentials are excluded.")
    harness_records = st.session_state.get("harness_audit", [])
    if harness_records:
        st.dataframe(pd.DataFrame(harness_records), hide_index=True, use_container_width=True)
        st.download_button("Export harness audit (JSON)", json.dumps(harness_records, indent=2, ensure_ascii=False),
                           file_name="atlas_harness_audit.json", mime="application/json")
        if st.button("Clear harness audit history"):
            st.session_state.harness_audit = []
            st.rerun()
    else:
        st.info("No harness executions recorded in this session yet.")
    st.markdown("#### 5 · Controlled test record")
    with st.expander("Evaluation guidance"):
        st.write("For a defensible evaluation, create a labelled test set of drawings and manually record ground-truth labels, dimensions and bounding boxes. Compare model proposals with that reference; report precision, recall, F1, exact text accuracy and dimension error. A successful API response is not proof of accuracy.")
    st.download_button("Download blank vision ground-truth template", "drawing_id,page,element_type,label,value,unit,x1_norm,y1_norm,x2_norm,y2_norm,reviewer,notes\n", file_name="vision_ground_truth_template.csv",mime="text/csv")

elif page=="Structural Modelling":
    heading("Structural modelling", "Create a parameterised 2D frame with explicit member placement, section properties and connectivity.")
    with st.form("frame_model_form"):
        st.markdown("#### 1 · Frame geometry")
        a,b,c=st.columns(3)
        bays=a.number_input("Number of bays",1,8,2)
        storeys=b.number_input("Number of storeys",1,8,2)
        bay_width=c.number_input("Typical bay width (m)",min_value=0.5,max_value=20.0,value=4.0)
        a,b=st.columns(2)
        storey_height=a.number_input("Storey height (m)",min_value=0.5,max_value=10.0,value=3.0)
        elastic_modulus=b.number_input("Concrete elastic modulus (GPa)",min_value=1.0,max_value=60.0,value=25.0,help="User-specified elastic modulus for linear-elastic analysis; not inferred from concrete grade.")
        st.markdown("#### 2 · Member section properties")
        st.caption("Rectangular gross sections are assumed. Beam and column dimensions are entered separately.")
        a,b,c,d=st.columns(4)
        beam_width=a.number_input("Beam width (mm)",150,1000,225,step=25)
        beam_depth=b.number_input("Beam depth (mm)",200,1500,450,step=25)
        col_width=c.number_input("Column width (mm)",150,1500,300,step=25)
        col_depth=d.number_input("Column depth (mm)",150,1500,300,step=25)
        build=st.form_submit_button("Generate structural frame",type="primary")
    if build:
        try:
            st.session_state.frame_model=build_regular_frame(int(bays),int(storeys),bay_width,storey_height,beam_width,beam_depth,col_width,col_depth,elastic_modulus)
            st.session_state.frame_analysis=None
            st.success("Frame model generated. Review the geometry, member schedule and assumptions below.")
        except Exception as e: report_error("Structural modelling",e,"The frame model could not be generated. Check the geometry and section inputs.")
    model=st.session_state.get("frame_model")
    if model:
        st.markdown("#### Model preview")
        fig,ax=plt.subplots(figsize=(10,5))
        for m in model["members"]:
            ni=next(n for n in model["nodes"] if n["id"]==m["i"]); nj=next(n for n in model["nodes"] if n["id"]==m["j"])
            ax.plot([ni["x_m"],nj["x_m"]],[ni["y_m"],nj["y_m"]],linewidth=3 if m["type"]=="Beam" else 2)
        for n in model["nodes"]: ax.scatter(n["x_m"],n["y_m"],s=22); ax.annotate(n["id"],(n["x_m"],n["y_m"]),xytext=(3,4),textcoords="offset points",fontsize=7)
        ax.set_aspect("equal"); ax.set_xlabel("X (m)"); ax.set_ylabel("Storey elevation (m)"); ax.grid(alpha=.2); st.pyplot(fig); plt.close(fig)
        a,b,c=st.columns(3); a.metric("Nodes",len(model["nodes"])); b.metric("Members",len(model["members"])); c.metric("Base restraints",len(model["supports"]))
        st.markdown("#### Member schedule")
        st.dataframe(pd.DataFrame([{"Member":m["id"],"Type":m["type"],"From":m["i"],"To":m["j"],"Section (mm)":m["section_mm"],"Connectivity":"Rigid joint"} for m in model["members"]]),use_container_width=True,hide_index=True)
        st.markdown("#### Model assumptions")
        st.info("Regular planar frame; beams and columns are connected at rigid joints. All base nodes are fixed. Gross rectangular section properties and one common elastic modulus are used. The generated model is an idealisation and must be checked against project drawings.")
        st.download_button("Download structural model (JSON)",json.dumps(model,indent=2),file_name="atlas_frame_model.json",mime="application/json")
    else:
        st.info("Enter the frame geometry and section properties, then generate the model. No structural model has been created yet.")

elif page=="Structural Analysis":
    heading("Structural analysis", "Run a first-order 2D frame analysis using the direct stiffness method on the generated structural model.")
    model=st.session_state.get("frame_model")
    if not model:
        st.info("Generate a structural frame first in Structural Modelling. The analysis engine needs member geometry, properties and connectivity.")
    else:
        top_nodes=[n for n in model["nodes"] if abs(n["y_m"]-model["storeys"]*model["storey_height_m"])<1e-8]
        st.caption(f"Active model: {model['bays']} bays · {model['storeys']} storeys · {len(model['members'])} members · fixed bases")
        with st.form("frame_analysis_form"):
            st.markdown("#### Applied nodal loading")
            a,b=st.columns(2)
            fx=a.number_input("Horizontal load at each top-storey joint (kN)",value=10.0,help="Positive acts in global +X direction.")
            fy=b.number_input("Vertical load at each top-storey joint (kN)",value=-20.0,help="Negative acts downward in global Y direction.")
            run=st.form_submit_button("Analyse structural frame",type="primary")
        if run:
            try:
                loads={n["id"]:[fx,fy,0.0] for n in top_nodes}
                st.session_state.frame_analysis=harness_run("frame_analysis", "frame_solver", analyse_frame_2d, {"nodes":model["nodes"],"members":model["members"],"supports":model["supports"],"loads":loads}, nodes=model["nodes"],members=model["members"],supports=model["supports"],nodal_loads=loads)
            except Exception as e: report_error("Structural analysis",e,"The frame could not be analysed. Review the supports, connectivity, properties and loading.")
        result=st.session_state.get("frame_analysis")
        if result:
            st.success("Frame analysis completed by the linear-elastic direct stiffness solver. Review all assumptions and results independently.")
            nr=pd.DataFrame(result["nodes"]); mr=pd.DataFrame([{"Member":m["member_id"],"Length (m)":m["length_m"],"i-end N (kN)":m["local_end_actions_kN_kNm"][0],"i-end V (kN)":m["local_end_actions_kN_kNm"][1],"i-end M (kN·m)":m["local_end_actions_kN_kNm"][2],"j-end N (kN)":m["local_end_actions_kN_kNm"][3],"j-end V (kN)":m["local_end_actions_kN_kNm"][4],"j-end M (kN·m)":m["local_end_actions_kN_kNm"][5]} for m in result["members"]])
            st.markdown("#### Joint displacements and support reactions")
            st.dataframe(nr,use_container_width=True,hide_index=True)
            st.markdown("#### Member local end actions")
            st.dataframe(mr,use_container_width=True,hide_index=True)
            st.download_button("Download analysis results (CSV)",mr.to_csv(index=False),file_name="atlas_frame_member_actions.csv",mime="text/csv")
            with st.expander("Analysis method and limitations"):
                st.write(result["method"])
                for item in result["limitations"]: st.write("• "+item)
            show_warning()

elif page=="Beam Statics":
    heading("Simply supported beam statics", "Retained single-beam analysis for full-span UDL and downward point loads.")
    with st.form("analysis_form"):
        a,b,c=st.columns(3); span=a.number_input("Beam span (m)",min_value=.1,value=6.0); udl=b.number_input("Full-span UDL (kN/m)",min_value=0.0,value=10.0); n=c.number_input("Number of point loads",0,5,1)
        point_loads=[]
        for i in range(int(n)):
            x,y=st.columns(2); px=x.number_input(f"Point load {i+1} position from A (m)",0.0,float(span),float(span/2),key=f"beamstat_px{i}"); py=y.number_input(f"Point load {i+1} (kN)",0.0,value=20.0,key=f"beamstat_py{i}"); point_loads.append({"x_m":px,"load_kn":py})
        run=st.form_submit_button("Analyse simply supported beam",type="primary")
    if run:
        try: st.session_state.analysis=harness_run("beam_statics", "beam_statics_solver", analyse_simply_supported_beam, {"span_m":span,"udl_kn_m":udl,"point_loads":point_loads}, span_m=span,udl_kn_m=udl,point_loads=point_loads)
        except Exception as e: report_error("Beam statics",e,"This operation could not be completed. Check the inputs and try again.")
    if st.session_state.analysis:
        r=st.session_state.analysis; a,b,c,d=st.columns(4); a.metric("Reaction A",f"{r['reaction_A_kN']:.2f} kN"); b.metric("Reaction B",f"{r['reaction_B_kN']:.2f} kN"); c.metric("Max |V|",f"{r['max_abs_shear_kN']:.2f} kN"); d.metric("Max |M|",f"{r['max_abs_moment_kNm']:.2f} kN·m")
        plot_sfd_bmd(r); st.success(f"Equilibrium checks: vertical residual {r['equilibrium_vertical_error_kN']:.3g} kN; moment residual {r['equilibrium_moment_error_kNm']:.3g} kN·m")
        st.caption(r["sign_convention"]); show_warning()

elif page=="Beam Design":
    heading("RC beam design","Limited simply supported rectangular beam under UDL. BS 8110-focused academic calculation module.")
    with st.form("beam_design"):
        a,b,c=st.columns(3); span=a.number_input("Effective span (m)",1.0,value=6.0); width=b.number_input("Width (mm)",100,value=225); depth=c.number_input("Overall depth (mm)",150,value=450)
        a,b,c=st.columns(3); cover=a.number_input("Cover (mm)",10,value=25); link=b.number_input("Link diameter (mm)",6,value=8); bar=c.number_input("Main bar diameter (mm)",8,value=20)
        a,b,c=st.columns(3); fcu=a.number_input("Concrete cube strength fcu (N/mm²)",15.0,value=25.0); fy=b.number_input("Main steel fy (N/mm²)",250.0,value=460.0); fyv=c.number_input("Link steel fy (N/mm²)",250.0,value=460.0)
        a,b=st.columns(2); g=a.number_input("Dead load Gk (kN/m)",0.0,value=20.0); q=b.number_input("Imposed load Qk (kN/m)",0.0,value=10.0)
        vc=st.number_input("Verified concrete shear capacity vc (N/mm²); 0 omits shear screening",0.0,value=0.0)
        run=st.form_submit_button("Design beam",type="primary")
    if run:
        try: show_result(harness_run("beam_design", "rc_beam_design", design_beam, {"span_m":span,"width_mm":width,"overall_depth_mm":depth}, span_m=span,width_mm=width,overall_depth_mm=depth,cover_mm=cover,link_diameter_mm=link,main_bar_diameter_mm=bar,fcu_nmm2=fcu,fy_nmm2=fy,dead_load_kn_m=g,imposed_load_kn_m=q,shear_concrete_capacity_n_mm2=vc or None,link_steel_fy_nmm2=fyv),"Beam")
        except Exception as e: report_error("Workflow", e, "This operation could not be completed. Check the inputs and try again.")

elif page=="Slab Design":
    heading("RC one-way slab design","Simply supported one-way slab using a one-metre design strip.")
    with st.form("slab_design"):
        a,b,c=st.columns(3); span=a.number_input("Effective span (m)",.5,value=3.5); thick=b.number_input("Thickness (mm)",100,value=160); cover=c.number_input("Cover (mm)",10,value=20)
        a,b,c=st.columns(3); bar=a.number_input("Main bar diameter (mm)",6,value=10); fcu=b.number_input("fcu (N/mm²)",15.0,value=25.0); fy=c.number_input("Steel fy (N/mm²)",250.0,value=460.0)
        a,b=st.columns(2); g=a.number_input("Dead load Gk (kN/m²)",0.0,value=4.0); q=b.number_input("Imposed load Qk (kN/m²)",0.0,value=2.0)
        run=st.form_submit_button("Design slab",type="primary")
    if run:
        try: show_result(harness_run("slab_design", "rc_slab_design", design_one_way_slab, {"span_m":span,"thickness_mm":thick}, span_m=span,thickness_mm=thick,cover_mm=cover,bar_diameter_mm=bar,fcu_nmm2=fcu,fy_nmm2=fy,dead_load_kn_m2=g,imposed_load_kn_m2=q),"Slab")
        except Exception as e: report_error("Workflow", e, "This operation could not be completed. Check the inputs and try again.")

elif page=="Column Design":
    heading("RC column design","Short tied rectangular column under concentric axial compression only.")
    with st.form("column_design"):
        a,b,c=st.columns(3); width=a.number_input("Width (mm)",150,value=300); depth=b.number_input("Depth (mm)",150,value=300); load=c.number_input("Ultimate axial load (kN)",1.0,value=800.0)
        a,b,c=st.columns(3); fcu=a.number_input("fcu (N/mm²)",15.0,value=25.0); fy=b.number_input("Steel fy (N/mm²)",250.0,value=460.0); bar=c.number_input("Longitudinal bar diameter (mm)",8,value=20)
        count=st.number_input("Number of longitudinal bars",4,value=8,step=1); confirmed=st.checkbox("I have independently confirmed this is a short column and axial-only assumptions are appropriate.")
        run=st.form_submit_button("Design column",type="primary")
    if run:
        try: show_result(harness_run("column_design", "rc_column_design", design_short_axially_loaded_column, {"width_mm":width,"depth_mm":depth,"axial_load_kn":load}, width_mm=width,depth_mm=depth,axial_load_kn=load,fcu_nmm2=fcu,fy_nmm2=fy,bar_diameter_mm=bar,number_of_bars=int(count),confirmed_short_column=confirmed),"Column")
        except Exception as e: report_error("Workflow", e, "This operation could not be completed. Check the inputs and try again.")

elif page=="Reinforcement Detailing":
    heading("Reinforcement detailing","Preliminary bar selection and schedule from a required steel area. Not construction detailing.")
    saved=st.session_state.design_results.get("Beam",{}); default=float(saved.get("As_required_mm2",600.0))
    with st.form("detail_form"):
        area=st.number_input("Required longitudinal steel area As (mm²)",min_value=1.0,value=max(1.0,default)); link_d=st.selectbox("Link diameter (mm)",[6,8,10,12],index=1); spacing=st.number_input("Link spacing (mm) — user supplied",min_value=0,value=0,step=5); cover=st.number_input("Nominal cover (mm) — user supplied",min_value=0,value=25)
        run=st.form_submit_button("Generate preliminary schedule",type="primary")
    if run:
        try: st.session_state.detail=beam_schedule(area,link_d,spacing or None,cover)
        except Exception as e: report_error("Workflow", e, "This operation could not be completed. Check the inputs and try again.")
    if st.session_state.detail:
        st.dataframe(pd.DataFrame([{"Item":k.replace("_"," "),"Value":str(v)} for k,v in st.session_state.detail.items()]),hide_index=True,use_container_width=True); st.warning(st.session_state.detail["status"])

elif page=="Engineering Adviser":
    heading("Atlas.ai Engineering Adviser","Ask an engineering question, explore a design decision or continue a project discussion.")
    with st.container(border=True):
        st.markdown("**Atlas assistance**")
        st.caption("Atlas uses recent conversation, your project description and drawing observations explicitly verified by an engineer. It asks for missing inputs and distinguishes retrieved dataset material from general engineering explanation.")
    if st.session_state.adviser_messages:
        for message in st.session_state.adviser_messages[-12:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    query=st.chat_input("Ask Atlas about reinforced concrete, structural behaviour or BS 8110…")
    if query:
        previous_history = list(st.session_state.adviser_messages[-8:])
        st.session_state.adviser_messages.append({"role":"user","content":query})
        hits=search_knowledge(query,limit=6)
        st.session_state.knowledge_hits=hits
        st.session_state.last_answer_query=query
        source_context=format_retrieval_context(hits)
        project_context=build_project_context(
            project_name=st.session_state.project_name,
            project_notes=st.session_state.project_notes,
            verified_observations=st.session_state.verified_data,
        )
        try:
            with st.spinner("Atlas is reviewing your question and relevant project references…"):
                answer=harness_run("engineering_adviser", "groq_text_adviser", ask_text, {"query":query}, prompt=query, context=source_context,history=previous_history,
                    project_context=project_context,model=st.session_state.model)
        except Exception as e:
            answer="I couldn't connect to the AI service, so I haven't generated an engineering answer. Check the connection settings and try again."
            report_error("Engineering Adviser", e, "Atlas could not reach the AI service. No engineering answer was generated.")
        else:
            st.session_state.pop("last_ai_error",None)
        st.session_state.adviser_messages.append({"role":"assistant","content":answer})
        st.session_state.last_answer_sources=[{
            "type":hit["type"],"title":readable_record(hit)["title"],
            "clause":readable_record(hit)["reference"],"dataset":hit["source"]["dataset"],
            "record_id":hit["source"]["record_id"],"relevance":hit["score"]
        } for hit in hits]
        st.rerun()
    if st.session_state.last_answer_query:
        with st.expander("References retrieved for the latest question", expanded=False):
            st.caption("These are the records retrieved for the latest question, not proof that their contents or applicability have been verified against the published standard.")
            if st.session_state.last_answer_sources:
                st.dataframe(pd.DataFrame(st.session_state.last_answer_sources),hide_index=True,use_container_width=True)
            else:
                st.info("No matching BS 8110 dataset records were retrieved. Atlas should not invent a clause reference.")
    left,right=st.columns([1,5])
    with left:
        if st.button("Clear conversation"):
            st.session_state.adviser_messages=[]
            st.session_state.knowledge_hits=[]
            st.session_state.last_answer_sources=[]
            st.session_state.last_answer_query=""
            st.rerun()
    with right:
        st.caption("Conversation and project context are held in this app session only. Pending drawing proposals are excluded from Atlas project context.")
    show_warning()

elif page=="Reports & Exports":
    heading("Reports & exports","Compile the current session's analysis, calculations, verified observations and preliminary detailing.")
    a,b,c=st.columns(3); a.metric("Verified observations",len(st.session_state.verified_data)); b.metric("Saved design calculations",len(st.session_state.design_results)); c.metric("Analysis saved","Yes" if st.session_state.analysis else "No")
    if st.button("Generate project PDF",type="primary"): st.session_state.report_ready=True
    if st.session_state.get("report_ready"): st.download_button("Download LODE.ai engineering report",make_report(),file_name="LODE_ai_project_report.pdf",mime="application/pdf")
    st.info("The PDF is an academic record of current-session outputs. It is not a signed design certificate or construction drawing.")

elif page=="Scope & Limitations":
    heading("Scope & limitations","A clear boundary between implemented functions, model-assisted proposals and future research.")
    st.markdown("""
### Implemented in this package
- Streamlit browser application with professional responsive workspace layout.
- Groq-hosted Qwen vision model for text and image interpretation. A Groq API key is required; free-tier access and rate limits depend on the provider account.
- Tesseract OCR integration with executable discovery, OCR text and word bounding boxes. The Tesseract binary must be installed on the host; Streamlit Cloud uses `packages.txt`.
- Optional explicit CLIP ViT-B/32 encoder diagnostics, embedding generation and relative text-image similarity. Install `requirements-vision.txt` to enable it.
- PDF/image upload, PDF page rendering, digital PDF text extraction, OCR, Groq-hosted Qwen visual interpretation and engineer-verification handoff.
- Existing BS 8110 JSON retrieval and limited beam, one-way slab and short axially-loaded column calculations preserved.
- Simply supported beam reactions, SFD/BMD for full-span UDL and downward point loads; equilibrium residual checks.
- Preliminary beam reinforcement bar selection, session project JSON export/import and PDF report export.
- GitHub repository files, setup documentation and automated tests.

### Not implemented / not claimed
- No fine-tuning or LoRA training; Qwen vision model is hosted by Groq; no model fine-tuning or LoRA training is included.
- CLIP similarity is not calibrated confidence, object detection, segmentation or proof of engineering interpretation accuracy.
- Groq-hosted Qwen vision proposals are not guaranteed correct; bounding boxes and dimensions require manual validation.
- No automatic verified building geometry, connected analytical model, finite-element/global frame analysis or load-path analysis.
- No full continuous/doubly reinforced/flanged beam, torsion, complete shear/deflection/crack checks, full two-way slab, punching shear, foundation, retaining wall or slender/biaxial column design.
- No complete construction-ready reinforcement detailing, anchorage/laps/curtailment validation or DXF generation.
- Knowledge datasets are retrieval aids, not a complete executable or certified BS 8110 implementation. Amendments and related standards must be checked.
- No user accounts, database, cloud sync, or hosted public URL. Anyone may fork the repository and run it locally or deploy the Streamlit app with their own Groq API key. Groq hosts inference; Streamlit hosts the app interface.

**Academic prototype only. Not for construction.** Software tests establish software behaviour only; they do not certify code compliance or engineering safety.
""")
    show_warning()
