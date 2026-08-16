from pathlib import Path
import pandas as pd
from idxanalysis.config.DbConfig import dbConfig


class __SqlRepository:
    def executeSQL(self, sqlPath: Path):
        with dbConfig.create_db_connection() as connection:
            with open(sqlPath, "r") as fw:
                content = fw.read()
                for sqlQuery in content.split(";"):
                    if len(sqlQuery) == 0:
                        continue
                    dbConfig.query(connection=connection, sql=sqlQuery.strip())
            connection.commit()
            connection.close()

    def pandasRead(self, sqlQuery: str) -> pd.DataFrame:
        df = pd.DataFrame()
        with dbConfig.create_db_connection() as connection:
            df = pd.read_sql(sqlQuery, connection)
            connection.commit()
            connection.close()
        return df


sqlRepository = __SqlRepository()
