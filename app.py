import streamlit as st
import pandas as pd
import json
import time
import random
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(page_title="Hopkins Health Portal", layout="wide", initial_sidebar_state="expanded")

# --- ENTERPRISE CSS OVERRIDE ---
st.markdown("""
    <style>
    .stApp {
        background-color: #F4F7FC;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #1C1B4B;
        border-right: none;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    h1, h2, h3 {
        color: #1E293B;
        font-weight: 600;
    }
    p, span, label {
        color: #475569;
    }
    /* Secondary Buttons */
    div.stButton > button {
        border-radius: 20px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        border: 1px solid #CBD5E1;
        background-color: white;
        color: #0F172A; /* Darkened text so it doesn't look greyed out */
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #8B5CF6;
        color: #8B5CF6;
        box-shadow: 0 4px 6px -1px rgba(139, 92, 246, 0.1);
    }
    /* Primary Buttons (Teal) */
    div.stButton > button[kind="primary"] {
        background-color: #14B8A6;
        color: white;
        border: none;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #0D9488;
        color: white;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: white;
        border-radius: 12px;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        padding: 24px;
    }
    [data-testid="stMetricValue"] {
        color: #1E293B;
        font-size: 2rem;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #64748B;
        font-weight: 500;
    }
    .hero-box {
        background: linear-gradient(135deg, #1C1B4B 0%, #2D2A77 100%);
        padding: 40px 30px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(28, 27, 75, 0.2);
    }
    .hero-box h1, .hero-box p {
        color: white;
        margin: 0;
    }
    .hero-box h1 {
        font-size: 2.5rem;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SECRETS & API SETUP (GROQ) ---
try:
    api_key = st.secrets["GROQ_API_KEY"] 
except KeyError:
    st.error("System Error: Missing API Key Configuration.")
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key,
)

# --- STAFF MAPPING DIRECTORY ---
STAFF_MAP = {
    "Clinical": ["Dr. Sarah Chen", "NP Adams", "Dr. Martinez", "Nurse Triage Unit"],
    "Billing": ["Joe (Billing)", "Sarah (Finance)", "Marcus (Accounts)", "Billing Department"],
    "Scheduling": ["Lisa (Front Desk)", "Mike (Scheduling)", "Elena (Reception)"],
    "IT_Support": ["Dave (IT Helpdesk)", "System Admin", "Tech Support Team"]
}

# --- SESSION STATE ---
if "logged_in_as" not in st.session_state:
    st.session_state.logged_in_as = None
if "pending_messages" not in st.session_state:
    st.session_state.pending_messages = []
if "analyzed_ticket" not in st.session_state:
    st.session_state.analyzed_ticket = None
if "archived_tickets" not in st.session_state:
    st.session_state.archived_tickets = [] 
if "routed_messages" not in st.session_state:
    st.session_state.routed_messages = [] # Emptied out for realism!

# --- 1. BASELINE SYSTEM (FIXED BUG) ---
def keyword_baseline(text):
    clean_words = text.lower().replace('.', '').replace(',', '').replace('?', '').split()
    
    if any(word in clean_words for word in ['password', 'login', 'error', 'app', 'portal', 'click']):
        return "IT_Support"
    elif any(word in clean_words for word in ['pay', 'bill', 'cost', 'charge', 'insurance', 'copay']):
        return "Billing"
    elif any(word in clean_words for word in ['appointment', 'cancel', 'schedule', 'reschedule', 'time']):
        return "Scheduling"
    elif any(word in clean_words for word in ['pain', 'refill', 'doctor', 'pill', 'sick', 'fever', 'hurt']):
        return "Clinical"
    else:
        return "Unclassified" 

# --- 2. LLM SYSTEM (GROQ) ---
def llm_router(message):
    system_prompt = """You are an automated triage system for a hospital patient portal.
    Classify the patient's message into exactly ONE of these four departments: Billing, Scheduling, Clinical, or IT_Support.
    
    CRITICAL SAFETY RULE: If the message mentions severe pain, bleeding, or shortness of breath, you MUST immediately classify it as Clinical, regardless of other text.

    OUTPUT FORMAT: Return strictly valid JSON with exactly two keys:
    1. "category": The assigned department name.
    2. "sql": An Oracle SQL INSERT statement formatted exactly like this: 
       INSERT INTO portal_tickets (message_body, assigned_dept) VALUES ('<escaped_message>', '<category>');
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"category": "Error", "sql": str(e)}

# --- NAVIGATION CONTROLS ---
def logout():
    st.session_state.logged_in_as = None

# --- SMART SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### Portal Overview")
    
    # Only show profile tools if logged in
    if st.session_state.logged_in_as == "Patient":
        st.info("👤 **Patient Profile:**\nKhadidiatou Dia")
        st.button("Secure Log Out", on_click=logout, use_container_width=True, type="primary")
    elif st.session_state.logged_in_as == "Hospital":
        st.success("🛡️ **Active Role:**\nTriage Administrator")
        st.button("Secure Log Out", on_click=logout, use_container_width=True, type="primary")
    else:
        st.write("Please authenticate to access system modules.")
        
    st.divider()
    st.caption("Hopkins Health System v2.2")
    st.caption("End-to-End Encryption Enabled")

# ==========================================
# VIEW 0: LOGIN SCREEN
# ==========================================
if st.session_state.logged_in_as is None:
    st.markdown('<div class="hero-box"><h1>Hopkins Health System</h1><p>Secure Portal Login Gateway</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("### Authentication Required")
        
        with st.container(border=True):
            st.markdown("#### Patient Access")
            st.write("Access health records, messages, and billing.")
            if st.button("Log in as Patient", type="primary", use_container_width=True):
                st.session_state.logged_in_as = "Patient"
                st.rerun()
                
        st.write("") 
        
        with st.container(border=True):
            st.markdown("#### Provider & Staff Access")
            st.write("Authorized clinical and administrative personnel.")
            if st.button("Log in as Staff", use_container_width=True):
                st.session_state.logged_in_as = "Hospital"
                st.rerun()

# ==========================================
# VIEW 1: PATIENT PORTAL
# ==========================================
elif st.session_state.logged_in_as == "Patient":
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("Patient Overview")
    with col2:
        st.button("Log Out", on_click=logout, type="primary")
        
    st.write("Welcome back, Khadidiatou Dia.")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Recent Test Results", value="2 Unread")
    m2.metric(label="Upcoming Appointments", value="1 Scheduled")
    m3.metric(label="Outstanding Balance", value="$0.00")
    
    st.write("")
    
    tab1, tab2 = st.tabs(["Compose New Message", "Secure Inbox"])
    
    with tab1:
        with st.container(border=True):
            st.markdown("### Secure Messaging Center")
            
            # Using st.form automatically clears the text box on submit
            with st.form("compose_message_form", clear_on_submit=True):
                new_message = st.text_area("Direct Message to Care Team", placeholder="Please describe your symptoms, request, or inquiry...", height=120, label_visibility="collapsed")
                submitted = st.form_submit_button("Submit Message", type="primary")
                
                if submitted:
                    if new_message.strip() == "":
                        st.warning("Message payload cannot be empty.")
                    else:
                        msg_text = new_message.strip()
                        st.session_state.pending_messages.append(msg_text)
                        
                        # Add instantly to inbox
                        st.session_state.routed_messages.insert(0, {
                            "text": msg_text,
                            "category": "Pending Triage",
                            "staff": "Awaiting Assignment",
                            "reply": "Your message has been received and is currently in the triage queue."
                        })
                        st.success("Transmission successful! Your message is in the routing queue.")

    with tab2:
        st.markdown("### Active Message Threads")
        
        # Filtering Logic
        filter_dept = st.selectbox("Filter Messages by Department:", ["All Departments", "Clinical", "Billing", "Scheduling", "IT_Support", "Pending Triage"])
        
        display_list = st.session_state.routed_messages
        if filter_dept != "All Departments":
            display_list = [m for m in display_list if m["category"] == filter_dept]
        
        if len(display_list) == 0:
            if len(st.session_state.routed_messages) == 0:
                st.info("Your secure inbox is currently empty. Messages routed to our care team will appear here.")
            else:
                st.info(f"No messages found for the {filter_dept} filter.")
        else:
            # Create a clickable dropdown thread for each routed message
            for idx, msg in enumerate(display_list):
                with st.expander(f"{msg['category']} Department Inquiry", expanded=(idx == 0)):
                    st.caption(f"**Assigned Care Member:** {msg['staff']}")
                    st.divider()
                    
                    # Chat Bubble UI
                    with st.chat_message("user"):
                        st.write(msg['text'])
                        
                    with st.chat_message("assistant"):
                        st.write(msg['reply'])

# ==========================================
# VIEW 2: HOSPITAL DASHBOARD & EVALUATION
# ==========================================
elif st.session_state.logged_in_as == "Hospital":
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("Triage Command Center")
    with col2:
        st.button("Log Out", on_click=logout, type="primary")
        
    st.write("Automated Inquiry Routing and Categorization")
    st.divider()
    
    staff_tab1, staff_tab2 = st.tabs(["Active Queue", "Archive & Analytics"])
    
    with staff_tab1:
        if len(st.session_state.pending_messages) == 0:
            st.info("The message queue is currently empty. Switch to Patient Portal to submit a test message.")
        else:
            current_message = st.session_state.pending_messages[0]
            
            with st.container(border=True):
                st.markdown("**Incoming Patient Transmission:**")
                st.write(f"*{current_message}*")
                st.write("")
                
                if st.session_state.analyzed_ticket is None or st.session_state.analyzed_ticket["message"] != current_message:
                    if st.button("Execute Routing Protocol", type="primary"):
                        with st.spinner("Processing semantics..."):
                            baseline_result = keyword_baseline(current_message)
                            llm_result = llm_router(current_message)
                            
                            st.session_state.analyzed_ticket = {
                                "message": current_message,
                                "llm_result": llm_result,
                                "baseline_result": baseline_result
                            }
                            st.rerun() 
                            
                if st.session_state.analyzed_ticket is not None and st.session_state.analyzed_ticket["message"] == current_message:
                    llm_result = st.session_state.analyzed_ticket["llm_result"]
                    baseline_result = st.session_state.analyzed_ticket["baseline_result"]
                    
                    st.divider()
                    col_ai, col_base = st.columns(2)
                    
                    with col_ai:
                        st.markdown("#### Primary System (GenAI)")
                        cat = llm_result.get('category', 'Unknown')
                        st.info(f"**Assigned Routing:** {cat}")
                        st.caption("Generated SQL Command:")
                        st.code(llm_result.get('sql'), language='sql')
                            
                    with col_base:
                        st.markdown("#### Legacy System (Baseline)")
                        st.write(f"**Assigned Routing:** {baseline_result}")
                        if baseline_result != cat:
                            st.warning("Context discrepancy detected in legacy logic.")
                    
                    st.write("")
                    if st.button("Commit to Database & Archive Ticket", use_container_width=True):
                        assigned_staff = random.choice(STAFF_MAP.get(cat, ["System Administrator"]))
                        
                        # Update the specific pending message in the Patient Inbox
                        for msg in st.session_state.routed_messages:
                            if msg["text"] == current_message and msg["category"] == "Pending Triage":
                                msg["category"] = cat
                                msg["staff"] = assigned_staff
                                msg["reply"] = "Your inquiry has been successfully routed. Our team is reviewing your file and will respond shortly."
                                break
                        
                        # Send to Hospital Archive
                        st.session_state.archived_tickets.insert(0, {
                            "Patient Message": current_message,
                            "Routed Dept": cat,
                            "Assigned Staff": assigned_staff,
                            "Status": "Pending Action"
                        })
                        
                        st.session_state.pending_messages.pop(0)
                        st.session_state.analyzed_ticket = None
                        st.rerun()

    with staff_tab2:
        st.subheader("Historical Ticket Archive")
        
        if len(st.session_state.archived_tickets) == 0:
            st.info("No tickets have been archived during this session.")
        else:
            df_archive = pd.DataFrame(st.session_state.archived_tickets)
            st.dataframe(df_archive, use_container_width=True)
            
            if st.button("Clear System Archive"):
                st.session_state.archived_tickets = []
                st.session_state.routed_messages = [] # Clears patient inbox too
                st.session_state.pending_messages = []
                st.rerun()

    # Evaluation Section
    st.write("")
    st.write("")
    with st.expander("System Administration: Execute Batch Evaluation"):
        st.write("Run validation against the 50-record synthetic test suite.")
        if st.button("Initialize Test Sequence"):
            try:
                df = pd.read_csv("patient_messages.csv")
                my_bar = st.progress(0, text="Compiling results...")
                
                baseline_preds, llm_preds = [], []
                for index, row in df.iterrows():
                    baseline_preds.append(keyword_baseline(row['Message']))
                    llm_preds.append(llm_router(row['Message']).get('category', 'Error'))
                    my_bar.progress((index + 1) / len(df), text=f"Processing record {index + 1}/50")
                
                df['Baseline_Pred'] = baseline_preds
                df['LLM_Pred'] = llm_preds
                baseline_acc = (df['Baseline_Pred'] == df['True_Category']).mean() * 100
                llm_acc = (df['LLM_Pred'] == df['True_Category']).mean() * 100
                
                col_res1, col_res2 = st.columns(2)
                col_res1.metric("GenAI Model Accuracy", f"{llm_acc:.1f}%")
                col_res2.metric("Legacy Model Accuracy", f"{baseline_acc:.1f}%")
                
                st.markdown("**Resolution Log: Edge Cases**")
                edge_cases = df[(df['Baseline_Pred'] != df['True_Category']) & (df['LLM_Pred'] == df['True_Category'])]
                st.dataframe(edge_cases[['Message', 'True_Category', 'Baseline_Pred', 'LLM_Pred']], use_container_width=True)
                
            except FileNotFoundError:
                st.error("System Error: 'patient_messages.csv' missing from directory.")