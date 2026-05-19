import os
import subprocess
import sys
from pathlib import Path

import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DB_PATH = os.environ.get("DUCKDB_PATH", "datavault.duckdb")
REPO_ROOT = Path(__file__).parent.parent


def _build_db():
    """Run load_raw + dbt build if DuckDB file is absent (e.g. fresh Streamlit Cloud deploy)."""
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "load_raw.py")],
        cwd=REPO_ROOT, check=True,
    )
    subprocess.run(
        ["dbt", "deps", "--project-dir", "datavault_dbt", "--profiles-dir", "."],
        cwd=REPO_ROOT, check=True,
    )
    subprocess.run(
        ["dbt", "build", "--project-dir", "datavault_dbt", "--profiles-dir", "."],
        cwd=REPO_ROOT, check=True,
    )


if not Path(DB_PATH).exists():
    with st.spinner("First run — building data pipeline (≈ 30 s)…"):
        _build_db()
DAY_LABELS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}


@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data
def load_daily_ridership():
    return get_connection().execute(
        "SELECT * FROM main_marts.mart_daily_ridership ORDER BY trip_date, corridor_id"
    ).df()


@st.cache_data
def load_corridor_stats():
    return get_connection().execute(
        "SELECT * FROM main_marts.mart_corridor_stats ORDER BY total_trips DESC"
    ).df()


@st.cache_data
def load_stop_performance():
    return get_connection().execute(
        "SELECT * FROM main_marts.mart_stop_performance ORDER BY performance_score DESC"
    ).df()


@st.cache_data
def load_surge():
    return get_connection().execute(
        "SELECT * FROM main_marts.mart_surge_analysis"
    ).df()


def fmt_idr(v):
    if v is None:
        return "—"
    b = v / 1_000_000_000
    if b >= 1:
        return f"Rp {b:.2f}B"
    m = v / 1_000_000
    return f"Rp {m:.1f}M"


st.set_page_config(
    page_title="TransJakarta Analytics",
    page_icon="🚌",
    layout="wide",
)

st.title("TransJakarta BRT — April 2023")
st.caption("dbt + DuckDB analytics pipeline · datavault portfolio project")

daily = load_daily_ridership()
corridors = load_corridor_stats()
stops = load_stop_performance()
surge = load_surge()

# ── KPI row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Trips", f"{daily['total_trips'].sum():,}")
k2.metric("Total Revenue", fmt_idr(daily["total_revenue"].sum()))
k3.metric("Active Corridors", f"{len(corridors):,}")
k4.metric("Unique Riders", f"{daily['unique_riders'].sum():,}")

st.divider()

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["Daily Ridership", "Corridors", "Stop Performance", "Surge Analysis"]
)

# ── Tab 1: Daily Ridership ────────────────────────────────────────────────────
with tab1:
    st.subheader("Daily Trips — All Corridors")

    daily_agg = (
        daily.groupby("trip_date", as_index=False)
        .agg(total_trips=("total_trips", "sum"), total_revenue=("total_revenue", "sum"))
    )

    fig = px.area(
        daily_agg,
        x="trip_date",
        y="total_trips",
        labels={"trip_date": "Date", "total_trips": "Trips"},
        color_discrete_sequence=["#0099FF"],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=300)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Top 10 Corridors by Trips")
        top10 = corridors.head(10)
        fig2 = px.bar(
            top10,
            x="total_trips",
            y="corridor_id",
            orientation="h",
            labels={"total_trips": "Trips", "corridor_id": "Corridor"},
            color="total_trips",
            color_continuous_scale="Blues",
        )
        fig2.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=20, b=0),
            height=350,
            yaxis={"autorange": "reversed"},
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("Completion Rate Distribution")
        fig3 = px.histogram(
            corridors,
            x="completion_rate_pct",
            nbins=20,
            labels={"completion_rate_pct": "Completion Rate (%)"},
            color_discrete_sequence=["#0099FF"],
        )
        fig3.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=350)
        st.plotly_chart(fig3, use_container_width=True)

# ── Tab 2: Corridors ──────────────────────────────────────────────────────────
with tab2:
    st.subheader("Corridor Statistics")

    col_c, col_d = st.columns(2)
    with col_c:
        fig4 = px.scatter(
            corridors,
            x="avg_distance_km",
            y="avg_duration_min",
            size="total_trips",
            color="completion_rate_pct",
            hover_data=["corridor_id", "corridor_name"],
            labels={
                "avg_distance_km": "Avg Distance (km)",
                "avg_duration_min": "Avg Duration (min)",
                "completion_rate_pct": "Completion %",
            },
            color_continuous_scale="Blues",
            title="Distance vs Duration (bubble = trip volume)",
        )
        fig4.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=400)
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        fig5 = px.bar(
            corridors.head(15),
            x="corridor_id",
            y="total_revenue",
            labels={"corridor_id": "Corridor", "total_revenue": "Revenue (IDR)"},
            color="total_revenue",
            color_continuous_scale="Blues",
            title="Top 15 Corridors by Revenue",
        )
        fig5.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=40, b=0),
            height=400,
        )
        st.plotly_chart(fig5, use_container_width=True)

    st.dataframe(
        corridors[
            [
                "corridor_id", "corridor_name", "total_trips", "complete_trips",
                "completion_rate_pct", "unique_riders", "avg_distance_km", "avg_duration_min",
            ]
        ].rename(columns={
            "corridor_id": "ID",
            "corridor_name": "Name",
            "total_trips": "Trips",
            "complete_trips": "Complete",
            "completion_rate_pct": "Completion %",
            "unique_riders": "Unique Riders",
            "avg_distance_km": "Avg Dist (km)",
            "avg_duration_min": "Avg Dur (min)",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ── Tab 3: Stop Performance ───────────────────────────────────────────────────
with tab3:
    st.subheader("Stop Performance Map")

    top_n = st.slider("Show top N stops by score", 50, len(stops), 200, step=50)
    plot_stops = stops.head(top_n)

    fig6 = px.scatter_mapbox(
        plot_stops,
        lat="lat",
        lon="lon",
        size="total_boardings",
        color="performance_score",
        hover_name="stop_name",
        hover_data={"lat": False, "lon": False, "total_boardings": True, "performance_score": True},
        color_continuous_scale="Blues",
        zoom=10,
        center={"lat": -6.21, "lon": 106.85},
        height=500,
        mapbox_style="carto-positron",
    )
    fig6.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig6, use_container_width=True)

    col_e, col_f = st.columns(2)
    with col_e:
        st.subheader("Top 20 Stops by Score")
        st.dataframe(
            stops.head(20)[["stop_id", "stop_name", "total_boardings", "performance_score"]].rename(
                columns={
                    "stop_id": "ID",
                    "stop_name": "Name",
                    "total_boardings": "Boardings",
                    "performance_score": "Score",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with col_f:
        fig7 = px.histogram(
            stops,
            x="performance_score",
            nbins=25,
            labels={"performance_score": "Performance Score"},
            color_discrete_sequence=["#0099FF"],
            title="Score Distribution",
        )
        fig7.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=350)
        st.plotly_chart(fig7, use_container_width=True)

# ── Tab 4: Surge Analysis ─────────────────────────────────────────────────────
with tab4:
    st.subheader("Demand Surge Heatmap")

    all_corridors = ["All"] + sorted(surge["corridor_id"].unique().tolist())
    selected = st.selectbox("Corridor", all_corridors)

    if selected == "All":
        surge_data = (
            surge.groupby(["day_of_week", "hour_of_day"], as_index=False)
            .agg(trip_count=("trip_count", "sum"))
        )
        surge_data["demand_index"] = (
            surge_data["trip_count"] / surge_data["trip_count"].mean()
        )
    else:
        surge_data = surge[surge["corridor_id"] == selected].copy()

    surge_data["day_label"] = surge_data["day_of_week"].map(DAY_LABELS)
    pivot = surge_data.pivot_table(
        index="day_label", columns="hour_of_day", values="demand_index", aggfunc="mean"
    )
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    fig8 = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[f"{h:02d}:00" for h in pivot.columns],
            y=pivot.index.tolist(),
            colorscale="Blues",
            colorbar=dict(title="Demand Index"),
            hovertemplate="Day: %{y}<br>Hour: %{x}<br>Index: %{z:.2f}<extra></extra>",
        )
    )
    fig8.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        margin=dict(l=0, r=0, t=20, b=0),
        height=350,
    )
    st.plotly_chart(fig8, use_container_width=True)

    col_g, col_h = st.columns(2)
    with col_g:
        peak = surge_data.nlargest(10, "demand_index")[
            ["day_label", "hour_of_day", "trip_count", "demand_index"]
        ].rename(columns={
            "day_label": "Day",
            "hour_of_day": "Hour",
            "trip_count": "Trips",
            "demand_index": "Demand Index",
        })
        st.subheader("Top 10 Peak Slots")
        st.dataframe(peak, use_container_width=True, hide_index=True)

    with col_h:
        hourly_agg = (
            surge_data.groupby("hour_of_day", as_index=False)
            .agg(trip_count=("trip_count", "sum"))
        )
        fig9 = px.bar(
            hourly_agg,
            x="hour_of_day",
            y="trip_count",
            labels={"hour_of_day": "Hour", "trip_count": "Total Trips"},
            color="trip_count",
            color_continuous_scale="Blues",
            title="Trips by Hour",
        )
        fig9.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=40, b=0),
            height=300,
        )
        st.plotly_chart(fig9, use_container_width=True)
