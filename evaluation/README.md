# Example command for `qald_10-en`

```
python -m evaluation.question_answering \
    --title test \
    --agent_provider ollama \
    --agent llama3.2:3b-instruct-fp16 \
    --graph wikidata \
    --questions qald_10-en \
    --questions_from 10 --questions_to 12 \
    --methods formatog_d3_p3 formatog_noctx_d3_p3 tog_d3_p3 cot io_zero_shot io_few_shot \
    --repetitions 2 \
    --env_note "Test run on local environment"
```

# Evaluation pipeline

1. Run experiment
   1. with jobs on hpc cluster (see [evaluations/hpc](./hpc/README.md))
   2. or directly with `question_answering.py` as shown above
2. If an experiment was run with several jobs running on the cluster, you need to merge the results with `merge_experiments.py`
3. Result files are still spread across method directories. To bring the results into one file and calculate metrics such as F1 and exact match for each trial, run `preprocess.py`
4. `analyze.py` will then calculate the metrics on experiment level
5. Finally `visualize.py` will output figures and relevant tables
