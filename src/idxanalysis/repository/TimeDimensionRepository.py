from datetime import datetime
from idxanalysis.config.DbConfig import dbConfig
from idxanalysis.config.AppConfig import appConfig


class __TimeDimensionRepository:
    def getTimeDimensions(self) -> list[datetime]:
        timestamps = set[datetime]()
        with dbConfig.create_db_connection() as connection:
            result = dbConfig.query(
                connection=connection, sql=appConfig.SQL_GET_TIME_DIMENSIONS)
            for row in result:
                tm = row[0]
                if isinstance(tm, datetime):
                    timestamps.add(tm)
            connection.commit()
            connection.close()
        return list(timestamps)

    def insertTimeDimension(self, timestamp: datetime):
        with dbConfig.create_db_connection() as connection:
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_INSERT_TIME_DIMENSIONS, parameters={"tm": timestamp})
            connection.commit()
            connection.close()


timeDimensionRepository = __TimeDimensionRepository()
