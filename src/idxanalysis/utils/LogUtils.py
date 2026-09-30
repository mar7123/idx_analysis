from datetime import datetime
from idxanalysis.config.AppConfig import appConfig
import os


class LogUtils:
    @staticmethod
    def __insert_log(msg: str, mode: str):
        file_path = appConfig.LOG_DIR
        file_path.mkdir(parents=True, exist_ok=True)
        with open(os.path.join(file_path, appConfig.LOG_FILE_NAME), mode) as fw:
            fw.write(f"{datetime.now()} - {msg}\n")

    @staticmethod
    def write_log(msg: str):
        LogUtils.__insert_log(msg, "w")

    @staticmethod
    def append_log(msg: str):
        LogUtils.__insert_log(msg, "a")
