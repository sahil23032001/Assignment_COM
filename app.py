import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Payment Reconciliation Dashboard",
    layout="wide",
)

# ---------------------- STYLING ----------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0b1020 0%, #141b34 100%);
    color: #EAECEF;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}

h1, h2, h3 {
    color: #F8FAFC;
}

.subtle {
    color: #94A3B8;
    font-size: 0.95rem;
    margin-bottom: 1.25rem;
}

.card-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    margin-bottom: 28px;
}

.summary-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.25);
}

.summary-card.warning {
    background: linear-gradient(135deg, rgba(244,63,94,0.22), rgba(249,115,22,0.18));
    border: 1px solid rgba(244,63,94,0.30);
}

.summary-title {
    font-size: 0.82rem;
    color: #CBD5E1;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.summary-value {
    font-size: 2rem;
    font-weight: 700;
    color: white;
    margin-bottom: 6px;
}

.summary-label {
    font-size: 0.88rem;
    color: #CBD5E1;
}

.section-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 24px;
    margin-top: 18px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.22);
}

.gap-card {
    background: rgba(255,255,255,0.05);
    border-left: 5px solid #6366F1;
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    margin-bottom: 16px;
}

.gap-card.critical {
    border-left-color: #F43F5E;
}

.gap-card.warning {
    border-left-color: #F59E0B;
}

.gap-card.info {
    border-left-color: #38BDF8;
}

.gap-head {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 10px;
}

.gap-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #F8FAFC;
}

.gap-amount {
    font-size: 1.4rem;
    font-weight: 700;
    white-space: nowrap;
}

.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-left: 8px;
    vertical-align: middle;
}

.badge-critical {
    background: rgba(244,63,94,0.18);
    color: #FDA4AF;
}

.badge-warning {
    background: rgba(245,158,11,0.18);
    color: #FCD34D;
}

.badge-info {
    background: rgba(56,189,248,0.18);
    color: #7DD3FC;
}

.resolution {
    margin-top: 12px;
    background: rgba(255,255,255,0.06);
    padding: 12px;
    border-radius: 10px;
    color: #C7F9CC;
    font-size: 0.9rem;
}

.bridge-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

.bridge-table td {
    padding: 12px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

.bridge-table tr:last-child td {
    border-bottom: none;
}

.bridge-label {
    color: #E2E8F0;
}

.bridge-value {
    text-align: right;
    font-weight: 700;
    color: white;
}

.bridge-highlight td {
    background: rgba(99,102,241,0.14);
}

.bridge-final td {
    background: linear-gradient(135deg, rgba(79,70,229,0.55), rgba(59,130,246,0.45));
    color: white;
    font-weight: 700;
}

.small-note {
    color: #94A3B8;
    font-size: 0.85rem;
    margin-top: 8px;
}

.status-ok {
    color: #86EFAC;
    font-weight: 700;
}

.status-warn {
    color: #FCA5A5;
    font-weight: 700;
}

hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 24px 0;
}

[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    overflow: hidden;
}

@media (max-width: 900px) {
    .card-row {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------------- HELPERS ----------------------
def money(v: float) -> str:
    sign = "-" if v < 0 else ""
    return f"{sign}₹{abs(v):,.2f}"

def render_summary_cards(platform_total, bank_total, diff, txn_count_platform, txn_count_bank):
    warning_cls = "warning" if diff != 0 else ""
    st.markdown(f"""
    <div class="card-row">
        <div class="summary-card">
            <div class="summary-title">Platform Total</div>
            <div class="summary-value">{money(platform_total)}</div>
            <div class="summary-label">{txn_count_platform} transactions recorded</div>
        </div>
        <div class="summary-card">
            <div class="summary-title">Bank Total</div>
            <div class="summary-value">{money(bank_total)}</div>
            <div class="summary-label">{txn_count_bank} transactions settled</div>
        </div>
        <div class="summary-card {warning_cls}">
            <div class="summary-title">Difference (Bank - Platform)</div>
            <div class="summary-value">{money(diff)}</div>
            <div class="summary-label">Mismatch requiring analysis</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def format_view(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "transaction_id",
        "date_A", "amount_A", "type_A", "reference_A",
        "date_B", "amount_B", "type_B", "reference_B",
        "status"
    ]
    available = [c for c in cols if c in df.columns]
    return df[available].rename(columns={
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

def show_table_or_empty(title: str, df: pd.DataFrame, empty_text: str):
    st.markdown(f"#### {title}")
    if df.empty:
        st.success(empty_text)
    else:
        st.dataframe(format_view(df), use_container_width=True)

# ---------------------- HEADER ----------------------
st.title("💰 Payment Reconciliation Dashboard")
st.markdown('<div class="subtle">Upload Platform and Bank CSVs to analyze mismatches, explain root causes, and build a reconciliation bridge.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    file_a = st.file_uploader("📂 Upload Platform CSV", type=["csv"])
with col2:
    file_b = st.file_uploader("🏦 Upload Bank CSV", type=["csv"])

if file_a and file_b:
    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)

    # Basic cleanup
    df_a["amount"] = pd.to_numeric(df_a["amount"], errors="coerce")
    df_b["amount"] = pd.to_numeric(df_b["amount"], errors="coerce")
    df_a["date"] = pd.to_datetime(df_a["date"], errors="coerce")
    df_b["date"] = pd.to_datetime(df_b["date"], errors="coerce")
    df_a["type"] = df_a["type"].astype(str).str.lower()
    df_b["type"] = df_b["type"].astype(str).str.lower()

    total_a = round(df_a["amount"].sum(), 2)
    total_b = round(df_b["amount"].sum(), 2)
    diff = round(total_b - total_a, 2)

    render_summary_cards(total_a, total_b, diff, len(df_a), len(df_b))

    if diff != 0:
        st.error("🚨 Mismatch detected — gap analysis below explains the drivers.")
    else:
        st.success("✅ Perfect match — no discrepancies found.")

    # ---------------------- MERGE ----------------------
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

    # Gap datasets
    missing_bank = merged[merged["status"] == "Missing in Bank"].copy()
    missing_platform = merged[merged["status"] == "Missing in Platform"].copy()

    dup_bank_rows = df_b[df_b.duplicated("transaction_id", keep=False)].copy()
    duplicate_counts = dup_bank_rows.groupby("transaction_id").size().reset_index(name="count")
    duplicates = merged.merge(duplicate_counts, on="transaction_id", how="inner").copy()
    duplicates["status"] = "Duplicate"
    duplicates = duplicates.drop_duplicates(subset=["transaction_id"])

    rounding = merged[
        (merged["amount_A"].notna()) &
        (merged["amount_B"].notna()) &
        (abs(merged["amount_A"] - merged["amount_B"]) < 1) &
        (merged["amount_A"] != merged["amount_B"])
    ].copy()
    rounding["status"] = "Rounding Difference"

    timing = merged[
        (merged["date_A"].notna()) &
        (merged["date_B"].notna()) &
        (
            (merged["date_A"].dt.month != merged["date_B"].dt.month) |
            (merged["date_A"].dt.year != merged["date_B"].dt.year)
        )
    ].copy()
    timing["status"] = "Timing Difference"

    payment_refs = set(df_a[df_a["type"] == "payment"]["reference"].dropna())
    refunds = df_a[
        (df_a["type"] == "refund") &
        (~df_a["reference"].isin(payment_refs))
    ].copy()

    # ---------------------- IMPACTS ----------------------
    duplicate_impact = 0.0
    if not dup_bank_rows.empty:
        dup_calc = dup_bank_rows.groupby("transaction_id")["amount"].agg(["count", "first"]).reset_index()
        dup_calc["extra_count"] = dup_calc["count"] - 1
        dup_calc["impact"] = dup_calc["extra_count"] * dup_calc["first"]
        duplicate_impact = round(dup_calc["impact"].sum(), 2)

    rounding_impact = round((rounding["amount_B"] - rounding["amount_A"]).sum(), 2) if not rounding.empty else 0.0
    missing_bank_impact = round(-missing_bank["amount_A"].fillna(0).sum(), 2) if not missing_bank.empty else 0.0
    missing_platform_impact = round(missing_platform["amount_B"].fillna(0).sum(), 2) if not missing_platform.empty else 0.0
    orphan_refund_impact = round(-refunds["amount"].sum(), 2) if not refunds.empty else 0.0

    explained_difference = round(
        duplicate_impact +
        rounding_impact +
        missing_bank_impact +
        missing_platform_impact +
        orphan_refund_impact,
        2
    )

    # ---------------------- GAP ANALYSIS ----------------------
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 🔍 Gap Analysis")

    if not timing.empty:
        row = timing.iloc[0]
        st.markdown(f"""
        <div class="gap-card critical">
            <div class="gap-head">
                <div class="gap-title">
                    Gap #1: Settlement Timing Difference
                    <span class="badge badge-critical">CRITICAL</span>
                </div>
                <div class="gap-amount">{money(missing_bank_impact if missing_bank_impact != 0 else 0)}</div>
            </div>
            <div>
                <b>Transaction:</b> {row.get("transaction_id", "")}<br>
                <b>Platform Date:</b> {row.get("date_A").date() if pd.notna(row.get("date_A")) else "-"}<br>
                <b>Bank Settlement:</b> {row.get("date_B").date() if pd.notna(row.get("date_B")) else "-"}<br>
                <b>Impact:</b> Platform recorded the transaction in one period, but bank settled it in another period.
            </div>
            <div class="resolution">Resolution: Carry forward this item or post an accrual adjustment until settlement appears in the correct bank period.</div>
        </div>
        """, unsafe_allow_html=True)

    if duplicate_impact != 0:
        row = duplicates.iloc[0]
        count_value = int(row.get("count", 2)) if "count" in row else 2
        st.markdown(f"""
        <div class="gap-card critical">
            <div class="gap-head">
                <div class="gap-title">
                    Gap #2: Duplicate Entry
                    <span class="badge badge-critical">CRITICAL</span>
                </div>
                <div class="gap-amount">{money(duplicate_impact)}</div>
            </div>
            <div>
                <b>Transaction:</b> {row.get("transaction_id", "")}<br>
                <b>Platform Count:</b> 1 entry<br>
                <b>Bank Count:</b> {count_value} entries<br>
                <b>Amount per entry:</b> {money(float(row.get("amount_B", 0) if pd.notna(row.get("amount_B")) else 0))}<br>
                <b>Impact:</b> Bank total is inflated due to one or more duplicate settlements.
            </div>
            <div class="resolution">Resolution: Validate bank statement lineage and remove duplicate settlement from the reconciled balance.</div>
        </div>
        """, unsafe_allow_html=True)

    if rounding_impact != 0:
        st.markdown(f"""
        <div class="gap-card warning">
            <div class="gap-head">
                <div class="gap-title">
                    Gap #3: Rounding Difference
                    <span class="badge badge-warning">WARNING</span>
                </div>
                <div class="gap-amount">{money(rounding_impact)}</div>
            </div>
            <div>
                <b>Transactions:</b> {", ".join(rounding["transaction_id"].astype(str).tolist())}<br>
                <b>Impact:</b> Small row-level amount differences accumulate when totals are summed.
            </div>
            <div class="resolution">Resolution: Apply a rounding tolerance policy or standardize rounding before reconciliation.</div>
        </div>
        """, unsafe_allow_html=True)

    if not refunds.empty:
        row = refunds.iloc[0]
        st.markdown(f"""
        <div class="gap-card info">
            <div class="gap-head">
                <div class="gap-title">
                    Gap #4: Orphan Refund
                    <span class="badge badge-info">INVESTIGATE</span>
                </div>
                <div class="gap-amount">{money(orphan_refund_impact)}</div>
            </div>
            <div>
                <b>Transaction:</b> {row.get("transaction_id", "")}<br>
                <b>Date:</b> {row.get("date").date() if pd.notna(row.get("date")) else "-"}<br>
                <b>Amount:</b> {money(float(row.get("amount", 0) if pd.notna(row.get("amount")) else 0))}<br>
                <b>Issue:</b> Refund exists but the original payment is not present in the available platform payment records.
            </div>
            <div class="resolution">Resolution: Check prior-period data or refund processing logs to confirm whether this is valid or an upstream data issue.</div>
        </div>
        """, unsafe_allow_html=True)

    if timing.empty and duplicate_impact == 0 and rounding_impact == 0 and refunds.empty and missing_platform.empty and missing_bank.empty:
        st.success("✅ No discrepancy gaps identified.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------- RECONCILIATION BRIDGE ----------------------
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 📊 Reconciliation Bridge")

    adjusted_total = round(
        total_a
        + duplicate_impact
        + rounding_impact
        + missing_bank_impact
        + missing_platform_impact
        + orphan_refund_impact,
        2
    )
    remaining_unexplained = round(total_b - adjusted_total, 2)

    bridge_html = f"""
    <table class="bridge-table">
        <tr>
            <td class="bridge-label"><b>Platform Total</b></td>
            <td class="bridge-value">{money(total_a)}</td>
        </tr>
        <tr>
            <td class="bridge-label">Add: Duplicate Impact</td>
            <td class="bridge-value">{money(duplicate_impact)}</td>
        </tr>
        <tr>
            <td class="bridge-label">Add: Rounding Impact</td>
            <td class="bridge-value">{money(rounding_impact)}</td>
        </tr>
        <tr>
            <td class="bridge-label">Add / (Less): Missing in Platform</td>
            <td class="bridge-value">{money(missing_platform_impact)}</td>
        </tr>
        <tr>
            <td class="bridge-label">Add / (Less): Missing in Bank</td>
            <td class="bridge-value">{money(missing_bank_impact)}</td>
        </tr>
        <tr>
            <td class="bridge-label">Add / (Less): Orphan Refund Impact</td>
            <td class="bridge-value">{money(orphan_refund_impact)}</td>
        </tr>
        <tr class="bridge-highlight">
            <td class="bridge-label"><b>Adjusted Platform Total</b></td>
            <td class="bridge-value">{money(adjusted_total)}</td>
        </tr>
        <tr class="bridge-final">
            <td class="bridge-label">Bank Total</td>
            <td class="bridge-value">{money(total_b)}</td>
        </tr>
        <tr>
            <td class="bridge-label"><b>Remaining Unexplained</b></td>
            <td class="bridge-value">{money(remaining_unexplained)}</td>
        </tr>
    </table>
    """
    st.markdown(bridge_html, unsafe_allow_html=True)

    if remaining_unexplained == 0:
        st.markdown('<div class="small-note status-ok">✓ All discrepancy drivers are fully explained by the bridge.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="small-note status-warn">⚠ Some variance remains unexplained. This may indicate overlapping cases or additional business rules are needed.</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="small-note">
        Formula used: <br>
        <code>
        Adjusted Platform = Platform Total + Duplicate + Rounding + Missing in Platform + Missing in Bank + Orphan Refund
        </code>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------- DETAILED TABLES ----------------------
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 📋 Detailed Drill-Down")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Missing (Bank)",
        "Missing (Platform)",
        "Duplicates",
        "Rounding",
        "Timing",
        "Orphan Refunds"
    ])

    with tab1:
        show_table_or_empty("Transactions present in Platform but missing in Bank", missing_bank, "✅ No transactions missing in Bank")

    with tab2:
        show_table_or_empty("Transactions present in Bank but missing in Platform", missing_platform, "✅ No transactions missing in Platform")

    with tab3:
        show_table_or_empty("Duplicate transactions found in Bank", duplicates, "✅ No duplicate transactions found")

    with tab4:
        show_table_or_empty("Transactions with rounding differences", rounding, "✅ No rounding differences found")

    with tab5:
        show_table_or_empty("Transactions settled in a different period", timing, "✅ No timing differences found")

    with tab6:
        st.markdown("#### Refunds without matching original payment")
        if refunds.empty:
            st.success("✅ No orphan refunds found")
        else:
            st.dataframe(refunds, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------- FOOTER ----------------------
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## ✅ Reconciliation Status")
    if remaining_unexplained == 0:
        st.success("Reconciliation complete — all material gaps identified and explained.")
    else:
        st.warning("Reconciliation partially complete — main gaps identified, but some variance remains unexplained.")
    st.caption(
        f"Generated from uploaded files | Platform Rows: {len(df_a)} | Bank Rows: {len(df_b)} | Explained Difference: {money(explained_difference)}"
    )
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("👆 Upload both CSV files to generate the dashboard.")
