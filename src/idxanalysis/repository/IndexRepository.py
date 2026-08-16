from typing import Mapping

from idxanalysis.config.DbConfig import dbConfig
from idxanalysis.config.AppConfig import appConfig
from idxanalysis.data_model.scrape_model import IndexSummaryResponse


class __IndexRepository:
    def getIndexProfiles(self) -> list[str]:
        index_profiles = set[str]()
        with dbConfig.create_db_connection() as connection:
            result = dbConfig.query(
                connection=connection, sql=appConfig.SQL_GET_INDEX_PROFILES)
            for row in result:
                index_code = row[0]
                if isinstance(index_code, str):
                    index_profiles.add(index_code)
            connection.commit()
            connection.close()
        return list(index_profiles)

    def insertIndexData(self, index_summary: IndexSummaryResponse):
        index_profiles: list[Mapping[str, object]] = []
        index_data: list[Mapping[str, object]] = []
        for i in index_summary.data:
            index_profiles.append({"index_code": i.IndexCode})
            index_data.append(
                {
                    "index_profile": i.IndexCode,
                    "timestamp": i.Date,
                    "previous": i.Previous,
                    "highest": i.Highest,
                    "lowest": i.Lowest,
                    "close": i.Close,
                    "number_of_stock": i.NumberOfStock,
                    "change": i.Change,
                    "volume": i.Volume,
                    "value": i.Value,
                    "frequency": i.Frequency,
                    "market_capital": i.MarketCapital,
                }
            )

        with dbConfig.create_db_connection() as connection:
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_INSERT_INDEX_PROFILES, parameters=index_profiles)
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_INSERT_INDEX_DATA, parameters=index_data)
            connection.commit()
            connection.close()

    def insertIndexStock(self, index_stock_map: dict[str, set[str]]):
        index_stock_insert: list[Mapping[str, object]] = []
        for index_code, stock_codes in index_stock_map.items():
            for stock_code in stock_codes:
                index_stock_insert.append({
                    "index_code": index_code,
                    "stock_code": stock_code,
                })

        with dbConfig.create_db_connection() as connection:
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_INSERT_INDEX_STOCK, parameters=index_stock_insert)
            connection.commit()
            connection.close()

    def deleteIndexStock(self):
        with dbConfig.create_db_connection() as connection:
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_DELETE_INDEX_STOCK)
            connection.commit()
            connection.close()


indexRepository = __IndexRepository()
