import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Fintech Reconciliation Tool",
    layout="wide",
)

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
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
[data-testid="stMetric"] {
    background-color: rgba(255,255,255,0.03);
    padding: 16px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("💳 Fintech Reconciliation Tool")
st.caption("Upload Platform & Bank datasets → Detect mismatches instantly")

col1, col2 = st.columns(2)

with col1:
    file_a = st.file_uploader("📂 Upload Platform CSV", type=["csv"])

with col2:
    file_b = st.file_uploader("🏦 Upload Bank CSV", type=["csv"])


def format_view(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = [
        "transaction_id",
        "date_A", "amount_A", "type_A", "reference_A",
        "date_B", "amount_B", "type_B", "reference_B",
        "status"
    ]
    available_cols = [c for c in required_cols if c in df.columns]

    return df[available_cols].rename(columns={
        "date_A": "Platform Date",
        "amount_A": "Platform Amount",
        "type_A": "Platform Type",
        "reference_A": "Platform Ref",
        "date_B": "Bank Date",
        "amount_B": "Bank Amount",
        "type_B": "Bank Type",
        "reference_B": "Bank Ref",
        "status": "Status"
    })


def show_table_or_empty(df: pd.DataFrame, empty_message: str):
    if df.empty:
        st.success(empty_message)
    else:
        st.dataframe(format_view(df), use_container_width=True)


if file_a and file_b:
    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)

    # Clean types
    df_a["amount"] = pd.to_numeric(df_a["amount"], errors="coerce")
    df_b["amount"] = pd.to_numeric(df_b["amount"], errors="coerce")

    df_a["date"] = pd.to_datetime(df_a["date"], errors="coerce")
    df_b["date"] = pd.to_datetime(df_b["date"], errors="coerce")

    total_a = round(df_a["amount"].sum(), 2)
    total_b = round(df_b["amount"].sum(), 2)
    diff = round(total_b - total_a, 2)

    st.subheader("💰 Summary")
    m1, m2, m3 = st.columns(3)
    m1.metric("Platform Total", f"₹{total_a:,.2f}")
    m2.metric("Bank Total", f"₹{total_b:,.2f}")
    m3.metric("Difference (Bank - Platform)", f"₹{diff:,.2f}")

    if diff != 0:
        st.error("🚨 Mismatch detected — investigate discrepancies below")
    else:
        st.success("✅ Perfect match — no discrepancies")

    st.divider()

    # Merge
    merged = df_a.merge(
        df_b,
        on="transaction_id",
        how="outer",
        suffixes=("_A", "_B"),
        indicator=True
    )

    merged["status"] = "Matched"
    merged.loc[merged["_merge"] == "left_only", "status"] = "Missing in Bank"
    merged.loc[merged["_merge"] == "right_only", "status"] = "Missing in Platform"

    # Missing in Bank
    missing_bank = merged[merged["status"] == "Missing in Bank"].copy()

    # Missing in Platform
    missing_platform = merged[merged["status"] == "Missing in Platform"].copy()

    # Duplicate in Bank
    dup_bank_rows = df_b[df_b.duplicated("transaction_id", keep=False)].copy()
    duplicate_counts = dup_bank_rows.groupby("transaction_id").size().reset_index(name="count")
    duplicates = merged.merge(duplicate_counts, on="transaction_id", how="inner").copy()
    duplicates["status"] = "Duplicate"

    # Keep one row per duplicated transaction for display logic
    duplicates = duplicates.drop_duplicates(subset=["transaction_id"])

    # Rounding differences
    rounding = merged[
        (merged["amount_A"].notna()) &
        (merged["amount_B"].notna()) &
        (abs(merged["amount_A"] - merged["amount_B"]) < 1) &
        (merged["amount_A"] != merged["amount_B"])
    ].copy()
    rounding["status"] = "Rounding Difference"

    # Timing differences
    timing = merged[
        (merged["date_A"].notna()) &
        (merged["date_B"].notna()) &
        (
            (merged["date_A"].dt.month != merged["date_B"].dt.month) |
            (merged["date_A"].dt.year != merged["date_B"].dt.year)
        )
    ].copy()
    timing["status"] = "Timing Difference"

    # Orphan refunds
    payment_refs = set(df_a[df_a["type"].str.lower() == "payment"]["reference"].dropna())
    refunds = df_a[
        (df_a["type"].str.lower() == "refund") &
        (~df_a["reference"].isin(payment_refs))
    ].copy()

    # ---------------------------
    # IMPACT CALCULATION
    # ---------------------------

    duplicate_impact = 0.0
    if not dup_bank_rows.empty:
        dup_calc = dup_bank_rows.groupby("transaction_id")["amount"].agg(["count", "first"]).reset_index()
        dup_calc["extra_count"] = dup_calc["count"] - 1
        dup_calc["impact"] = dup_calc["extra_count"] * dup_calc["first"]
        duplicate_impact = round(dup_calc["impact"].sum(), 2)

    rounding_impact = 0.0
    if not rounding.empty:
        rounding_impact = round((rounding["amount_B"] - rounding["amount_A"]).sum(), 2)

    orphan_refund_impact = 0.0
    if not refunds.empty:
        orphan_refund_impact = round(-refunds["amount"].sum(), 2)

    timing_impact = 0.0
    if not timing.empty:
        timing_impact = round((timing["amount_B"] - timing["amount_A"]).sum(), 2)

    missing_bank_impact = 0.0
    if not missing_bank.empty:
        missing_bank_impact = round(-missing_bank["amount_A"].fillna(0).sum(), 2)

    missing_platform_impact = 0.0
    if not missing_platform.empty:
        missing_platform_impact = round(missing_platform["amount_B"].fillna(0).sum(), 2)

    # Displayed formula using issue buckets
    # Note: timing already reflects bank-platform for matched transactions across periods
    explained_difference = round(
        duplicate_impact
        + rounding_impact
        + orphan_refund_impact
        + missing_bank_impact
        + missing_platform_impact,
        2
    )

    st.subheader("📊 Discrepancy Impact Summary")

    c1, c2, c3 = st.columns(3)
    c1.metric("Duplicate Impact", f"₹{duplicate_impact:,.2f}")
    c2.metric("Rounding Impact", f"₹{rounding_impact:,.2f}")
    c3.metric("Orphan Refund Impact", f"₹{orphan_refund_impact:,.2f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Missing in Bank Impact", f"₹{missing_bank_impact:,.2f}")
    c5.metric("Missing in Platform Impact", f"₹{missing_platform_impact:,.2f}")
    c6.metric("Explained Difference", f"₹{explained_difference:,.2f}")

    st.markdown("### 🧮 Formula Used")
    st.code(
        f"""Difference (Bank - Platform) = 
Duplicate Impact + Rounding Impact + Orphan Refund Impact + Missing in Bank Impact + Missing in Platform Impact

= {duplicate_impact:,.2f} + {rounding_impact:,.2f} + ({orphan_refund_impact:,.2f}) + ({missing_bank_impact:,.2f}) + {missing_platform_impact:,.2f}
= {explained_difference:,.2f}""",
        language="text"
    )

    if round(diff, 2) == round(explained_difference, 2):
        st.success("✅ The discrepancy formula matches the total difference.")
    else:
        st.warning(
            f"⚠️ Total difference is ₹{diff:,.2f}, but explained discrepancy is ₹{explained_difference:,.2f}. "
            "This usually means some cases overlap or need more precise business rules."
        )

    st.markdown("### 📝 Why is the amount mismatched?")
    reasons = []

    if duplicate_impact != 0:
        reasons.append(f"- Bank has duplicate transaction(s), adding **₹{duplicate_impact:,.2f}** extra.")
    if rounding_impact != 0:
        reasons.append(f"- Small row-level rounding differences add up to **₹{rounding_impact:,.2f}**.")
    if orphan_refund_impact != 0:
        reasons.append(f"- Platform has orphan refund(s), reducing total by **₹{abs(orphan_refund_impact):,.2f}**.")
    if missing_bank_impact != 0:
        reasons.append(f"- Some transaction(s) exist in Platform but not in Bank, impacting total by **₹{missing_bank_impact:,.2f}**.")
    if missing_platform_impact != 0:
        reasons.append(f"- Some transaction(s) exist in Bank but not in Platform, impacting total by **₹{missing_platform_impact:,.2f}**.")
    if timing_impact != 0:
        reasons.append(f"- Timing differences exist across periods. Net timing delta on matched rows is **₹{timing_impact:,.2f}**.")

    if reasons:
        st.markdown("\n".join(reasons))
    else:
        st.info("No discrepancy drivers found. Both datasets appear matched.")

    st.divider()

    st.subheader("🔍 Discrepancy Breakdown")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "❌ Missing (Bank)",
        "❌ Missing (Platform)",
        "🔁 Duplicates",
        "💸 Rounding",
        "⏳ Timing"
    ])

    with tab1:
        show_table_or_empty(missing_bank, "✅ No transactions missing in Bank")

    with tab2:
        show_table_or_empty(missing_platform, "✅ No transactions missing in Platform")

    with tab3:
        show_table_or_empty(duplicates, "✅ No duplicate transactions found")

    with tab4:
        show_table_or_empty(rounding, "✅ No rounding differences found")

    with tab5:
        show_table_or_empty(timing, "✅ No timing differences found")

    st.subheader("⚠️ Orphan Refunds")
    if refunds.empty:
        st.success("✅ No orphan refunds found")
    else:
        st.dataframe(refunds, use_container_width=True)

    st.success("✅ Reconciliation Completed")

else:
    st.info("👆 Upload both Platform & Bank CSV files to begin")
