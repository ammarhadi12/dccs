import streamlit as st
import pandas as pd
import re
import os
from io import BytesIO, StringIO
from datetime import datetime, timedelta

APP_PASSWORD = os.getenv("APP_PASSWORD")

st.title("🔐 Internal Access Only")

password = st.text_input("Enter password to continue:", type="password")

if password != APP_PASSWORD:
    st.warning("Access denied 🚫 — please enter the correct password to continue.")
    st.stop()

st.success("Access granted ✅ Welcome!")

st.set_page_config(page_title="Ticket Date Adjuster", layout="wide")
st.title("📅 Ticket Date Adjuster — Paste Only")
st.write("Paste your ticket text (no upload). The tool will apply your exact minus-rules and return a processed table + downloadable Excel.")

# ---------------------------
# Hard-coded mapping from the list you provided.
# Keys are normalized (upper, trimmed). Multiple names separated by newline are split into individual keys.
# ---------------------------
raw_mapping_text = r"""
DEV.RAW.NMMS_dcsresourcecompliance	NOT FOUND
DEV.RAW.NMMS_DIPCLMP	NOT FOUND
DEV.RAW.NMMS_MPLMP_DAP	NOT FOUND
DEV.RAW.NMMS_MPLMP_HAP	NOT FOUND
DEV.RAW.NMMS_MPLMP_WAP	NOT FOUND
DEV.RAW.NMMS_MPREGIONALSUMMARY_DAP	NOT FOUND
DEV.RAW.NMMS_MPREGIONALSUMMARY_HAP	NOT FOUND
DEV.RAW.NMMS_MPREGIONALSUMMARY_WAP	NOT FOUND
DEV.RAW.NMMS_MPRESERVESCHEDULE_DAP	NOT FOUND
DEV.RAW.NMMS_MPRESERVESCHEDULE_HAP	NOT FOUND
DEV.RAW.NMMS_MPRESERVESCHEDULE_WAP	NOT FOUND
DEV.RAW.NMMS_MPSCHEDULES_DAP	NOT FOUND
DEV.RAW.NMMS_MPSCHEDULES_HAP	NOT FOUND
DEV.RAW.NMMS_MPSCHEDULES_WAP	NOT FOUND
DEV.RAW.NMMS_occresourcecompliancedetail	NOT FOUND
DEV.RAW.NMMS_OCCRESOURCECOMPLIANCEHOUR	NOT FOUND
pub_hvdc_limit_wap	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_constraint_violation_hap
DEV.RAW.NMMS_pub_constraint_violation_hap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_constraint_violation_rtd
DEV.RAW.NMMS_pub_constraint_violation_rtd_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_constraint_violation_wap
DEV.RAW.NMMS_pub_constraint_violation_wap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_gwap
DEV.RAW.NMMS_pub_gwap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_hvdc_limit_dap
DEV.RAW.NMMS_pub_hvdc_limit_dap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_hvdc_limit_hap
DEV.RAW.NMMS_pub_hvdc_limit_hap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_hvdc_limit_rtd
DEV.RAW.NMMS_pub_hvdc_limit_rtd_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_hvdc_limit_wap
DEV.RAW.NMMS_pub_hvdc_limit_wap_reject"	Daily_2days_Ago
"DEV.RAW.NMMS_pub_hvdc_schedules_dap
DEV.RAW.NMMS_pub_hvdc_schedules_dap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_hvdc_schedules_hap
DEV.RAW.NMMS_pub_hvdc_schedules_hap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_hvdc_schedules_rtd
DEV.RAW.NMMS_pub_hvdc_schedules_rtd_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_hvdc_schedules_wap
DEV.RAW.NMMS_pub_hvdc_schedules_wap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_LWAP
DEV.RAW.NMMS_pub_LWAP_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_market_bids_and_offer_energy
DEV.RAW.NMMS_pub_market_bids_and_offer_energy_reject"	7days_Ago
"DEV.RAW.NMMS_pub_market_bids_and_offer_nomination
DEV.RAW.NMMS_pub_market_bids_and_offer_nomination_reject"	7days_Ago
"DEV.RAW.NMMS_pub_market_bids_and_offer_reserve
DEV.RAW.NMMS_pub_market_bids_and_offer_reserve_reject"	7days_Ago
"DEV.RAW.NMMS_pub_market_clearing_price
DEV.RAW.NMMS_pub_market_clearing_price_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_market_projections_dap
DEV.RAW.NMMS_pub_market_projections_dap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_market_projections_hap
DEV.RAW.NMMS_pub_market_projections_hap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_market_projections_wap
DEV.RAW.NMMS_pub_market_projections_wap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_pmrc
DEV.RAW.NMMS_pub_pmrc_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_realtime_dispatch_prices_and_schedules
DEV.RAW.NMMS_pub_realtime_dispatch_prices_and_schedules_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_realtime_dispatch_reserve_schedules
DEV.RAW.NMMS_pub_realtime_dispatch_reserve_schedules_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_regional_summary_dap
DEV.RAW.NMMS_pub_regional_summary_dap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_regional_summary_hap
DEV.RAW.NMMS_pub_regional_summary_hap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_regional_summary_rtd
DEV.RAW.NMMS_pub_regional_summary_rtd_reject"	Set_Date_Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_regional_summary_wap
DEV.RAW.NMMS_pub_regional_summary_wap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_security_limit_dap
DEV.RAW.NMMS_pub_security_limit_dap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_security_limit_hap
DEV.RAW.NMMS_pub_security_limit_hap_reject"	Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_security_limit_rtd
DEV.RAW.NMMS_pub_security_limit_rtd_reject"	Set_Date_Daily_2_and_1days_Ago
"DEV.RAW.NMMS_pub_security_limit_wap
DEV.RAW.NMMS_pub_security_limit_wap_reject"	Daily_2_and_1days_Ago
DEV.RAW.NMMS_RTDLMP	NOT FOUND
DEV.RAW.NMMS_RTDREGIONALSUMMARY	NOT FOUND
DEV.RAW.NMMS_RTDRESERVESCHEDULE	NOT FOUND
DEV.RAW.NMMS_RTDSCHEDULES	NOT FOUND
DEV.RAW.NMMS_TIPCLMP	NOT FOUND
DEV.RAW.NMMS_PUB_MOT_FILES	Daily
"""

def build_mapping(raw_text):
    rules = {}
    for line in [l.strip() for l in raw_text.splitlines() if l.strip()]:
        # split at last tab or multiple spaces
        parts = re.split(r"\t+", line)
        if len(parts) == 1:
            parts = re.split(r"\s{2,}", line)
        if len(parts) >= 2:
            key_part = parts[0].strip().strip('"')
            val_part = parts[-1].strip()
            # key_part may contain newline-separated multiple keys, split them
            keys = [k.strip().strip('"') for k in re.split(r"\n+", key_part) if k.strip()]
            for k in keys:
                # normalize
                norm = k.upper()
                rules[norm] = val_part
    return rules

MAPPING = build_mapping(raw_mapping_text)

# mapping to days-to-subtract based on your rule
rule_to_days = {
    "DAILY": 0,
    "DAILY_2_AND_1DAYS_AGO": 1,
    "SET_DATE_DAILY_2_AND_1DAYS_AGO": 1,
    "7DAYS_AGO": 7,
    "NOT FOUND": None
}

# Initialize session state for tracking rerun status
if 'rerun_status' not in st.session_state:
    st.session_state.rerun_status = {}

st.markdown("**Paste ticket (exact text).** Each data row should start with a row number and the `DATE` (YYYY-MM-DD).")
ticket_text = st.text_area("Paste ticket text here:", height=360, placeholder="Paste ticket rows...")

def normalize_table_name(name: str):
    if not isinstance(name, str):
        return ""
    n = name.strip().upper()
    # if user pasted a short name (no DEV.RAW), add a suffix match attempt later
    return n

def find_rule_for_table(table_name: str):
    """
    Try various matching strategies:
      1) exact match on normalized name
      2) try adding or removing DEV.RAW. prefix
      3) substring match (mapping key in table_name or table_name in mapping key)
    """
    n = table_name.upper()
    # exact
    if n in MAPPING:
        return MAPPING[n]
    # try with DEV.RAW. prefix
    if not n.startswith("DEV.RAW.") and f"DEV.RAW.{n}" in MAPPING:
        return MAPPING[f"DEV.RAW.{n}"]
    # try without DEV.RAW.
    if n.startswith("DEV.RAW.") and n.replace("DEV.RAW.", "") in MAPPING:
        return MAPPING[n.replace("DEV.RAW.", "")]
    # substring matches (prefer longer mapping keys)
    for k in sorted(MAPPING.keys(), key=lambda x:-len(x)):
        if k in n or n in k:
            return MAPPING[k]
    return None

def parse_ticket_lines(text: str):
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    data_lines = []
    for ln in lines:
        # pick lines that begin with an index number and a date YYYY-MM-DD (as your sample)
        if re.match(r"^\s*\d+\s+\d{4}-\d{2}-\d{2}", ln):
            data_lines.append(ln)
    # split rows by two or more spaces (keeps table name intact)
    rows = []
    for ln in data_lines:
        parts = re.split(r"\s{2,}", ln)
        # if splitting didn't work (maybe single spaces), fallback to whitespace split but keep first 3 col grouping
        if len(parts) < 3:
            parts = re.split(r"\s+", ln, maxsplit=7)
        rows.append(parts)
    return rows

if st.button("🔁 Process pasted ticket"):
    if not ticket_text.strip():
        st.warning("Paste the ticket text first.")
    else:
        try:
            rows = parse_ticket_lines(ticket_text)
            if not rows:
                st.error("No data rows found. Make sure each data row starts with a number and a date (YYYY-MM-DD).")
            else:
                # Build a DataFrame with flexible columns
                max_cols = max(len(r) for r in rows)
                col_names = ["IDX", "DATE", "TABLE_NAME"] + [f"COL_{i}" for i in range(4, max_cols+1)]
                normalized_rows = []
                for r in rows:
                    # pad
                    r_padded = r + [""] * (max_cols - len(r))
                    rowd = dict(zip(col_names, r_padded))
                    normalized_rows.append(rowd)
                orig_df = pd.DataFrame(normalized_rows)

                # compute mapping and rerun date
                outputs = []
                for _, r in orig_df.iterrows():
                    tbl = str(r["TABLE_NAME"]).strip()
                    norm_tbl = normalize_table_name(tbl)
                    rule = find_rule_for_table(norm_tbl)
                    status = ""
                    original_date_formatted = ""
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
                                # Format as YYYYMMDD for TMC
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

                processed_df = pd.DataFrame(outputs)
                st.session_state.processed_df = processed_df
                st.session_state.orig_df = orig_df
                # Reset rerun status when new ticket is processed
                st.session_state.rerun_status = {}

        except Exception as e:
            st.error(f"Processing error: {e}")
            st.info("Ensure rows start with index number and date like: `1 2025-10-23 NMMS_PUB_...`")

# Display results if processed
if 'processed_df' in st.session_state:
    st.subheader("Original (parsed preview)")
    st.dataframe(st.session_state.orig_df, use_container_width=True)

    st.subheader("Processed (with RERUN_DATE and Status)")
    
    # Add custom CSS for copy button
    st.markdown("""
    <style>
    .copy-btn {
        cursor: pointer;
        padding: 4px 8px;
        background: transparent;
        border: none;
        font-size: 16px;
    }
    .copy-btn:hover {
        opacity: 0.7;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display headers
    col1, col2, col3, col4, col5, col6 = st.columns([0.4, 0.6, 3, 1.2, 2, 1.5])
    with col1:
        st.markdown("**✓**")
    with col2:
        st.markdown("**IDX**")
    with col3:
        st.markdown("**TABLE NAME**")
    with col4:
        st.markdown("**ORIGINAL DATE**")
    with col5:
        st.markdown("**RERUN DATE**")
    with col6:
        st.markdown("**RULE**")
    
    st.markdown("---")
    
    # Display processed data with interactive controls
    for idx, row in st.session_state.processed_df.iterrows():
        row_key = f"{idx}_{row['TABLE_NAME']}_{row['RERUN_DATE']}"
        
        # Get current status, default to False (unchecked/red)
        is_completed = st.session_state.rerun_status.get(row_key, False)
        
        # Color coding: green for completed, red for not completed
        bg_color = "#d4edda" if is_completed else "#f8d7da"
        
        col1, col2, col3, col4, col5, col6 = st.columns([0.4, 0.6, 3, 1.2, 2, 1.5])
        
        with col1:
            # Checkbox that updates status immediately
            new_status = st.checkbox("", value=is_completed, key=f"check_{row_key}", label_visibility="collapsed")
            if new_status != is_completed:
                st.session_state.rerun_status[row_key] = new_status
                st.rerun()
        
        with col2:
            st.markdown(f"<div style='background-color:{bg_color}; padding:10px; border-radius:4px; text-align:center;'><b>{row['IDX']}</b></div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"<div style='background-color:{bg_color}; padding:10px; border-radius:4px;'><b>{row['TABLE_NAME']}</b></div>", unsafe_allow_html=True)
        
        with col4:
            original_display = row['ORIGINAL_DATE'] if row['ORIGINAL_DATE'] else "-"
            st.markdown(f"<div style='background-color:{bg_color}; padding:10px; border-radius:4px; text-align:center;'>{original_display}</div>", unsafe_allow_html=True)
        
        with col5:
            if row['RERUN_DATE']:
                # Create HTML with copy functionality using clipboard API
                st.markdown(f"""
                <div style='background-color:{bg_color}; padding:10px; border-radius:4px;'>
                    <span style='font-weight:bold; font-size:18px;'>{row['RERUN_DATE']}</span>
                    <button class='copy-btn' onclick='
                        navigator.clipboard.writeText("{row["RERUN_DATE"]}");
                        this.innerHTML = "✓";
                        setTimeout(() => this.innerHTML = "📋", 1000);
                    ' title='Click to copy'>📋</button>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background-color:{bg_color}; padding:10px; border-radius:4px; text-align:center;'>-</div>", unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"<div style='background-color:{bg_color}; padding:10px; border-radius:4px; font-size:0.85em;'>{row['Mapped_Rule']}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Legend:** 🔴 Red = Not yet rerun | 🟢 Green = Already rerun | Check the box to mark as complete")
    
    # prepare Excel with two sheets
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
st.markdown("**Notes:**\n- Click 📋 beside rerun date to instantly copy to clipboard\n- Check ✓ to mark as completed → **Green** = Done, **Red** = Pending\n- If table shows \"NOT IN THE LOGIC, REFER SHEET\" - check the mapping sheet for correct table name")