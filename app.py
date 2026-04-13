import streamlit as st
import pandas as pd

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(
    page_title="Fintech Reconciliation Tool",
    layout="wide",
)

# ---------------------- DARK UI ----------------------
st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
h1, h2, h3 {
    color: #00d4ff;
}
.stButton>button {
    background-color: #00d4ff;
    color: black;
    border-radius: 8px;
}
.stDataFrame {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- HEADER ----------------------
st.title("💳 Fintech Reconciliation Tool")
st.caption("Upload Platform & Bank datasets → Detect mismatches instantly")

# ---------------------- FILE UPLOAD ----------------------
col1, col2 = st.columns(2)

with col1:
    file_a = st.file_uploader("📂 Upload Platform CSV", type=["csv"])

with col2:
    file_b = st.file_uploader("🏦 Upload Bank CSV", type=["csv"])

# ---------------------- PROCESS ----------------------
if file_a and file_b:
    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)

    # Ensure correct types
    df_a["amount"] = df_a["amount"].astype(float)
    df_b["amount"] = df_b["amount"].astype(float)

    # ---------------------- TOTALS ----------------------
    total_a = df_a["amount"].sum()
    total_b = df_b["amount"].sum()
    diff = round(total_b - total_a, 2)

    st.subheader("💰 Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Platform Total", f"₹{total_a:,.2f}")
    col2.metric("Bank Total", f"₹{total_b:,.2f}")
    col3.metric("Difference", f"₹{diff:,.2f}")

    # ✅ Mismatch Alert (Added)
    if diff != 0:
        st.error("🚨 Mismatch detected — investigate discrepancies below")
    else:
        st.success("✅ Perfect match — no discrepancies")

    st.divider()

    # ---------------------- MERGE ----------------------
    merged = df_a.merge(
        df_b,
        on="transaction_id",
        how="outer",
        suffixes=("_A", "_B"),
        indicator=True
    )

    # ---------------------- DISCREPANCIES ----------------------

    # Missing
    missing_bank = merged[merged["_merge"] == "left_only"]
    missing_platform = merged[merged["_merge"] == "right_only"]

    # Duplicates (Bank)
    dup_bank = df_b[df_b.duplicated("transaction_id", keep=False)]

    # Rounding
    rounding = merged[
        (merged["amount_A"].notna()) &
        (merged["amount_B"].notna()) &
        (abs(merged["amount_A"] - merged["amount_B"]) < 1) &
        (merged["amount_A"] != merged["amount_B"])
    ]

    # Timing
    merged["date_A"] = pd.to_datetime(merged["date_A"], errors='coerce')
    merged["date_B"] = pd.to_datetime(merged["date_B"], errors='coerce')

    timing = merged[
        (merged["date_A"].notna()) &
        (merged["date_B"].notna()) &
        (merged["date_A"].dt.month != merged["date_B"].dt.month)
    ]

    # Refunds (Orphan)
    refunds = df_a[
        (df_a["type"] == "refund") &
        (~df_a["reference"].isin(df_a[df_a["type"] == "payment"]["reference"]))
    ]

    # ---------------------- OUTPUT ----------------------

    st.subheader("🔍 Discrepancy Breakdown")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "❌ Missing (Bank)",
        "❌ Missing (Platform)",
        "🔁 Duplicates",
        "💸 Rounding",
        "⏳ Timing"
    ])

    with tab1:
        st.write("Transactions present in Platform but missing in Bank")
        st.dataframe(missing_bank, use_container_width=True)

    with tab2:
        st.write("Transactions present in Bank but missing in Platform")
        st.dataframe(missing_platform, use_container_width=True)

    with tab3:
        st.write("Duplicate Transactions in Bank")
        st.dataframe(dup_bank, use_container_width=True)

    with tab4:
        st.write("Rounding Differences")
        st.dataframe(rounding, use_container_width=True)

    with tab5:
        st.write("Settlement Timing Differences")
        st.dataframe(timing, use_container_width=True)

    # ---------------------- REFUND ----------------------
    st.subheader("⚠️ Orphan Refunds")
    st.dataframe(refunds, use_container_width=True)

    st.success("✅ Reconciliation Completed")

else:
    st.info("👆 Upload both Platform & Bank CSV files to begin")
