(
export QUESTIONS="cwq"
export QUESTIONS_BATCH_LENGTH=71
export MODEL="llama3.1:8b"
export GRAPH="wikidata"
export METHODS="formatog_d3_p3 formatog_noctx_d3_p3 tog_d3_p3 cot io_simple"
export GRAPH_USER_AGENT="FormaToG/1.0 (https://samchamani.com; contact@samchamani.com)"
sbatch \
 --job-name=slm_on_cwq \
 --array=0-49 \
 --partition=gpu \
 --gres=gpu:1 \
 --mem=60G \
 --cpus-per-task=4 \
 --time=10:00:00 \
 --export=ALL \
 ~/FormaToG/evaluation/hpc/job.sbatch
)