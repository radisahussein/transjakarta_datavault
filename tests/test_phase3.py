import time

import duckdb
import pytest

DB = "datavault.duckdb"


@pytest.fixture(scope="module")
def con():
    return duckdb.connect(DB, read_only=True)


# --- int_trips_enriched ---

def test_int_trips_enriched_row_count(con):
    n = con.execute("SELECT COUNT(*) FROM main_intermediate.int_trips_enriched").fetchone()[0]
    assert n == 182520, f"Expected 182520, got {n}"


def test_int_trips_enriched_unique_transaction_id(con):
    total = con.execute("SELECT COUNT(*) FROM main_intermediate.int_trips_enriched").fetchone()[0]
    unique = con.execute("SELECT COUNT(DISTINCT transaction_id) FROM main_intermediate.int_trips_enriched").fetchone()[0]
    assert total == unique


def test_int_trips_enriched_hour_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_intermediate.int_trips_enriched WHERE hour_of_day NOT BETWEEN 0 AND 23"
    ).fetchone()[0]
    assert bad == 0


def test_int_trips_enriched_day_of_week_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_intermediate.int_trips_enriched WHERE day_of_week NOT BETWEEN 1 AND 7"
    ).fetchone()[0]
    assert bad == 0


def test_int_trips_enriched_distance_positive(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_intermediate.int_trips_enriched WHERE distance_km IS NOT NULL AND distance_km < 0"
    ).fetchone()[0]
    assert bad == 0


def test_int_trips_enriched_duration_positive(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_intermediate.int_trips_enriched WHERE duration_min IS NOT NULL AND duration_min < 0"
    ).fetchone()[0]
    assert bad == 0


def test_int_trips_enriched_complete_trips_subset(con):
    complete = con.execute(
        "SELECT COUNT(*) FROM main_intermediate.int_trips_enriched WHERE is_complete_trip"
    ).fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM main_intermediate.int_trips_enriched").fetchone()[0]
    assert 0 < complete < total


# --- mart_daily_ridership ---

def test_mart_daily_ridership_row_count(con):
    n = con.execute("SELECT COUNT(*) FROM main_marts.mart_daily_ridership").fetchone()[0]
    assert n > 1000, f"Expected >1000 rows, got {n}"


def test_mart_daily_ridership_totals_match(con):
    mart_total = con.execute("SELECT SUM(total_trips) FROM main_marts.mart_daily_ridership").fetchone()[0]
    source_total = con.execute("SELECT COUNT(*) FROM main_intermediate.int_trips_enriched").fetchone()[0]
    assert mart_total == source_total, f"Totals diverge: mart={mart_total}, source={source_total}"


def test_mart_daily_ridership_no_negative_trips(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_marts.mart_daily_ridership WHERE total_trips <= 0"
    ).fetchone()[0]
    assert bad == 0


# --- mart_corridor_stats ---

def test_mart_corridor_stats_row_count(con):
    n = con.execute("SELECT COUNT(*) FROM main_marts.mart_corridor_stats").fetchone()[0]
    assert n == 221, f"Expected 221 corridors, got {n}"


def test_mart_corridor_stats_unique_corridor_id(con):
    total = con.execute("SELECT COUNT(*) FROM main_marts.mart_corridor_stats").fetchone()[0]
    unique = con.execute("SELECT COUNT(DISTINCT corridor_id) FROM main_marts.mart_corridor_stats").fetchone()[0]
    assert total == unique


def test_mart_corridor_stats_completion_rate_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_marts.mart_corridor_stats WHERE completion_rate_pct NOT BETWEEN 0 AND 100"
    ).fetchone()[0]
    assert bad == 0


# --- mart_stop_performance ---

def test_mart_stop_performance_row_count(con):
    n = con.execute("SELECT COUNT(*) FROM main_marts.mart_stop_performance").fetchone()[0]
    assert n > 1000, f"Expected >1000 stop rows, got {n}"


def test_mart_stop_performance_unique_stop_id(con):
    total = con.execute("SELECT COUNT(*) FROM main_marts.mart_stop_performance").fetchone()[0]
    unique = con.execute("SELECT COUNT(DISTINCT stop_id) FROM main_marts.mart_stop_performance").fetchone()[0]
    assert total == unique


def test_mart_stop_performance_score_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_marts.mart_stop_performance WHERE performance_score < 0 OR performance_score > 100"
    ).fetchone()[0]
    assert bad == 0


# --- mart_surge_analysis ---

def test_mart_surge_analysis_demand_index_positive(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_marts.mart_surge_analysis WHERE demand_index <= 0"
    ).fetchone()[0]
    assert bad == 0


def test_mart_surge_analysis_hour_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_marts.mart_surge_analysis WHERE hour_of_day NOT BETWEEN 0 AND 23"
    ).fetchone()[0]
    assert bad == 0


# --- performance ---

def test_mart_daily_ridership_query_performance(con):
    start = time.time()
    con.execute("SELECT * FROM main_marts.mart_daily_ridership LIMIT 1000").fetchall()
    assert time.time() - start < 1.0


def test_mart_corridor_stats_query_performance(con):
    start = time.time()
    con.execute("SELECT * FROM main_marts.mart_corridor_stats").fetchall()
    assert time.time() - start < 1.0


def test_mart_stop_performance_query_performance(con):
    start = time.time()
    con.execute("SELECT * FROM main_marts.mart_stop_performance").fetchall()
    assert time.time() - start < 1.0
