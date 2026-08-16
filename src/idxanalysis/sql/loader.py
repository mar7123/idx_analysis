from pathlib import Path


def load_sql_path(dir: str, filename: str) -> Path:
    return Path(__file__).parent.joinpath(dir).joinpath(filename)
