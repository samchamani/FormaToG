import argparse
import glob
import json
import os
import sys
import time
import shutil
import pandas as pd
from typing import List

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pattern",
        type=str,
        help="The matching pattern of experiments to merge (in results folder)",
        required=True,
    )
    parser.add_argument(
        "--new_name",
        type=str,
        help="The new name of the merged folder",
        required=True,
    )
    parser.add_argument(
        "--env_note",
        type=str,
        help="Additional info to add in the env_note field of the meta file",
    )

    args = parser.parse_args()

    current_dir = os.path.dirname(__file__)
    root_dir = os.path.abspath(os.path.join(current_dir, ".."))
    directories = glob.glob(os.path.join(root_dir, "results", args.pattern))

    print("Found result directories:")
    for dir in directories:
        print(dir)

    answer = ""
    while not answer:
        answer = input("\nContinue [y/n]?: ")
        if answer == "y":
            break
        if answer == "n":
            print("Cancelling merge process")
            sys.exit(0)

    meta_datas = []
    for dir in directories:
        with open(os.path.join(dir, "meta.json"), "r") as f:
            content = f.read()
            meta_datas.append(json.loads(content))

    print("Checking meta data against first entry...")
    experiment = meta_datas[0]["experiment"]
    methods: list = meta_datas[0]["methods"]
    agent = meta_datas[0]["agent"]
    provider = meta_datas[0]["provider"]
    graph = meta_datas[0]["graph"]
    questions = meta_datas[0]["questions"]

    with open(os.path.join(root_dir, "questions", questions + ".json"), "r") as f:
        content = f.read()
        num_questions = len(json.loads(content))

    min_q, max_q = meta_datas[0]["q_range"]

    for index, meta_data in enumerate(meta_datas):
        if experiment != meta_data["experiment"]:
            print("Experiments don't match at index", index)
            sys.exit(1)
        if set(methods) != set(meta_data["methods"]):
            print("Methods don't match at index", index)
            sys.exit(1)
        if agent != meta_data["agent"]:
            print("Agents don't match at index", index)
            sys.exit(1)
        if provider != meta_data["provider"]:
            print("Providers don't match at index", index)
            sys.exit(1)
        if graph != meta_data["graph"]:
            print("Graphs don't match at index", index)
            sys.exit(1)
        if questions != meta_data["questions"]:
            print("Question datasets don't match at index", index)
            sys.exit(1)
        q_from, q_to = meta_data["q_range"]
        min_q = min(min_q, q_from)
        max_q = max(max_q, q_to)
        max_q = min(max_q, num_questions)

    merged_meta = {
        "title": args.new_name,
        "experiment": experiment,
        "methods": methods,
        "agent": agent,
        "provider": provider,
        "graph": graph,
        "questions": questions,
        "q_range": [min_q, max_q],
        "repetitions": None,
        "env_note": "Merged data",
        "timestamp": time.time(),
    }
    if args.env_note:
        merged_meta["env_note"] += " | " + args.env_note
    merged_meta = json.dumps(merged_meta, ensure_ascii=False, indent=4)

    merged_data_dir = os.path.join(root_dir, "results", args.new_name)
    os.makedirs(merged_data_dir)
    print("New meta data:\n", merged_meta)

    with open(os.path.join(merged_data_dir, "meta.json"), "w") as f:
        f.write(merged_meta)

    print("Copying old files into new directory")
    old_meta_dir = os.path.join(merged_data_dir, "orig_meta_files")
    os.makedirs(old_meta_dir)
    new_raw_data_dir = os.path.join(merged_data_dir, "raw_data")
    os.makedirs(new_raw_data_dir)
    for meta_data in meta_datas:
        exp_name = meta_data["title"]
        with open(os.path.join(old_meta_dir, exp_name + "_meta.json"), "w") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=4)

    print("Starting data transfer...")
    time.sleep(5)

    sorted_dirs = sorted(directories, key=lambda d: int(d.split("-")[-2]))
    for method in methods:
        dfs: List[pd.DataFrame] = []
        for dir in sorted_dirs:
            result_files = glob.glob(
                os.path.join(dir, "raw_data", method, "results_*.csv")
            )
            for result_file in result_files:
                dfs.append(pd.read_csv(result_file))
            shutil.copytree(
                os.path.join(dir, "raw_data", method, "logs"),
                os.path.join(new_raw_data_dir, method, "logs"),
                dirs_exist_ok=True,
            )
        merged_data = pd.concat(dfs, ignore_index=True)
        merged_data.to_csv(
            os.path.join(new_raw_data_dir, method, "results_rep1.csv"), index=False
        )

    print("Data merge complete.")
