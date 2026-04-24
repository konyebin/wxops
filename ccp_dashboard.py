#!/usr/bin/env python3
"""
Cisco Calling Plan Usage Dashboard
Run with: streamlit run ccp_dashboard.py
"""

import glob
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cisco Calling Plan Dashboard",
    page_icon="📞",
    layout="wide",
)

st.title("📞 Cisco Calling Plan Usage Dashboard")

# ── File loader ───────────────────────────────────────────────────────────────
st.sidebar.header("Data Source")

# Auto-detect CDR CSVs on the system
default_search = str(Path.home() / "detailed_call_history_*" / "*.csv")
found_files = sorted(glob.glob(default_search))

if found_files:
    st.sidebar.success(f"Found {len(found_files)} CDR file(s)")
    selected_files = st.sidebar.multiselect(
        "Select CDR file(s) to load",
        options=found_files,
        default=found_files,
        format_func=lambda x: Path(x).name,
    )
else:
    selected_files = []
    st.sidebar.warning("No CDR files auto-detected.")

# Manual upload fallback
uploaded = st.sidebar.file_uploader(
    "Or upload CSV file(s)", type="csv", accept_multiple_files=True
)

# Auto-refresh toggle
auto_refresh = st.sidebar.toggle("Auto-refresh (30s)", value=False)
if auto_refresh:
    import time
    st.sidebar.caption(f"Last refresh: {pd.Timestamp.now().strftime('%H:%M:%S')}")
    time.sleep(30)
    st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_data(file_paths: tuple, uploaded_names: tuple) -> pd.DataFrame:
    dfs = []
    for path in file_paths:
        try:
            dfs.append(pd.read_csv(path, low_memory=False))
        except Exception as e:
            st.warning(f"Could not read {Path(path).name}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


@st.cache_data(ttl=30)
def load_uploaded(files) -> pd.DataFrame:
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f, low_memory=False))
        except Exception as e:
            st.warning(f"Could not read {f.name}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


raw_df = pd.DataFrame()
if selected_files:
    raw_df = load_data(tuple(selected_files), ())
if uploaded:
    up_df = load_uploaded(tuple(uploaded))
    raw_df = pd.concat([raw_df, up_df], ignore_index=True) if not raw_df.empty else up_df

if raw_df.empty:
    st.info("👈 Select or upload a CDR CSV file to get started.")
    st.stop()

# ── Filter: Cisco Calling Plan only ──────────────────────────────────────────
ccp_df = raw_df[
    raw_df["PSTN vendor name"].astype(str).str.contains("Cisco Calling Plans", case=False, na=False)
].copy()

if ccp_df.empty:
    st.warning("No Cisco Calling Plan records found in the selected file(s).")
    st.stop()

# ── Data prep ─────────────────────────────────────────────────────────────────
ccp_df["Duration"] = pd.to_numeric(ccp_df["Duration"], errors="coerce").fillna(0)
ccp_df["Duration_min"] = ccp_df["Duration"] / 60
ccp_df["Start time"] = pd.to_datetime(ccp_df["Start time"], errors="coerce", utc=True)
ccp_df["Date"] = ccp_df["Start time"].dt.date
ccp_df["User"] = ccp_df["User"].fillna("Unknown").astype(str)

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("Filters")

direction_options = sorted(ccp_df["Direction"].dropna().unique().tolist())
selected_directions = st.sidebar.multiselect(
    "Call Direction", direction_options, default=direction_options
)

date_min = ccp_df["Date"].min()
date_max = ccp_df["Date"].max()
date_range = st.sidebar.date_input("Date Range", value=(date_min, date_max))

top_n = st.sidebar.slider("Show top N users", min_value=5, max_value=50, value=20)

# Apply filters
filtered = ccp_df[ccp_df["Direction"].isin(selected_directions)]
if len(date_range) == 2:
    filtered = filtered[
        (filtered["Date"] >= date_range[0]) & (filtered["Date"] <= date_range[1])
    ]

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_calls     = len(filtered)
total_minutes   = filtered["Duration_min"].sum()
total_users     = filtered["User"].nunique()
avg_min_per_call = filtered["Duration_min"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total CCP Calls",        f"{total_calls:,}")
k2.metric("Total Minutes",          f"{total_minutes:,.1f}")
k3.metric("Unique Users",           f"{total_users:,}")
k4.metric("Avg Duration (min)",     f"{avg_min_per_call:.2f}")

st.divider()

# ── Per-user summary ──────────────────────────────────────────────────────────
user_summary = (
    filtered.groupby("User")
    .agg(
        Total_Calls=("Duration_min", "count"),
        Total_Minutes=("Duration_min", "sum"),
        Avg_Duration_min=("Duration_min", "mean"),
    )
    .round(2)
    .sort_values("Total_Minutes", ascending=False)
    .reset_index()
)

top_users = user_summary.head(top_n)

col1, col2 = st.columns(2)

# Individual minutes bar chart
with col1:
    st.subheader(f"⏱ Individual Usage — Top {top_n} Users")
    fig_bar = px.bar(
        top_users,
        x="Total_Minutes",
        y="User",
        orientation="h",
        color="Total_Minutes",
        color_continuous_scale="Blues",
        text=top_users["Total_Minutes"].apply(lambda x: f"{x:.1f}m"),
        labels={"Total_Minutes": "Minutes", "User": ""},
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        height=max(400, top_n * 28),
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
        margin=dict(l=0, r=60, t=20, b=20),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Cumulative minutes chart
with col2:
    st.subheader("📈 Cumulative Minutes — Top Users")
    top_users_cum = top_users.copy()
    top_users_cum["Cumulative_Minutes"] = top_users_cum["Total_Minutes"].cumsum()
    fig_cum = go.Figure()
    fig_cum.add_bar(
        x=top_users_cum["User"],
        y=top_users_cum["Total_Minutes"],
        name="Individual",
        marker_color="#4A90D9",
    )
    fig_cum.add_scatter(
        x=top_users_cum["User"],
        y=top_users_cum["Cumulative_Minutes"],
        mode="lines+markers",
        name="Cumulative",
        line=dict(color="#E85454", width=2),
        yaxis="y2",
    )
    fig_cum.update_layout(
        height=450,
        yaxis=dict(title="Individual Minutes"),
        yaxis2=dict(title="Cumulative Minutes", overlaying="y", side="right"),
        xaxis=dict(tickangle=-35),
        legend=dict(orientation="h", y=1.05),
        margin=dict(l=0, r=60, t=40, b=80),
    )
    st.plotly_chart(fig_cum, use_container_width=True)

st.divider()

# ── Daily usage trend ─────────────────────────────────────────────────────────
st.subheader("📅 Daily CCP Usage Trend")
daily = (
    filtered.groupby("Date")
    .agg(Minutes=("Duration_min", "sum"), Calls=("Duration_min", "count"))
    .reset_index()
)
fig_trend = px.area(
    daily, x="Date", y="Minutes",
    labels={"Minutes": "Total Minutes", "Date": ""},
    color_discrete_sequence=["#4A90D9"],
)
fig_trend.update_layout(height=280, margin=dict(t=10, b=10))
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("📋 User Summary Table")
display_df = user_summary.rename(columns={
    "User": "User",
    "Total_Calls": "Total Calls",
    "Total_Minutes": "Total Minutes",
    "Avg_Duration_min": "Avg Duration (min)",
})
st.dataframe(display_df, use_container_width=True, hide_index=True)

# Download button
csv_out = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Summary CSV",
    data=csv_out,
    file_name="ccp_usage_summary.csv",
    mime="text/csv",
)
