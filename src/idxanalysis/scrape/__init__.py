from idxanalysis.data_model.scrape_model import IndexSummaryResponse, StockSummaryResponse, CurrencyExchangeRateResponse, StockIndexResponse
from idxanalysis.config.AppConfig import appConfig
from idxanalysis.repository.TimeDimensionRepository import timeDimensionRepository
from idxanalysis.repository.IndexRepository import indexRepository
from idxanalysis.repository.StockRepository import stockRepository
from idxanalysis.repository.CurrencyExchangeRateRepository import currencyExchangeRateRepository
from datetime import datetime, timedelta
import random
import time
import os
from pathlib import Path
import zipfile
from typing import Iterator, cast
import pandas as pd
import shutil
import gc
import undetected_chromedriver as uc  # type: ignore
from urllib.parse import urlencode, urlsplit, quote, urlunsplit, parse_qsl
from idxanalysis.utils.LogUtils import LogUtils
import json


def sanitize_url(raw_url: str, params: dict[str, str] = {}) -> str:
    raw_url = raw_url + "?" + urlencode(params)
    components = urlsplit(raw_url)
    fixed_path = quote(components.path)
    query_params = parse_qsl(components.query, keep_blank_values=True)
    fixed_query = urlencode(query_params)
    clean_url = urlunsplit((
        components.scheme,
        components.netloc,
        fixed_path,
        fixed_query,
        components.fragment
    ))
    return clean_url


def uc_client_request(driver: uc.Chrome, url: str, waitForDownload: bool = False, timeout: int = 30):
    driver.get(url)
    LogUtils.append_log(url)

    status_code = 0
    request_id = ""
    body = ""

    start_time = time.time()
    download_completed = False

    while time.time() - start_time < timeout:
        try:
            logs = driver.get_log("performance")  # type: ignore
            for entry in logs:
                log_message = json.loads(entry["message"])["message"]
                method = log_message.get("method")

                if method == "Network.responseReceived":
                    response = log_message["params"]["response"]
                    if response["url"] == url:
                        status_code = cast(int, response["status"])
                        request_id = log_message["params"]["requestId"]

                if method == "Page.downloadProgress":
                    if log_message["params"].get("state") == "completed":
                        download_completed = True

            if request_id and (not waitForDownload or download_completed):
                break
            elif not waitForDownload and request_id:
                break
            elif download_completed:
                break

        except Exception as e:
            print(e)

        time.sleep(0.5)

    if request_id:
        try:
            body = cast(str, driver.execute_cdp_cmd('Network.getResponseBody', {  # type: ignore
                'requestId': request_id
            })["body"])
        except Exception as e:
            print(f"Error getting response body: {e}")

    return status_code, body


def rand_sleep():
    num = random.randint(200, 500)
    time.sleep(num / 100)


def scrape_index_stock(driver: uc.Chrome):
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
            status_code, body = uc_client_request(
                driver, sanitize_url(appConfig.SCRAPE_INDEX_STOCK_URL, params))
            if status_code != 200:
                LogUtils.append_log(
                    f"{status_code}\n{body}")
                break
            index_summary = StockIndexResponse.model_validate_json(body)

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

    index_stock_extract_path = appConfig.SCRAPE_INDEX_STOCK_ZIP_DIR
    # zip_tmp_file = index_stock_extract_path / "temp_downloaded_file.zip"
    index_stock_extract_path.mkdir(parents=True, exist_ok=True)

    for index_stock_report_path in index_stock_report_paths:
        index_stock_report_url = appConfig.index_stock_report_url(
            index_stock_report_path)
        status_code, body = uc_client_request(
            driver, sanitize_url(index_stock_report_url), waitForDownload=True)
        if status_code != 200:
            LogUtils.append_log(
                f"{status_code}\n{body}")
            rand_sleep()
            continue
        first_zip = next(index_stock_extract_path.glob("*.zip"), None)
        if not first_zip:
            continue

        LogUtils.append_log(f"Download {index_stock_report_url}")

        # Extract the ZIP contents
        LogUtils.append_log(f"Extracting files {index_stock_report_url}")
        with zipfile.ZipFile(first_zip, 'r') as zip_ref:
            for info in zip_ref.infolist():
                if not info.filename.endswith(".xlsx"):
                    continue
                extracted_path = zip_ref.extract(
                    info, index_stock_extract_path)
                date_time = info.date_time
                time_tuple = date_time + (0, 0, -1)
                timestamp = time.mktime(time_tuple)

                os.utime(extracted_path, (timestamp, timestamp))
        first_zip.unlink()
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
    options = uc.ChromeOptions()
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    prefs: dict[str, str | bool] = {
        "download.default_directory": str(appConfig.SCRAPE_INDEX_STOCK_ZIP_DIR.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)  # type: ignore
    driver = uc.Chrome(options=options)
    try:
        for timestamp in filtered_dates:
            timestamp_url_param = timestamp.strftime("%Y%m%d")
            params = {
                "length": "9999",
                "start": "0",
                "date": timestamp_url_param,
            }

            status_code, body = uc_client_request(
                driver, sanitize_url(appConfig.SCRAPE_INDEX_URL, params))
            if status_code != 200:
                LogUtils.append_log(
                    f"{status_code}\n{body}")
                raise Exception(status_code)

            index_summary = IndexSummaryResponse.model_validate_json(body)

            status_code, body = uc_client_request(
                driver, sanitize_url(appConfig.SCRAPE_STOCK_URL, params))
            if status_code != 200:
                LogUtils.append_log(
                    f"{status_code}\n{body}")
                raise Exception(status_code)
            stock_summary = StockSummaryResponse.model_validate_json(body)

            # Get Currency Exchange Data
            oldest_date = timestamp.strftime("%Y-%m-%d")
            latest_date = timestamp.strftime("%Y-%m-%d")
            params = {
                "base": currencyExchangeRateRepository.primary_currency,
                "symbols": currencyExchangeRateRepository.secondary_currency,
            }
            status_code, body = uc_client_request(driver, sanitize_url(appConfig.currency_exchange_rates_url(
                oldest_date, latest_date), params))
            if status_code != 200:
                LogUtils.append_log(
                    f"{status_code}\n{body}")
                raise Exception(status_code)
            currency_exchange_rate_data = CurrencyExchangeRateResponse.model_validate_json(
                body)

            timeDimensionRepository.insertTimeDimension(timestamp)
            if len(stock_summary.data) != 0 and len(index_summary.data) != 0:
                indexRepository.insertIndexData(index_summary)
                stockRepository.insertStockData(stock_summary)
                currencyExchangeRateRepository.insertCurrencyExchangeRateData(
                    currency_exchange_rate_data)
            else:
                LogUtils.append_log("Data Empty")
            rand_sleep()
        scrape_index_stock(driver)
    finally:
        driver.quit()
    # Get Index Stock
    gc.collect()
    shutil.rmtree(appConfig.SCRAPE_INDEX_STOCK_ZIP_DIR)

    LogUtils.append_log("SCRAPE END")
