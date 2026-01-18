(
export QUESTIONS="qald_10-en"
export QUESTIONS_BATCH_LENGTH=333
export MODEL="llama4:scout"
export GRAPH="wikidata"
export GRAPH_USER_AGENT="FormaToG/1.0 (https://samchamani.com; contact@samchamani.com)"
export METHODS="formatog_d3_p3 formatog_noctx_d3_p3 tog_d3_p3 cot io_simple"
sbatch \
 --job-name=elm_on_qald \
 --array=0-0 \
 --partition=scioi_gpu \
 --constraint=tesla_a10080G \
 --gres=gpu:a100:1 \
 --mem=60G \
 --cpus-per-task=4 \
 --time=1-20:00:00 \
 --export=ALL \
 ~/FormaToG/evaluation/hpc/job.sbatch
)
