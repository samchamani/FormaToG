from graphs.registry import graph_service
from agents.registry import agent_provider
import evaluation.utils as utils
import argparse
import os
import json
import csv
import time
import tqdm


if __name__ == "__main__":

    # ---------------------------------------------------------------------------- #
    #                                     SETUP                                    #
    # ---------------------------------------------------------------------------- #

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--title", type=str, required=True, help="The folder name for the results"
    )
    parser.add_argument(
        "--graph",
        choices=list(graph_service.keys()),
        required=True,
        help="The graph to use for knowledge retrieval",
    )
    parser.add_argument(
        "--agent_provider",
        choices=list(agent_provider.keys()),
        required=True,
        help="The service that provides the language model (ollama, google, ..)",
    )
    parser.add_argument(
        "--agent",
        type=str,
        required=True,
        help="Language Model to use as agent (must be available through agent provider)",
    )
    parser.add_argument(
        "--questions",
        type=str,
        required=True,
        help="Question catalogue to use. Catalogue must be a JSON file in /questions. Enter the file name without '.json'.",
    )
    parser.add_argument(
        "--questions_from",
        type=int,
        help="The index marking the first question to be used (inclusive start index)",
    )
    parser.add_argument(
        "--questions_to",
        type=int,
        help="The index marking up to which question questions will be used (exclusive end index)",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        type=str,
        required=True,
        help="Methods to evaluate. Named after method files in /methods. For tog methods extend the name with max depth and max paths like so 'tog_d{max_depth}_p{max_paths}'.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="How often each question is repeated",
    )
    parser.add_argument(
        "--env_note",
        type=str,
        help="Additional information stored in meta file. Use to note on what kind of machine the experiment was run.",
    )

    args = parser.parse_args()

    print(
        "\n\nInitialized question answering experiment with following configuration\n"
    )
    print(f"{"Title:":>20} {args.title}")

    graph = graph_service[args.graph]()
    print(f"{"Graph:":>20} {args.graph}")

    agent_factory = agent_provider[args.agent_provider]
    print(f"{"Agent Provider:":>20} {args.agent_provider}")
    print(f"{"Agent:":>20} {args.agent}")

    current_dir = os.path.dirname(__file__)
    root_dir = os.path.abspath(os.path.join(current_dir, ".."))
    q_path = os.path.join(root_dir, "questions", f"{args.questions}.json")
    with open(q_path) as f:
        questions = json.load(f)
    q_from = args.questions_from if args.questions_from is not None else 0
    q_to = args.questions_to if args.questions_to is not None else len(questions)
    questions = questions[q_from:q_to]
    print(f"{"Questions:":>20} {args.questions}")
    print(f"{"Question Range:":>20} {q_from} {q_to}")

    methods = [utils.get_configured_method(method) for method in args.methods]
    print(f"{"Methods:":>20} {args.methods}")

    reps = args.repetitions
    print(f"{"Repetitions:":>20} {args.repetitions}\n\n")

    experiment_dir = os.path.join(root_dir, "results", args.title)
    data_dir = os.path.join(experiment_dir, "raw_data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(experiment_dir, "meta.json"), "w", newline="") as f:
        json.dump(
            {
                "title": args.title,
                "experiment": "question answering",
                "methods": args.methods,
                "agent": args.agent,
                "provider": args.agent_provider,
                "graph": args.graph,
                "questions": args.questions,
                "q_range": [q_from, q_to],
                "repetitions": reps,
                "env_note": args.env_note,
                "timestamp": time.time(),
            },
            f,
            indent=4,
        )

    columns = [
        "question_index",
        "expected_answer",
        "answer",
        "has_err_instruction",
        "has_err_format",
        "has_err_graph",
        "has_err_other",
        "has_err_agent",
        "is_kg_based_answer",
        "kg_calls",
        "agent_calls",
        "reached_depth",
        "start_timestamp",
        "duration",
    ]

    total_iterations = reps * len(questions) * len(methods)
    # ---------------------------------------------------------------------------- #
    #                                  EXPERIMENT                                  #
    # ---------------------------------------------------------------------------- #
    with tqdm.tqdm(total=total_iterations) as progress:
        progress.set_postfix(
            {
                "Rep": f"{0}/{reps}",
                "Q": f"{0}/{len(questions)}",
                "Method": "",
            }
        )
        progress.update(0)
        for rep in range(reps):
            for q_index, q_dict in enumerate(questions):
                q_overall_index = q_from + q_index
                question_data = utils.map_question(args.questions, q_dict, graph)
                for method, execute, config, use_context, schema in methods:
                    q_dir = os.path.join(data_dir, method, "logs", str(q_overall_index))
                    os.makedirs(q_dir, exist_ok=True)

                    results_file = os.path.join(
                        data_dir, method, f"results_rep{rep+1}.csv"
                    )
                    file_exists = os.path.exists(results_file)
                    header_missing = False

                    if file_exists:
                        with open(results_file, "r", newline="") as f:
                            reader = csv.DictReader(f, fieldnames=columns)
                            last_row = None
                            for row in reader:
                                last_row = row
                            if last_row == None:
                                header_missing = True
                            last_question: str = last_row.get("question_index")
                            if last_question.isdigit():
                                if q_overall_index <= int(last_question):
                                    progress.set_postfix(
                                        {
                                            "Rep": f"{rep+1}/{reps}",
                                            "Q": f"{q_index+1}/{len(questions)}",
                                            "Method": method,
                                        }
                                    )
                                    progress.update(1)
                                    continue

                    if not file_exists or header_missing:
                        with open(results_file, "w", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=columns)
                            writer.writeheader()

                    agent = agent_factory(
                        model=args.agent,
                        instructions=config,
                        use_context=use_context,
                        response_schema=schema,
                        log_path=os.path.join(q_dir, f"history_{rep+1}.log"),
                    )
                    agent.flush_context()

                    # --------------------------------- EXECUTION -------------------------------- #
                    start_timestamp = time.time()
                    output = execute(
                        question_data["question"],
                        agent=agent,
                        graph=graph,
                        seed_entities=question_data["seed_entities"],
                        log_path=os.path.join(q_dir, f"method_{rep+1}.log"),
                    )
                    duration = time.time() - start_timestamp
                    # ---------------------------------------------------------------------------- #

                    result = {
                        "question_index": q_overall_index,
                        "expected_answer": question_data["answer"],
                        "answer": output["machine_answer"],
                        "is_kg_based_answer": output["is_kg_based_answer"],
                        "kg_calls": output["kg_calls"],
                        "agent_calls": output["agent_calls"],
                        "reached_depth": output["depth"],
                        "has_err_instruction": output["has_err_instruction"],
                        "has_err_format": output["has_err_format"],
                        "has_err_graph": output["has_err_graph"],
                        "has_err_other": output["has_err_other"],
                        "has_err_agent": output["has_err_agent"],
                        "start_timestamp": start_timestamp,
                        "duration": duration,
                    }

                    with open(results_file, "a", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writerow(result)

                    progress.set_postfix(
                        {
                            "Rep": f"{rep+1}/{reps}",
                            "Q": f"{q_index+1}/{len(questions)}",
                            "Method": method,
                        }
                    )
                    progress.update(1)

print("\nExperiment completed!\n")
