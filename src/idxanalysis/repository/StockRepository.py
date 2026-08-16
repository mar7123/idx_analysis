from typing import Mapping

from idxanalysis.config.DbConfig import dbConfig
from idxanalysis.config.AppConfig import appConfig
from idxanalysis.data_model.scrape_model import StockSummaryResponse


class __StockRepository:
    def insertStockData(self, stock_summary: StockSummaryResponse):
        stock_profiles: list[Mapping[str, object]] = []
        stock_data: list[Mapping[str, object]] = []
        for i in stock_summary.data:
            stock_profiles.append(
                {
                    "stock_code": i.StockCode,
                    "stock_name": i.StockName,
                    "remarks": i.Remarks,
                    "delisting_date": (None if i.DelistingDate is None else None if len(i.DelistingDate) == 0 else i.DelistingDate),
                }
            )
            stock_data.append(
                {
                    "stock_profile": i.StockCode,
                    "timestamp": i.Date,
                    "previous": i.Previous,
                    "open_price": i.OpenPrice,
                    "first_trade": i.FirstTrade,
                    "high": i.High,
                    "low": i.Low,
                    "close": i.Close,
                    "change": i.Change,
                    "volume": i.Volume,
                    "value": i.Value,
                    "frequency": i.Frequency,
                    "index_individual": i.IndexIndividual,
                    "offer": i.Offer,
                    "offer_volume": i.OfferVolume,
                    "bid": i.Bid,
                    "bid_volume": i.BidVolume,
                    "listed_shares": i.ListedShares,
                    "tradeble_shares": i.TradebleShares,
                    "weight_for_index": i.WeightForIndex,
                    "foreign_sell": i.ForeignSell,
                    "foreign_buy": i.ForeignBuy,
                    "non_regular_volume": i.NonRegularVolume,
                    "non_regular_value": i.NonRegularValue,
                    "non_regular_frequency": i.NonRegularFrequency,
                    "persen": i.persen,
                    "percentage": i.percentage,
                }
            )

        with dbConfig.create_db_connection() as connection:
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_INSERT_STOCK_PROFILES, parameters=stock_profiles)
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_INSERT_STOCK_DATA, parameters=stock_data)
            connection.commit()
            connection.close()


stockRepository = __StockRepository()
