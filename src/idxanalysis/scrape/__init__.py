from idxanalysis.data_model.scrape_model import IndexSummaryResponse, StockSummaryResponse, CurrencyExchangeRateResponse, StockIndexResponse
from idxanalysis.config.AppConfig import appConfig
from idxanalysis.repository.TimeDimensionRepository import timeDimensionRepository
from idxanalysis.repository.IndexRepository import indexRepository
from idxanalysis.repository.StockRepository import stockRepository
from idxanalysis.repository.CurrencyExchangeRateRepository import currencyExchangeRateRepository
from datetime import datetime, timedelta
from curl_cffi import requests
import random
import time
import os
from pathlib import Path
import zipfile
from typing import Iterator
import pandas as pd
import shutil
import gc

from idxanalysis.utils.LogUtils import LogUtils


def rand_sleep():
    num = random.randint(200, 500)
    time.sleep(num / 100)


def scrape_index_stock(session: requests.Session):
    index_profiles = set(indexRepository.getIndexProfiles())
    index_stock_report_paths = set[str]()
    for index_profile in index_profiles:
        year = datetime.now().year
        max_tries = 3
        while max_tries > 0:
            params = {
                "typeIndex": index_profile,
                "year": str(year),
                "table": "stockIndex",
                "locale": "id",
            }
            index_stock_response = session.get(
                appConfig. INDEX_STOCK_URL, params=params, impersonate="chrome124")
            LogUtils.append_log(index_stock_response.url)
            if index_stock_response.status_code != 200:
                LogUtils.append_log(
                    f"{index_stock_response.status_code}\n{index_stock_response.content}")
                break
            index_summary = StockIndexResponse.model_validate_json(
                index_stock_response.content)

            if len(index_summary.Results) != 0:
                sorted_results = sorted(index_summary.Results,
                                        key=lambda x: datetime.fromisoformat(x.Date))
                latest_result = sorted_results[-1]
                index_stock_report_paths.add(latest_result.AttachmentUrl)
                break
            else:
                year -= 1
                max_tries -= 1
                rand_sleep()

        rand_sleep()

    index_stock_extract_path = appConfig.scrape_index_stock_zip_dir
    zip_tmp_file = index_stock_extract_path / "temp_downloaded_file.zip"
    index_stock_extract_path.mkdir(parents=True, exist_ok=True)

    for index_stock_report_path in index_stock_report_paths:
        index_stock_report_url = appConfig.index_stock_report_url(
            index_stock_report_path)
        index_stock_report_zip_response = session.get(
            index_stock_report_url, impersonate="chrome124")
        LogUtils.append_log(index_stock_report_zip_response.url)
        if index_stock_report_zip_response.status_code != 200:
            LogUtils.append_log(
                f"{index_stock_report_zip_response.status_code}\n{index_stock_report_zip_response.content}")
            rand_sleep()
            continue

        with open(zip_tmp_file, "wb") as f:
            f.write(index_stock_report_zip_response.content)

        LogUtils.append_log(f"Download {index_stock_report_url}")

        # Extract the ZIP contents
        LogUtils.append_log(f"Extracting files {index_stock_report_url}")
        with zipfile.ZipFile(zip_tmp_file, 'r') as zip_ref:
            for info in zip_ref.infolist():
                if not info.filename.endswith(".xlsx"):
                    continue
                extracted_path = zip_ref.extract(
                    info, index_stock_extract_path)
                date_time = info.date_time
                time_tuple = date_time + (0, 0, -1)
                timestamp = time.mktime(time_tuple)

                os.utime(extracted_path, (timestamp, timestamp))
        zip_tmp_file.unlink()
        rand_sleep()

    files: Iterator[Path] = index_stock_extract_path.glob("*.xlsx")
    sorted_files = sorted(
        [f for f in files if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    index_stock_map = dict[str, set[str]]()
    for file_path in sorted_files:
        if not os.path.exists(file_path):
            continue

        xls = pd.ExcelFile(file_path)

        for sheet_name in xls.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name,  # type: ignore
                               header=None)

            index_name = None
            for row_idx, row in df.iterrows():
                row_str_list = row.astype(str).tolist()
                if any("Nama Indeks" in str(cell) for cell in row_str_list):
                    non_null_cells = [str(c).strip()
                                      for c in row_str_list if pd.notna(c)]
                    full_text = " ".join(non_null_cells)
                    if ":" in full_text:
                        index_name = full_text.split(":")[-1].strip()
                    else:
                        index_name = non_null_cells[-1].strip()
                    break

            if not index_name:
                continue
            if index_name == "IHSG":
                index_name = "COMPOSITE"

            if index_name not in index_stock_map:
                index_stock_map[index_name] = set[str]()
            else:
                continue

            kode_col_idx: int | None = None
            start_row: int | None = None

            for i, (_, row) in enumerate(df.iterrows()):
                row_str_list = [str(cell).strip() for cell in row.tolist()]

                if "Kode" in row_str_list:
                    kode_col_idx = row_str_list.index("Kode")
                    continue

                if kode_col_idx is not None and row_str_list[kode_col_idx] != "nan":
                    start_row = i
                    break

            if kode_col_idx is None or start_row is None:
                continue

            for row_idx in range(start_row, len(df)):
                val = df.iloc[row_idx, kode_col_idx]

                if pd.isna(val):
                    break

                stock_code = str(val).strip()
                index_stock_map[index_name].add(stock_code)

    indexRepository.deleteIndexStock()
    indexRepository.insertIndexStock(index_stock_map)


def main():
    LogUtils.append_log("SCRAPE START")
    now = datetime.now()
    end = (now if now.hour >= 17 else now - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = end - timedelta(days=appConfig.SCRAPE_DAY_WINDOW)

    all_dates = {start + timedelta(days=i)
                 for i in range((end - start).days + 1)}
    time_dimension_dates = timeDimensionRepository.getTimeDimensions()
    filtered_dates = sorted(all_dates - set(time_dimension_dates))

    session = requests.Session()
    session.headers.update(appConfig.SCRAPE_IDX_HEADERS)
    for timestamp in filtered_dates:
        timestamp_url_param = timestamp.strftime("%Y%m%d")
        params = {
            "length": "9999",
            "start": "0",
            "date": timestamp_url_param,
        }

        # Get Index Data
        index_response = session.get(
            appConfig.INDEX_URL, params=params, impersonate="chrome124"
        )
        LogUtils.append_log(index_response.url)
        if index_response.status_code != 200:
            LogUtils.append_log(
                f"{index_response.status_code}\n{index_response.content}")
            raise Exception(index_response.status_code)
        index_summary = IndexSummaryResponse.model_validate_json(
            index_response.content)

        # Get Stock Data
        stock_response = session.get(
            appConfig.STOCK_URL, params=params, impersonate="chrome124"
        )
        LogUtils.append_log(stock_response.url)
        if stock_response.status_code != 200:
            LogUtils.append_log(
                f"{stock_response.status_code}\n{stock_response.content}")
            raise Exception(stock_response.status_code)
        stock_summary = StockSummaryResponse.model_validate_json(
            stock_response.content)

        # Get Currency Exchange Data
        oldest_date = timestamp.strftime("%Y-%m-%d")
        latest_date = timestamp.strftime("%Y-%m-%d")
        params = {
            "base": currencyExchangeRateRepository.primary_currency,
            "symbols": currencyExchangeRateRepository.secondary_currency,
        }
        currency_exchange_rate_response = session.get(
            appConfig.currency_exchange_rates_url(oldest_date, latest_date), params=params,  headers=appConfig.SCRAPE_HEADERS, impersonate="chrome124"
        )
        LogUtils.append_log(currency_exchange_rate_response.url)
        if currency_exchange_rate_response.status_code != 200:
            LogUtils.append_log(
                f"{currency_exchange_rate_response.status_code}\n{currency_exchange_rate_response.content}")
            raise Exception(currency_exchange_rate_response.status_code)
        currency_exchange_rate_data = CurrencyExchangeRateResponse.model_validate_json(
            currency_exchange_rate_response.content)

        timeDimensionRepository.insertTimeDimension(timestamp)
        if len(stock_summary.data) != 0 and len(index_summary.data) != 0:
            indexRepository.insertIndexData(index_summary)
            stockRepository.insertStockData(stock_summary)
            currencyExchangeRateRepository.insertCurrencyExchangeRateData(
                currency_exchange_rate_data)
        else:
            LogUtils.append_log("Data Empty")
        rand_sleep()

    # Get Index Stock
    scrape_index_stock(session)
    gc.collect()
    shutil.rmtree(appConfig.scrape_index_stock_zip_dir)

    LogUtils.append_log("SCRAPE END")
