from pathlib import Path


class __AppConfig:
    __package_dir: Path = Path()

    def setPackageDir(self, packageDir: Path):
        self.__package_dir = packageDir

    LOG_FILE_NAME = "log.txt"

    @property
    def log_dir(self) -> Path:
        return self.__package_dir.joinpath("log")

    SQL_GET_TIME_DIMENSIONS = "SELECT * from time_dimensions"
    SQL_INSERT_TIME_DIMENSIONS = "INSERT IGNORE INTO time_dimensions VALUES (:tm)"
    SQL_GET_INDEX_PROFILES = "SELECT * from index_profiles"
    SQL_INSERT_INDEX_PROFILES = "INSERT IGNORE INTO index_profiles (index_code) VALUE (:index_code)"
    SQL_INSERT_INDEX_DATA = "INSERT IGNORE INTO index_data VALUE (:index_profile, :timestamp, :previous, :highest, :lowest, :close, :number_of_stock, :change, :volume, :value, :frequency, :market_capital)"
    SQL_INSERT_STOCK_PROFILES = "INSERT INTO stock_profiles VALUE (:stock_code, :stock_name, :remarks, :delisting_date) ON DUPLICATE KEY UPDATE delisting_date = delisting_date"
    SQL_INSERT_STOCK_DATA = "INSERT IGNORE INTO stock_data VALUE (:stock_profile, :timestamp, :previous, :open_price, :first_trade, :high, :low, :close, :change, :volume, :value, :frequency, :index_individual, :offer, :offer_volume, :bid, :bid_volume, :listed_shares, :tradeble_shares, :weight_for_index, :foreign_sell, :foreign_buy, :non_regular_volume, :non_regular_value, :non_regular_frequency, :persen, :percentage)"
    SQL_INSERT_CURRENCY_EXCHANGE_RATE_DATA = "INSERT IGNORE INTO currency_exchange_rates VALUES (:primary_code, :secondary_code, :primary_value, :secondary_value, :timestamp)"
    SQL_INSERT_INDEX_STOCK = "INSERT IGNORE INTO index_stock VALUE (:index_code, :stock_code)"
    SQL_DELETE_INDEX_STOCK = "DELETE from index_stock"

    SQL_LGBM_RANK_STOCK_GET_INFERENCE = "SELECT * FROM stock_inference"
    SQL_LGBM_RANK_STOCK_GET_TRAIN = "SELECT * FROM stock_train"
    SQL_LGBM_RANK_STOCK_GET_VAL = "SELECT * FROM stock_val"

    SCRAPE_DAY_WINDOW = 800
    INDEX_URL = "https://www.idx.co.id/primary/TradingSummary/GetIndexSummary"
    STOCK_URL = "https://www.idx.co.id/primary/TradingSummary/GetStockSummary"
    INDEX_STOCK_URL = "https://idx.co.id/secondary/get/StockData/GetStockUploader"
    SCRAPE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Referer": "https://www.idx.co.id/",
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    SCRAPE_IDX_HEADERS = {
        **SCRAPE_HEADERS,
        "Referer": "https://www.idx.co.id/",
    }

    def currency_exchange_rates_url(self, oldest_date: str, latest_date: str):
        return f"https://api.frankfurter.dev/v1/{oldest_date}..{latest_date}"

    def index_stock_report_url(self, index_stock_report_path: str):
        return "https://idx.co.id" + \
            index_stock_report_path.replace("\\", "/")

    @property
    def scrape_index_stock_zip_dir(self) -> Path:
        return self.__package_dir.joinpath("scrape", "stock_index_files")

    @property
    def model_output_dir(self) -> Path:
        return self.__package_dir.joinpath("output")

    LGBM_RANK_STOCK_FEATURES = [
        # Index
        "idx_close_pos",
        "idx_range",
        "idx_ret_1d",
        "idx_ret_5d",
        "idx_ret_20d",
        "idx_ret_60d",
        "idx_vol_20d",
        "idx_vol_60d",
        "idx_ret_ma_20d",
        "idx_ret_ma_60d",
        "idx_drawdown_20d",
        "idx_drawdown_60d",
        # Currency
        "currency_exchange_rate_ret_1d",
        "currency_exchange_rate_ret_5d",
        "currency_exchange_rate_ret_20d",
        "currency_exchange_rate_ret_60d",
        "currency_exchange_rate_vol_20d",
        "currency_exchange_rate_vol_60d",
        "currency_exchange_rate_ma_20d",
        "currency_exchange_rate_ma_60d",
        # Stock
        "is_active",
        "is_active_5d",
        "turnover_rank",
        "foreign_flow_rank",
        "order_imbalance_rank",
        "relative_spread_rank",
        "non_regular_activity_rank",
        "ret_1d",
        "ret_5d",
        "ret_20d",
        "ret_60d",
        "gap_rank",
        "intraday_range_rank",
        "close_position",
        "drawdown_20d",
        "drawdown_60d",
        "vol_20d",
        "vol_60d",
        "ret_ma_20d",
        "ret_ma_60d",
        "dow_sin",
        "dow_cos",
        "woy_sin",
        "woy_cos",
        "month_sin",
        "month_cos",
    ]

    @property
    def lgbm_rank_stock_output_path(self) -> Path:
        return self.model_output_dir.joinpath("lgbm_rank_stock_output.xlsx")


appConfig = __AppConfig()
