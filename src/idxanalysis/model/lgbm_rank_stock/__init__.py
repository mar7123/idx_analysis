from pathlib import Path
from idxanalysis.model.lgbm_rank_stock.train_model import train_model
from idxanalysis.model.lgbm_rank_stock.dataset import make_inference_sequences
from idxanalysis.sql.loader import load_sql_path
from idxanalysis.repository.SqlRepository import sqlRepository
from idxanalysis.utils.LogUtils import LogUtils
from idxanalysis.config.AppConfig import appConfig
import pandas as pd
import numpy as np
import gc
import tensorflow as tf
import random


def main():
    dir = Path(__file__).parent.name
    LogUtils.append_log(f"START {dir}")
    sqlRepository.executeSQL(load_sql_path(dir=dir, filename="prep.sql"))
    inference_df = sqlRepository.pandasRead(
        appConfig.SQL_LGBM_RANK_STOCK_GET_INFERENCE)
    stock_profile_set: set[str] = set()
    for stock_profile in inference_df["stock_profile"].values:
        stock_profile_set.add(stock_profile)
    stock_profile_mapper = {label: i for i,
                            label in enumerate(sorted(stock_profile_set))}
    stock_profile_mapper_reversed = {
        v: k for k, v in stock_profile_mapper.items()}
    inference_input = make_inference_sequences(inference_df)
    del inference_df
    gc.collect()
    result_df = pd.DataFrame()
    val_metric_df = pd.DataFrame()
    num_train = 8
    for i in range(num_train):
        rand = random.randint(1, 1000)
        random.seed(rand)
        tf.random.set_seed(rand)
        np.random.seed(rand)
        return_pred, return_val_metric = train_model(
            rand=rand, inference_input=inference_input)

        val_metric_df[f"val_metric_{i}"] = [return_val_metric]

        X_infer_id = sorted(stock_profile_mapper.values())
        temp_df = pd.DataFrame({
            "stock_id": X_infer_id,
            "return_pred": return_pred,
        })
        print(temp_df)
        temp_df["return_pred"] = temp_df["return_pred"].rank(pct=True)

        temp_df["stock_profile"] = temp_df["stock_id"].map(
            stock_profile_mapper_reversed)
        temp_df["result_score"] = temp_df["return_pred"]

        if i == 0:
            result_df["stock_profile"] = temp_df["stock_profile"]
        result_df[f"result_score{i}"] = temp_df["result_score"]

        del temp_df

        tf.keras.backend.clear_session()  # type: ignore

        gc.collect()

    result_df["score"] = result_df[[
        f'result_score{i}' for i in range(num_train)]].mean(axis=1)
    result_df["score_std"] = result_df[[
        f'result_score{i}' for i in range(num_train)]].std(axis=1)
    
    output_path = appConfig.model_output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(appConfig.lgbm_rank_stock_output_path, engine="openpyxl") as writer:
        result_df.to_excel(  # type: ignore
            writer, sheet_name="result_df", index=False)
        val_metric_df.to_excel(  # type: ignore
            writer, sheet_name="val_metric_df", index=False)

    sqlRepository.executeSQL(load_sql_path(dir=dir, filename="clean.sql"))
    LogUtils.append_log(f"END {dir}")
