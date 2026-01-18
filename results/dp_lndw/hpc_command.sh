(
    export QUESTIONS="lndw25"
    export QUESTIONS_BATCH_LENGTH=5
    export MODEL="llama3.1:8b"
    export GRAPH="neo4j"
    export METHODS="formatog_d1_p1 formatog_d2_p1 formatog_d3_p1 formatog_d4_p1 formatog_d1_p2 formatog_d2_p2 formatog_d3_p2 formatog_d4_p2 formatog_d1_p3 formatog_d2_p3 formatog_d3_p3 formatog_d4_p3 formatog_d1_p4 formatog_d2_p4 formatog_d3_p4 formatog_d4_p4"
    sbatch \
        --job-name=dp_lndw \
        --array=0-19 \
        --partition=gpu \
        --gres=gpu:1 \
        --mem=60G \
        --cpus-per-task=4 \
        --time=05:00:00 \
        --export=ALL \
        ~/FormaToG/evaluation/hpc/job.sbatch
)