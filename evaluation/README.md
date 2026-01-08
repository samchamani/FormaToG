# Experiment commands

Example for qald_10-en

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
