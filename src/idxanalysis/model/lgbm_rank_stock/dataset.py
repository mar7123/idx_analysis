from idxanalysis.config.AppConfig import appConfig
import numpy as np
import pandas as pd
from typing import cast


def __build_tabular_ranking_sequences(df: pd.DataFrame, target_col: str):
    features = appConfig.LGBM_RANK_STOCK_FEATURES
    df.sort_values(["timestamp", "stock_profile"], inplace=True)

    valid_timestamps = sorted(df["timestamp"].unique())

    X_tree_list: list[np.ndarray] = []
    y_tree_list: list[np.ndarray] = []
    tree_groups: list[int] = []

    for current_ts in valid_timestamps:
        day_slice = cast(pd.DataFrame, df[df["timestamp"] == current_ts])
        day_slice = day_slice.sort_values("stock_profile")
        X_tree_list.append(day_slice[features].values)
        y_tree_list.append(day_slice[target_col].to_numpy())
        tree_groups.append(len(day_slice))

    X_tree = np.vstack(X_tree_list) if X_tree_list else np.empty(
        (0, len(features)))
    y_tree = np.concatenate(y_tree_list) if y_tree_list else np.empty((0,))

    return X_tree, y_tree, np.array(tree_groups)


def make_sequences(df: pd.DataFrame):
    return __build_tabular_ranking_sequences(df, "future_target")


def make_inference_sequences(df: pd.DataFrame) -> np.ndarray:
    latest_ts = df['timestamp'].max()
    day_slice = cast(pd.DataFrame, df[df['timestamp'] == latest_ts]).sort_values(
        "stock_profile")

    X_tree = day_slice[appConfig.LGBM_RANK_STOCK_FEATURES].values

    return X_tree
