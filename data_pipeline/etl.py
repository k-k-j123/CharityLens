import pandas as pd
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ngos.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "Datasets", "ngosindia.csv")


def load(csv_path: str = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = (
        df.columns.str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace(r"^\s*$", None, regex=True)
    if "name" in df.columns:
        df["name"] = df["name"].str.strip()
    df = df.dropna(subset=["name"])
    before = len(df)
    df = df.drop_duplicates(subset=["name"], keep="first")
    dupes = before - len(df)
    return df, dupes


def store(df: pd.DataFrame, db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql("ngos", conn, if_exists="replace", index=False)
    conn.execute("DROP TABLE IF EXISTS ngos_fts")
    conn.execute(
        "CREATE VIRTUAL TABLE ngos_fts USING fts5("
        "name, purpose, aims_objectives_mission, "
        "content='ngos', content_rowid='rowid')"
    )
    conn.execute(
        "INSERT INTO ngos_fts(rowid, name, purpose, aims_objectives_mission) "
        "SELECT rowid, name, purpose, aims_objectives_mission FROM ngos"
    )
    conn.commit()
    conn.close()


def run_etl(csv_path: str = CSV_PATH, db_path: str = DB_PATH) -> int:
    df = load(csv_path)
    df, dupes = clean(df)
    store(df, db_path)
    print(f"ETL complete: {len(df)} records -> {db_path}")
    if dupes:
        print(f"  {dupes} duplicate names removed")
    return len(df)


if __name__ == "__main__":
    run_etl()
