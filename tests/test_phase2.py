import duckdb
import pytest

DB = "datavault.duckdb"


@pytest.fixture(scope="module")
def con():
    return duckdb.connect(DB, read_only=True)


def test_stg_transactions_row_count(con):
    n = con.execute("SELECT COUNT(*) FROM main_staging.stg_transactions").fetchone()[0]
    # 189,500 raw - ~6,980 null corridorID rows
    assert n > 180_000, f"Expected >180k rows, got {n}"


def test_stg_transactions_no_null_transaction_id(con):
    n = con.execute(
        "SELECT COUNT(*) FROM main_staging.stg_transactions WHERE transaction_id IS NULL"
    ).fetchone()[0]
    assert n == 0


def test_stg_transactions_unique_transaction_id(con):
    total = con.execute("SELECT COUNT(*) FROM main_staging.stg_transactions").fetchone()[0]
    unique = con.execute(
        "SELECT COUNT(DISTINCT transaction_id) FROM main_staging.stg_transactions"
    ).fetchone()[0]
    assert total == unique, f"Duplicate transaction_ids: {total - unique}"


def test_stg_transactions_valid_sex_values(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_staging.stg_transactions WHERE card_sex NOT IN ('F', 'M')"
    ).fetchone()[0]
    assert bad == 0


def test_stg_transactions_valid_direction(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_staging.stg_transactions WHERE direction NOT IN (0, 1)"
    ).fetchone()[0]
    assert bad == 0


def test_stg_transactions_age_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_staging.stg_transactions WHERE age_years NOT BETWEEN 3 AND 103"
    ).fetchone()[0]
    assert bad == 0


def test_stg_transactions_no_corridor_nulls(con):
    n = con.execute(
        "SELECT COUNT(*) FROM main_staging.stg_transactions WHERE corridor_id IS NULL"
    ).fetchone()[0]
    assert n == 0


def test_stg_transactions_pay_amount_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_staging.stg_transactions WHERE pay_amount IS NOT NULL AND pay_amount NOT BETWEEN 0 AND 20000"
    ).fetchone()[0]
    assert bad == 0


def test_stg_stops_row_count(con):
    n = con.execute("SELECT COUNT(*) FROM main_staging.stg_stops").fetchone()[0]
    assert n == 5250, f"Expected 5250 stops, got {n}"


def test_stg_stops_unique(con):
    total = con.execute("SELECT COUNT(*) FROM main_staging.stg_stops").fetchone()[0]
    unique = con.execute("SELECT COUNT(DISTINCT stop_id) FROM main_staging.stg_stops").fetchone()[0]
    assert total == unique


def test_stg_stops_jakarta_bounds(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM main_staging.stg_stops WHERE lat NOT BETWEEN -8.0 AND -5.0 OR lon NOT BETWEEN 106.0 AND 107.5"
    ).fetchone()[0]
    assert bad == 0


def test_stg_corridors_row_count(con):
    n = con.execute("SELECT COUNT(*) FROM main_staging.stg_corridors").fetchone()[0]
    assert n == 221, f"Expected 221 corridors, got {n}"


def test_stg_corridors_unique(con):
    total = con.execute("SELECT COUNT(*) FROM main_staging.stg_corridors").fetchone()[0]
    unique = con.execute(
        "SELECT COUNT(DISTINCT corridor_id) FROM main_staging.stg_corridors"
    ).fetchone()[0]
    assert total == unique
