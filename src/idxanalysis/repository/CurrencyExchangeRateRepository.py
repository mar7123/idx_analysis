from typing import Mapping

from idxanalysis.config.DbConfig import dbConfig
from idxanalysis.config.AppConfig import appConfig
from idxanalysis.data_model.scrape_model import CurrencyExchangeRateResponse


class __CurrencyExchangeRateRepository:
    primary_currency = "USD"
    secondary_currency = "IDR"

    def insertCurrencyExchangeRateData(self, currency_exchange_rate_data: CurrencyExchangeRateResponse):
        rate_data: list[Mapping[str, object]] = []
        for date, rate_info in currency_exchange_rate_data.rates.items():
            currency_value = rate_info[self.secondary_currency]
            rate_data.append(
                {
                    "primary_code": self.primary_currency,
                    "secondary_code": self.secondary_currency,
                    "primary_value": 1,
                    "secondary_value": currency_value,
                    "timestamp": date,
                }
            )

        with dbConfig.create_db_connection() as connection:
            dbConfig.query(
                connection=connection, sql=appConfig.SQL_INSERT_CURRENCY_EXCHANGE_RATE_DATA, parameters=rate_data)
            connection.commit()
            connection.close()


currencyExchangeRateRepository = __CurrencyExchangeRateRepository()
