"""
Calculates metrics of results.
Before running this, first run preprocess.py!

In case of repetitions, averages are calculated as average over reps, then average of those averages -> macro average.
for f1 this is the recommended way due to more robustness (macro f1 and macro f1).
micro averages are neglected to avoid uneqaully weighted questions (100 times question 1, 1 time question 2)
"""

from evaluation.utils import get_exp_and_dir_from_arg, DATA_TYPE_MAP
import pandas as pd
import os

if __name__ == "__main__":
    exp_name, exp_dir = get_exp_and_dir_from_arg()
    print(f"Initiating analysis of results for experiment {exp_name}")

    df = pd.read_csv(os.path.join(exp_dir, "results.csv"), dtype=DATA_TYPE_MAP)
    question_stats = (
        df.groupby(["method", "question_index"])
        .agg(
            q_has_err=("has_err", "mean"),
            q_has_err_and_correct=("has_err_and_correct", "mean"),
            q_has_err_instruction=("has_err_instruction", "mean"),
            q_has_err_tog=("has_err_tog", "mean"),
            q_has_err_graph=("has_err_graph", "mean"),
            q_has_err_other=("has_err_other", "mean"),
            q_has_err_agent=("has_err_agent", "mean"),
            q_is_kg_based_answer=("is_kg_based_answer", "mean"),
            q_is_kg_and_correct=("is_kg_and_correct", "mean"),
            q_kg_calls=("kg_calls", "mean"),
            q_agent_calls=("agent_calls", "mean"),
            q_reached_depth=("reached_depth", "mean"),
            q_duration=("duration", "mean"),
            q_exact_match=("exact_match", "mean"),
            q_f1=("f1", "mean"),
            q_is_no_answer=("is_no_answer", "mean"),
        )
        .reset_index()
    )

    metrics = [
        "has_err",
        "has_err_and_correct",
        "has_err_instruction",
        "has_err_tog",
        "has_err_graph",
        "has_err_other",
        "has_err_agent",
        "is_kg_based_answer",
        "is_kg_and_correct",
        "kg_calls",
        "agent_calls",
        "reached_depth",
        "duration",
        "exact_match",
        "f1",
        "is_no_answer",
    ]
    dfs = []
    for metric in metrics:
        grouped = question_stats.groupby("method")[f"q_{metric}"]
        metric_desc = grouped.describe()
        metric_sum = grouped.sum()
        metric_df = pd.concat([metric_desc, metric_sum.rename("sum")], axis=1)
        metric_df["metric"] = metric
        metric_df = metric_df.reset_index()
        dfs.append(metric_df)

    all_metrics = pd.concat(dfs, ignore_index=True)
    cols = all_metrics.columns.tolist()
    cols.insert(0, cols.pop(cols.index("metric")))
    all_metrics = all_metrics[cols]
    final_file = os.path.join(exp_dir, "agg_results.csv")
    print(f"Exporting to {final_file}")
    all_metrics.to_csv(final_file, index=False)
