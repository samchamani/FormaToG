# Experiment commands

Run on cwq

```
python -m evaluation.question_answering \
    --title test \
    --agent_provider ollama \
    --agent llama3.2:3b-instruct-fp16 \
    --graph wikidata \
    --questions cwq \
    --methods tog_d3_p3 tog_no_context_d3_p3 tog_sunetal_d3_p3 cot zero_shot few_shot \
    --repetitions 5
```

Remove aggregation questions?
Likely more relevant in R
aggregated_metrics = ["F1","Hits@1","error_rate","graph_based_answer_rate vs graph_based_correct_answer_rate","avg_LLM_calls","avg_KG_calls",
]

Performance with higher depth / width ?

## Experiment 1

```
python -m evaluation.question_answering \
    --title exp1_20251204 \
    --agent llama3.2:3b-instruct-fp16 \
    --graph wikidata \
    --questions qald_10-en \
    --methods tog_d3_p3 tog_sunetal_d3_p3 cot io_zero_shot io_few_shot \
    --repetitions 5
```

```
 Rscript analyze.R /path/to/results/exp1_20251204
```
