import pandas as pd
import lightgbm as lgb
import gc
import numpy as np
from idxanalysis.model.lgbm_rank_stock.dataset import make_sequences
from idxanalysis.config.AppConfig import appConfig
from idxanalysis.repository.SqlRepository import sqlRepository


def train_model(rand: int, inference_input: np.ndarray):
    train_df = sqlRepository.pandasRead(
        appConfig.SQL_LGBM_RANK_STOCK_GET_TRAIN)
    val_df = sqlRepository.pandasRead(appConfig.SQL_LGBM_RANK_STOCK_GET_VAL)

    X_train_tree, y_train_tree, train_groups = make_sequences(
        df=train_df)
    X_val_tree, y_val_tree, val_groups = make_sequences(
        df=val_df)
    del train_df, val_df
    gc.collect()

    print("TRAIN------------------------")
    print(X_train_tree.shape)
    print(X_val_tree.shape)

    tree_model = lgb.LGBMRanker(
        objective='lambdarank',
        metric='ndcg',
        ndcg_eval_at=[3, 5],  # cite: 6
        label_gain=list(range(101)),
        num_leaves=128,
        min_child_samples=50,
        colsample_bytree=0.8,
        subsample=0.7,
        subsample_freq=1,
        learning_rate=5e-3,
        n_estimators=5000,
        random_state=rand,
    )

    tree_model.fit(  # type: ignore
        X_train_tree, y_train_tree,
        group=train_groups,
        eval_set=[(X_val_tree, y_val_tree)],
        eval_group=[val_groups],
        callbacks=[
            lgb.early_stopping(stopping_rounds=300),
            lgb.log_evaluation(period=100),
        ],
    )

    X_tree = inference_input

    tree_pred = tree_model.predict(X_tree)

    tree_results = tree_model.evals_result_

    tree_best_iter = tree_model.best_iteration_
    tree_best_val_metric = tree_results['valid_0']['ndcg@5'][tree_best_iter - 1]

    feature_importances = pd.DataFrame({
        "features": appConfig.LGBM_RANK_STOCK_FEATURES,
        "scores": tree_model.feature_importances_,
    })
    print(feature_importances)

    return tree_pred, tree_best_val_metric
