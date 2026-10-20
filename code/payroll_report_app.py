"""
payroll_report_app.py — the quarter at a glance, for someone who never opens a terminal.

Every Friday since September the office manager at Salt City Coffee has downloaded
a payroll export from the Assignment 04 app; before that she typed the same file
by hand. The owner now wants to know where the hours went this quarter, the
accountant wants pay by month and department, and the manager wants to see who
has been missing shifts. This page answers all three from the pile of exports.

Same shape as Assignment 04: the page *assembles* the pipeline — one call to
`build_history` does the cleaning — and then shows the reports, filtered by the
department and dates the user picks.

Run it:  Run and Debug -> "Streamlit Run: Current File"
Test it: pytest tests/test_pipeline.py -k app
"""
# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignments 03 and 04 — plus two
# new ones, st.date_input and st.bar_chart. README Step 8 has the exact widgets,
# keys and labels; the tests in tests/test_pipeline.py -k app check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster   <- load_employees()                           (fixed; not uploaded)
#   uploads  <- st.file_uploader, key="exports", accept_multiple_files=True
#               (an empty list until files are chosen)
#   if there are uploads:
#       history <- build_history([load_export(u) for u in uploads], roster)
#       st.warning naming any employeeid with no department (not on the roster);
#           the reports below use only the rows that matched
#       st.selectbox, key="department": "All" plus each department
#       st.date_input, key="dates": a (start, end) range, defaulting to the first
#           and last pay_date — compare against pay_date.dt.date to filter
#       the selection as a subheader
#       four st.metric cards in st.columns(4): Weeks, Employees, Total hours,
#           Total gross pay — counts are .nunique(), totals are .sum()
#       st.bar_chart of pay_by_month(selected), with month as the x axis
#       st.dataframe of summarize_employees(selected)
#       st.dataframe of hours_grid(selected), then of missed_weeks(that grid)
#       st.download_button, key="download": pay_by_month(...).to_csv(index=False)
#
# What the page does NOT do: cleaning, grouping, pivoting. If you find yourself
# writing a groupby or a pivot_table here, that logic belongs in the package.

import streamlit as st

from payroll import (
    load_employees,
    load_export,
    build_history,
    summarize_employees,
    hours_grid,
    missed_weeks,
    pay_by_month,
)

st.title("Salt City Coffee — Quarterly Payroll Report")

roster = load_employees()

uploads = st.file_uploader(
    "Upload payroll exports:",
    type=["csv"],
    accept_multiple_files=True,
    key="exports",
)

if uploads:
    exports = [load_export(u) for u in uploads]
    history = build_history(exports, roster)

    unmatched = history[history["department"].isna()]
    if len(unmatched) > 0:
        ids = ", ".join(sorted(unmatched["employeeid"].unique()))
        st.warning(f"Unmatched employee IDs: {ids}")

    matched = history[history["department"].notna()]

    departments = sorted(matched["department"].unique())
    department = st.selectbox("Department", ["All"] + departments, key="department")

    first_date = matched["pay_date"].min().date()
    last_date = matched["pay_date"].max().date()
    dates = st.date_input(
        "Pay dates",
        value=(first_date, last_date),
        min_value=first_date,
        max_value=last_date,
        key="dates",
    )
    start, end = dates if len(dates) == 2 else (dates[0], dates[0])

    filtered = matched[
        (matched["pay_date"].dt.date >= start) & (matched["pay_date"].dt.date <= end)
    ]
    if department != "All":
        filtered = filtered[filtered["department"] == department]

    weeks = filtered["week_ending"].nunique()
    employees = filtered["employee_id"].nunique()
    total_hours = filtered["hours_worked"].sum()
    total_gross_pay = filtered["gross_pay"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Weeks", weeks)
    col2.metric("Employees", employees)
    col3.metric("Total hours", f"{total_hours:,.2f}")
    col4.metric("Total gross pay", f"${total_gross_pay:,.2f}")

    monthly = pay_by_month(filtered)
    st.bar_chart(monthly, x="month")

    st.dataframe(summarize_employees(filtered))

    grid = hours_grid(filtered)
    st.dataframe(grid)

    st.dataframe(missed_weeks(grid))

    st.download_button(
        "Download pay by month CSV",
        data=monthly.to_csv(index=False),
        file_name="pay_by_month.csv",
        mime="text/csv",
        key="download",
    )
