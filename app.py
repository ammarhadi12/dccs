import streamlit as st
import pandas as pd
from pathlib import Path
import os
import re
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="RerunAI — Ticket Date Adjuster", layout="wide", page_icon="⚡")

# ---------------------------------------------------------------------------
# THEME / STYLE — "AI startup" look: dark base, gradient accents, glass cards
# ---------------------------------------------------------------------------
def inject_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

        :root {
            --bg-0: #0b0e14;
            --bg-1: #11151f;
            --bg-2: #171c29;
            --border: rgba(255,255,255,0.08);
            --text-1: #f2f4f8;
            --text-2: #9aa3b5;
            --accent-1: #7c5cff;
            --accent-2: #22d3ee;
            --ok: #22c55e;
            --warn: #ef4444;
            --gradient: linear-gradient(90deg, var(--accent-1), var(--accent-2));
        }

        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: radial-gradient(circle at 20% -10%, #1a1f33 0%, var(--bg-0) 45%) fixed;
            color: var(--text-1);
        }

        h1, h2, h3, .hero-title {
            font-family: 'Space Grotesk', sans-serif !important;
        }

        /* ---------- Hero section ---------- */
        .hero-wrap {
            padding: 2.2rem 2rem 1.8rem 2rem;
            border-radius: 20px;
            border: 1px solid var(--border);
            background: linear-gradient(135deg, rgba(124,92,255,0.10), rgba(34,211,238,0.06));
            margin-bottom: 1.6rem;
        }
        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 14px;
            border-radius: 999px;
            background: rgba(124,92,255,0.15);
            border: 1px solid rgba(124,92,255,0.35);
            color: #c9bdff;
            font-size: 0.78rem;
            font-weight: 500;
            letter-spacing: 0.02em;
            margin-bottom: 14px;
        }
        .hero-title {
            font-size: 2.4rem;
            font-weight: 700;
            line-height: 1.15;
            margin: 0 0 8px 0;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero-sub {
            color: var(--text-2);
            font-size: 1.02rem;
            max-width: 640px;
            margin-bottom: 0;
        }

        /* ---------- Stat / glass cards ---------- */
        .stat-row { display: flex; gap: 14px; margin-top: 20px; flex-wrap: wrap; }
        .glass-card {
            flex: 1;
            min-width: 150px;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 18px;
            backdrop-filter: blur(6px);
        }
        .glass-card .num {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--text-1);
        }
        .glass-card .lbl {
            color: var(--text-2);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        /* ---------- Section headers ---------- */
        .section-label {
            display: inline-block;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--accent-2);
            font-weight: 600;
            margin-bottom: 4px;
        }

        /* ---------- Streamlit widget overrides ---------- */
        .stTextArea textarea {
            background: var(--bg-2) !important;
            color: var(--text-1) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            font-family: 'Inter', monospace;
        }
        .stButton > button {
            background: var(--gradient) !important;
            color: #0b0e14 !important;
            font-weight: 600 !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.55rem 1.4rem !important;
            transition: transform 0.15s ease, opacity 0.15s ease;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            opacity: 0.92;
        }
        .stDownloadButton > button {
            background: transparent !important;
            color: var(--accent-2) !important;
            border: 1px solid rgba(34,211,238,0.4) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        .stExpander {
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            background: rgba(255,255,255,0.02);
        }
        .status-chip {
            display: inline-block;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
            text-align: center;
            width: 100%;
        }
        .status-chip.done { background: rgba(34,197,94,0.16); color: #4ade80; border: 1px solid rgba(34,197,94,0.35); }
        .status-chip.pending { background: rgba(239,68,68,0.14); color: #f87171; border: 1px solid rgba(239,68,68,0.35); }
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

inject_theme()

# ---------------------------------------------------------------------------
# AUTH GATE
# ---------------------------------------------------------------------------
def check_password():
    def password_entered():
        if st.session_state["password"] == os.getenv("APP_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown('<div class="badge-pill">🔒 Secure Access</div>', unsafe_allow_html=True)
        st.text_input("Enter Password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown('<div class="badge-pill">🔒 Secure Access</div>', unsafe_allow_html=True)
        st.text_input("Enter Password:", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ---------------------------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-wrap">
    <div class="badge-pill">⚡ Internal Automation Tool</div>
    <div class="hero-title">RerunAI — Ticket Date Adjuster</div>
    <p class="hero-sub">Paste raw DCCS/ServiceDesk email text and instantly resolve the correct TMC rerun date
    for every affected table — no manual date math, no lookup spreadsheets.</p>
    <div class="stat-row">
        <div class="glass-card"><div class="num">60+</div><div class="lbl">Mapped Tables</div></div>
        <div class="glass-card"><div class="num">5</div><div class="lbl">Rerun Rules</div></div>
        <div class="glass-card"><div class="num">&lt;1s</div><div class="lbl">Processing Time</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("ℹ️ How to Copy & Paste DCCS Emails", expanded=False):
    st.markdown("""
    **Step 1 — Copy from Gmail / Outlook**
    Open your DCCS notification email, select all text (**Ctrl+A**), and copy (**Ctrl+C**).

    **Step 2 — Paste into the tool**
    Paste directly into the text area below (**Ctrl+V**). 

    The parser automatically uses regular expressions to extract `IDX`, `DATE`, and `TABLE_NAME` while ignoring headers and trailing criteria fields!
    """)

st.markdown('<div class="section-label">Input</div>', unsafe_allow_html=True)
st.markdown("Paste your raw email text below — no file upload or IT admin access needed.")

# ---------------------------------------------------------------------------
# MAPPING RULES
# ---------------------------------------------------------------------------

@st.cache_data
def load_mapping():
    path = Path(__file__).parent / "data" / "mapping_rules.csv"
    df = pd.read_csv(path)
    df["table_name"] = df["table_name"].astype(str).str.strip().str.upper()
    df["rule"] = df["rule"].astype(str).str.strip()
    mapping_dict = dict(zip(df["table_name"], df["rule"]))
    return mapping_dict, df

MAPPING, mapping_source_df = load_mapping()

rule_to_days = {
    "DAILY": 0,
    "SET_DATE_DAILY": 0,
    "DAILY_2_AND_1DAYS_AGO": 1,
    "SET_DATE_DAILY_2_AND_1DAYS_AGO": 1,
    "7DAYS_AGO": 7,
    "NOT FOUND": None
}

if 'rerun_status' not in st.session_state:
    st.session_state.rerun_status = {}

ticket_text = st.text_area("Paste email text here:", height=240, placeholder="Good day!\n\nPlease be informed that there are flagged missing/null values...\n\n1 2026-09-16 NMMS_DCSRESOURCECOMPLIANCE 520.0...")

def normalize_table_name(name: str):
    if not isinstance(name, str):
        return ""
    return name.strip().upper()

def find_rule_for_table(table_name: str):
    n = table_name.upper()
    if n in MAPPING:
        return MAPPING[n]
    if not n.startswith("DEV.RAW.") and f"DEV.RAW.{n}" in MAPPING:
        return MAPPING[f"DEV.RAW.{n}"]
    if n.startswith("DEV.RAW.") and n.replace("DEV.RAW.", "") in MAPPING:
        return MAPPING[n.replace("DEV.RAW.", "")]
    for k in sorted(MAPPING.keys(), key=lambda x: -len(x)):
        if k in n or n in k:
            return MAPPING[k]
    return None

def parse_ticket_lines(text: str):
    """
    Handles continuous, unspaced text copied from HTML tables.
    Matches:
      - Group 1: 1 or 2 digit index
      - Group 2: YYYY-MM-DD date
      - Group 3: Table name (starts with NMMS_, ends before the metric numbers)
    """
    # Look for 1-2 digits, followed by a date, followed by NMMS_ and valid identifier characters
    pattern = r"(\d{1,2})(\d{4}-\d{2}-\d{2})(NMMS_[A-Za-z0-9_]+?)(?=\d|\s|$)"
    matches = re.findall(pattern, text)
    
    rows = []
    for match in matches:
        idx, date_str, table_name = match
        rows.append([idx, date_str, table_name.strip()])
        
    return rows

col_run, _ = st.columns([1, 5])
with col_run:
    run_clicked = st.button("⚡ Process Ticket")

if run_clicked:
    if not ticket_text.strip():
        st.warning("Paste the email text first.")
    else:
        try:
            rows = parse_ticket_lines(ticket_text)
            if not rows:
                st.error("No valid table rows detected. Make sure the text contains entries like: `1 2026-09-16 NMMS_...`")
            else:
                col_names = ["IDX", "DATE", "TABLE_NAME"]
                normalized_rows = [dict(zip(col_names, r)) for r in rows]
                orig_df = pd.DataFrame(normalized_rows)

                outputs = []
                for _, r in orig_df.iterrows():
                    tbl = str(r["TABLE_NAME"]).strip()
                    norm_tbl = normalize_table_name(tbl)
                    rule = find_rule_for_table(norm_tbl)
                    date_str = str(r["DATE"]).strip()
                    original_date_formatted = date_str

                    if rule is None:
                        status = "NOT IN THE LOGIC, REFER SHEET"
                        rerun = ""
                    else:
                        rule_key = rule.strip().upper()
                        days = rule_to_days.get(rule_key, None)
                        if days is None:
                            status = "NOT IN THE LOGIC, REFER SHEET"
                            rerun = ""
                        else:
                            try:
                                dt = datetime.strptime(date_str, "%Y-%m-%d")
                                rerun_dt = dt - timedelta(days=days)
                                rerun = rerun_dt.strftime("%Y%m%d")
                                status = "OK"
                            except Exception as e:
                                rerun = ""
                                status = f"bad date format: {e}"
                    out = r.to_dict()
                    out.update({
                        "ORIGINAL_DATE": original_date_formatted,
                        "Mapped_Rule": rule if rule is not None else "",
                        "RERUN_DATE": rerun,
                        "Status": status
                    })
                    outputs.append(out)

                st.session_state.processed_df = pd.DataFrame(outputs)
                st.session_state.orig_df = orig_df
                st.session_state.rerun_status = {}

        except Exception as e:
            st.error(f"Processing error: {e}")

# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------
if 'processed_df' in st.session_state:
    st.markdown('<div class="section-label">Parsed Input</div>', unsafe_allow_html=True)
    st.dataframe(st.session_state.orig_df, use_container_width=True)

    st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)
    st.markdown("Rerun dates calculated below. Mark each as done once processed in TMC.")

    col1, col2, col3, col4, col5, col6 = st.columns([0.4, 0.6, 3, 1.2, 2, 1.5])
    for c, label in zip([col1, col2, col3, col4, col5, col6],
                          ["✓", "IDX", "TABLE NAME", "ORIGINAL DATE", "RERUN DATE", "RULE"]):
        c.markdown(f"**{label}**")
    st.markdown("---")

    for idx, row in st.session_state.processed_df.iterrows():
        row_key = f"{idx}_{row['TABLE_NAME']}_{row['RERUN_DATE']}"
        is_completed = st.session_state.rerun_status.get(row_key, False)
        chip_class = "done" if is_completed else "pending"

        col1, col2, col3, col4, col5, col6 = st.columns([0.4, 0.6, 3, 1.2, 2, 1.5])

        with col1:
            new_status = st.checkbox("", value=is_completed, key=f"check_{row_key}", label_visibility="collapsed")
            if new_status != is_completed:
                st.session_state.rerun_status[row_key] = new_status
                st.rerun()

        with col2:
            st.markdown(f"<div class='status-chip {chip_class}'>{row['IDX']}</div>", unsafe_allow_html=True)

        with col3:
            st.code(row['TABLE_NAME'], language=None)

        with col4:
            original_display = row['ORIGINAL_DATE'] if row['ORIGINAL_DATE'] else "-"
            st.markdown(f"<div class='status-chip {chip_class}'>{original_display}</div>", unsafe_allow_html=True)

        with col5:
            if row['RERUN_DATE']:
                st.code(row['RERUN_DATE'], language=None)
            else:
                st.markdown(f"<div class='status-chip {chip_class}'>-</div>", unsafe_allow_html=True)

        with col6:
            st.markdown(f"<div class='glass-card' style='padding:8px 12px; font-size:0.82em;'>{row['Mapped_Rule']}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Legend:** 🟢 Green = Already rerun · 🔴 Red = Not yet rerun · Check the box to mark complete")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state.orig_df.to_excel(writer, sheet_name="Original_Ticket", index=False)
        st.session_state.processed_df.to_excel(writer, sheet_name="Processed_Ticket", index=False)

    st.download_button(
        label="⬇️ Download Excel (Original + Processed)",
        data=output.getvalue(),
        file_name=f"tmc_rerun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")
st.markdown(
    "**Notes:** Check ✓ to mark completed. If a table shows *NOT IN THE LOGIC, REFER SHEET* — check the "
    "mapping table below. A blank result usually means the job is maintained by FGEN or the rule isn't mapped yet."
)

# ---------------------------------------------------------------------------
# MAPPING REFERENCE
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown('<div class="section-label">Reference</div>', unsafe_allow_html=True)
st.subheader("Table Mapping Rules")
st.markdown("Complete mapping logic used to calculate rerun dates.")

reference_data = [
    ("DEV.RAW.NMMS_dcsresourcecompliance", "NOT FOUND"),
    ("DEV.RAW.NMMS_DIPCLMP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPLMP_DAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPLMP_HAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPLMP_WAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPREGIONALSUMMARY_DAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPREGIONALSUMMARY_HAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPREGIONALSUMMARY_WAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPRESERVESCHEDULE_DAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPRESERVESCHEDULE_HAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPRESERVESCHEDULE_WAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPSCHEDULES_DAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPSCHEDULES_HAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_MPSCHEDULES_WAP", "NOT FOUND"),
    ("DEV.RAW.NMMS_occresourcecompliancedetail", "NOT FOUND"),
    ("DEV.RAW.NMMS_OCCRESOURCECOMPLIANCEHOUR", "NOT FOUND"),
    ("pub_hvdc_limit_wap", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_constraint_violation_hap + DEV.RAW.NMMS_pub_constraint_violation_hap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_constraint_violation_rtd + DEV.RAW.NMMS_pub_constraint_violation_rtd_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_constraint_violation_wap + DEV.RAW.NMMS_pub_constraint_violation_wap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_gwap + DEV.RAW.NMMS_pub_gwap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_limit_dap + DEV.RAW.NMMS_pub_hvdc_limit_dap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_limit_hap + DEV.RAW.NMMS_pub_hvdc_limit_hap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_limit_rtd + DEV.RAW.NMMS_pub_hvdc_limit_rtd_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_limit_wap + DEV.RAW.NMMS_pub_hvdc_limit_wap_reject", "Daily_2days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_schedules_dap + DEV.RAW.NMMS_pub_hvdc_schedules_dap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_schedules_hap + DEV.RAW.NMMS_pub_hvdc_schedules_hap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_schedules_rtd + DEV.RAW.NMMS_pub_hvdc_schedules_rtd_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_hvdc_schedules_wap + DEV.RAW.NMMS_pub_hvdc_schedules_wap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_LWAP + DEV.RAW.NMMS_pub_LWAP_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_market_bids_and_offer_energy + DEV.RAW.NMMS_pub_market_bids_and_offer_energy_reject", "7days_Ago"),
    ("DEV.RAW.NMMS_pub_market_bids_and_offer_nomination + DEV.RAW.NMMS_pub_market_bids_and_offer_nomination_reject", "7days_Ago"),
    ("DEV.RAW.NMMS_pub_market_bids_and_offer_reserve + DEV.RAW.NMMS_pub_market_bids_and_offer_reserve_reject", "7days_Ago"),
    ("DEV.RAW.NMMS_pub_market_clearing_price + DEV.RAW.NMMS_pub_market_clearing_price_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_market_projections_dap + DEV.RAW.NMMS_pub_market_projections_dap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_market_projections_hap + DEV.RAW.NMMS_pub_market_projections_hap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_market_projections_wap + DEV.RAW.NMMS_pub_market_projections_wap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_pmrc + DEV.RAW.NMMS_pub_pmrc_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_realtime_dispatch_prices_and_schedules + DEV.RAW.NMMS_pub_realtime_dispatch_prices_and_schedules_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_realtime_dispatch_reserve_schedules + DEV.RAW.NMMS_pub_realtime_dispatch_reserve_schedules_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_regional_summary_dap + DEV.RAW.NMMS_pub_regional_summary_dap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_regional_summary_hap + DEV.RAW.NMMS_pub_regional_summary_hap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_regional_summary_rtd + DEV.RAW.NMMS_pub_regional_summary_rtd_reject", "Set_Date_Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_regional_summary_wap + DEV.RAW.NMMS_pub_regional_summary_wap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_security_limit_dap + DEV.RAW.NMMS_pub_security_limit_dap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_security_limit_hap + DEV.RAW.NMMS_pub_security_limit_hap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_security_limit_rtd + DEV.RAW.NMMS_pub_security_limit_rtd_reject", "Set_Date_Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_pub_security_limit_wap + DEV.RAW.NMMS_pub_security_limit_wap_reject", "Daily_2_and_1days_Ago"),
    ("DEV.RAW.NMMS_RTDLMP", "NOT FOUND"),
    ("DEV.RAW.NMMS_RTDREGIONALSUMMARY", "NOT FOUND"),
    ("DEV.RAW.NMMS_RTDRESERVESCHEDULE", "NOT FOUND"),
    ("DEV.RAW.NMMS_RTDSCHEDULES", "NOT FOUND"),
    ("DEV.RAW.NMMS_TIPCLMP", "NOT FOUND"),
    ("DEV.RAW.NMMS_PUB_MOT_FILES", "Daily"),
    ("DEV.RAW.NMMS_ORIGINAL_LWAP", "Daily"),
    ("DEV.RAW.NMMS_PUB_OUTAGE_SCHEDULE_RTD", "Set_Date_Daily"),
]

mapping_display = []
for table, rule in reference_data:
    days_text = {
        "DAILY": "0 days (same date)",
        "SET_DATE_DAILY": "0 days (same date)",
        "DAILY_2_AND_1DAYS_AGO": "1 day",
        "SET_DATE_DAILY_2_AND_1DAYS_AGO": "1 day",
        "7DAYS_AGO": "7 days",
        "DAILY_2DAYS_AGO": "2 days",
        "NOT FOUND": "N/A"
    }.get(rule.upper().replace(" ", "_"), "N/A")
    mapping_display.append({
        "Target (Table Name)": table,
        "Target Data (Rule)": rule,
        "Days to Subtract": days_text
    })

mapping_df = pd.DataFrame(mapping_display)

st.markdown('<div class="section-label">Quick Stats</div>', unsafe_allow_html=True)
rule_stats = {}
for table, rule in reference_data:
    rule_stats[rule] = rule_stats.get(rule, 0) + 1

stat_cols = st.columns(6)
stat_defs = [
    ("Daily", "0 days"),
    ("Set_Date_Daily", "0 days"),
    ("Daily_2_and_1days_Ago", "1 day"),
    ("Set_Date_Daily_2_and_1days_Ago", "1 day"),
    ("7days_Ago", "7 days"),
    ("NOT FOUND", "Not configured"),
]
for c, (rule, help_text) in zip(stat_cols, stat_defs):
    c.metric(rule, rule_stats.get(rule, 0), help=help_text)

stat_cols2 = st.columns(2)
stat_cols2[0].metric("Daily_2days_Ago", rule_stats.get("Daily_2days_Ago", 0), help="2 days (not configured)")
stat_cols2[1].metric("Total Entries", len(reference_data), help="Paired tables counted once")

st.markdown("---")
st.dataframe(
    mapping_df,
    use_container_width=True,
    height=400,
    column_config={
        "Target (Table Name)": st.column_config.TextColumn("Target (Table Name)", width="large"),
        "Target Data (Rule)": st.column_config.TextColumn("Target Data (Rule)", width="medium"),
        "Days to Subtract": st.column_config.TextColumn("Days to Subtract", width="medium"),
    }
)

st.markdown("""
**Rule Definitions:**
- **Daily / Set_Date_Daily** — same date (0 days)
- **Daily_2_and_1days_Ago / Set_Date_Daily_2_and_1days_Ago** — subtract 1 day
- **Daily_2days_Ago** — subtract 2 days (not configured yet)
- **7days_Ago** — subtract 7 days
- **NOT FOUND** — table not configured for automatic rerun date calculation
""")

mapping_excel = BytesIO()
with pd.ExcelWriter(mapping_excel, engine="xlsxwriter") as writer:
    mapping_df.to_excel(writer, sheet_name="Mapping_Rules", index=False)

st.download_button(
    label="⬇️ Download Mapping Rules (Excel)",
    data=mapping_excel.getvalue(),
    file_name=f"mapping_rules_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)