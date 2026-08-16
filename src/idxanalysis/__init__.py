# import idxanalysis.scrape as scrape
import idxanalysis.model.lgbm_rank_stock as lgbm_rank_stock
from idxanalysis.config.AppConfig import appConfig
from pathlib import Path

from idxanalysis.utils.LogUtils import LogUtils


def main():
    appConfig.setPackageDir(Path(__file__).parent)
    LogUtils.write_log("START")
    # scrape.main()
    lgbm_rank_stock.main()
    LogUtils.append_log("END")
