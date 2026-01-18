import os
import glob
import json
import argparse
from evaluation.utils import (
    extract_meta_from_result_path,
    normalize_answer,
    get_tokens,
    DATA_TYPE_MAP,
)
import pandas as pd
from collections import Counter


def compute_exact_match(expected_answer: str, predicted_answer: str):
    """Exact match calculated the same as in SQUAD"""
    return int(normalize_answer(expected_answer) == normalize_answer(predicted_answer))


def compute_f1(expected_answer: str, predicted_answer: str):
    """F1 calculated the same as in SQUAD"""
    exp_toks = get_tokens(expected_answer)
    pred_toks = get_tokens(predicted_answer)
    tp_fp = len(pred_toks)
    tp_fn = len(exp_toks)
    if tp_fp == 0 or tp_fn == 0:
        # If either is no-answer, then F1 is 1 if they agree, 0 otherwise
        return float(exp_toks == pred_toks)

    common = Counter(exp_toks) & Counter(pred_toks)
    tp = 1.0 * sum(common.values())
    if tp == 0.0:
        return 0.0

    precision = tp / tp_fp
    recall = tp / tp_fn
    f1 = (2 * precision * recall) / (precision + recall)
    return f1


def compute_no_answer(expected_answer: str, predicted_answer: str):
    return int(len(str(predicted_answer)) == 0 and len(str(expected_answer)) > 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exp",
        type=str,
        help="the name of the experiment folder in results/",
        required=True,
    )

    args = parser.parse_args()
    exp_name = args.exp

    current_dir = os.path.dirname(__file__)
    exp_dir = os.path.abspath(os.path.join(current_dir, "..", "results", exp_name))
    if not os.path.exists(exp_dir):
        raise NotADirectoryError("No such directory", exp_dir)

    print(f"Initiating preprocessing of results for experiment {exp_name}")

    search_pattern = os.path.join(exp_dir, "raw_data", "**", "results_rep*.csv")
    result_file_paths = glob.glob(search_pattern)
    if not result_file_paths:
        raise FileNotFoundError("No results files found.")
    print(f"Found {len(result_file_paths)} result files")
    with open(os.path.join(exp_dir, "meta.json")) as f:
        meta_data = json.loads(f.read())
        print("Loaded meta file")

    dfs = []
    for path in result_file_paths:
        method, rep = extract_meta_from_result_path(path)

        print(f"Reading results of {method} for repetition {rep}")
        df = pd.read_csv(path, dtype=DATA_TYPE_MAP)
        df["answer"] = df["answer"].fillna("")
        df["exact_match"] = df.apply(
            lambda row: compute_exact_match(row["expected_answer"], row["answer"]),
            axis=1,
        )
        df["f1"] = df.apply(
            lambda row: compute_f1(row["expected_answer"], row["answer"]), axis=1
        )
        df["is_no_answer"] = df.apply(
            lambda row: compute_no_answer(row["expected_answer"], row["answer"]), axis=1
        )
        df["method"] = method
        df["rep"] = rep
        df["model"] = meta_data["agent"]
        df["questions"] = meta_data["questions"]

        dfs.append(df)

    all_data = pd.concat(dfs, ignore_index=True)
    final_file = os.path.join(exp_dir, "results.csv")
    print(f"Exporting to {final_file}")
    all_data.to_csv(final_file, index=False)
