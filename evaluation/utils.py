from methods.prompting import ask
from methods.formatog import think_on_graph as formatog
from methods.tog import think_on_graph as tog
from methods.instructions.cot import config as cot_config, schema as cot_schema
from methods.instructions.io_few_shot import (
    config as io_few_shot_config,
    schema as io_fs_schema,
)
from methods.instructions.io_zero_shot import (
    config as io_zero_shot_config,
    schema as io_zs_schema,
)
from methods.instructions.formatog import (
    config as formatog_config,
    schema as formatog_schema,
)
from methods.instructions.tog import config as tog_config
from graphs.Graph import Graph
import re
from pathlib import Path
import string
import argparse
import os


# ---------------------------------------------------------------------------- #
#                              QUESTION ANSWERING                              #
# ---------------------------------------------------------------------------- #
def get_configured_method(method: str):
    """Returns the method with all configured settings.
    ```
    name, function, instruction_config, use_context = get_configured_method("some_method")
    ```
    """
    result = (method, get_method_exec(method)) + get_config_and_use_context(method)
    return result


def get_method_exec(method: str):
    simple_methods = {
        "cot": lambda prompt, **kwargs: ask(prompt, with_reason=True, **kwargs),
        "io_few_shot": lambda prompt, **kwargs: ask(
            prompt, with_reason=False, **kwargs
        ),
        "io_zero_shot": lambda prompt, **kwargs: ask(
            prompt, with_reason=False, **kwargs
        ),
    }

    if method in simple_methods:
        return simple_methods[method]

    if re.fullmatch(r"_d[0-9]+_p[0-9]+$", method):
        parts = method.split("_")
        max_paths = int(parts[-1].removeprefix("p"))
        max_depth = int(parts[-2].removeprefix("d"))

        tog_methods = {
            "tog": lambda prompt, **kwargs: tog(
                prompt, max_depth=max_depth, max_paths=max_paths, **kwargs
            ),
            "formatog": lambda prompt, **kwargs: formatog(
                prompt, max_depth=max_depth, max_paths=max_paths, **kwargs
            ),
            "formatog_noctx": lambda prompt, **kwargs: formatog(
                prompt, max_depth=max_depth, max_paths=max_paths, **kwargs
            ),
        }
        method_no_params = re.sub(r"_d[0-9]+_p[0-9]+$", "", method)
        if method_no_params in tog_methods:
            return tog_methods[method_no_params]
    raise ValueError(f"Unknown method: {method}")


def get_config_and_use_context(method_with_params: str):
    method = re.sub(r"_d[0-9]+_p[0-9]+$", "", method_with_params)
    methods = {
        "cot": (cot_config, False, cot_schema),
        "io_few_shot": (io_few_shot_config, False, io_fs_schema),
        "io_zero_shot": (io_zero_shot_config, False, io_zs_schema),
        "formatog": (formatog_config, True, formatog_schema),
        "formatog_noctx": (formatog_config, False, formatog_schema),
        "tog": (tog_config, False, None),
    }

    if method in methods:
        return methods[method]

    raise ValueError(f"Unknown method: {method}")


def map_question(catalogue: str, question_dict: dict, graph: Graph):
    if catalogue == "cwq":
        return {
            "question": question_dict["question"],
            "answer": question_dict["answer"],
            "seed_entities": graph.get_entities(
                [key for key in list(question_dict["qid_topic_entity"].keys())]
            ),
        }
    if catalogue == "qald_10-en":
        return {
            "question": question_dict["question"],
            "answer": "; ".join(
                [val for val in list(question_dict["answer"].values())]
            ),
            "seed_entities": graph.get_entities(
                [key for key in list(question_dict["qid_topic_entity"].keys())]
            ),
        }

    if catalogue == "lndw25":
        return {
            "question": question_dict["question"],
            "answer": question_dict["answer"],
            "seed_entities": graph.get_entities(question_dict["seed_entities"]),
        }

    return question_dict


# ---------------------------------------------------------------------------- #
#                                    ANALYZE                                   #
# ---------------------------------------------------------------------------- #
DATA_TYPE_MAP = {
    "question_index": int,
    "expected_answer": str,
    "answer": str,
    "is_kg_based_answer": int,
    "has_err_instruction": int,
    "has_err_format": int,
    "has_err_graph": int,
    "has_err_other": int,
    "has_err_agent": int,
}


def get_exp_and_dir_from_arg():
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
    return exp_name, exp_dir


def extract_meta_from_result_path(path: str):
    """For an expected result file path, the repetition number and method name
    are extracted and returned as `(method, rep)`"""
    parts = Path(path).parts
    return parts[-2], int(parts[-1].replace(".csv", "").replace("results_rep", ""))


def normalize_answer(s: str):
    """Normalization according to SQUAD.
    Additions: German articles
    """
    # text to lowercase letters
    s = s.lower()

    # excluding punctuation
    exclude = set(string.punctuation)
    s = "".join(ch for ch in s if ch not in exclude)

    # articles removed
    regex = re.compile(
        r"\b(a|an|the|der|die|das|den|dem|des|ein|eine|einen|einem|einer|eines)\b",
        re.UNICODE,
    )
    s = re.sub(regex, " ", s)

    # normalized white spaces, new lines, ...
    s = " ".join(s.split())

    return s


def get_tokens(s: str):
    """Tokenization according to SQUAD."""
    if not s:
        return []
    return normalize_answer(s).split()
