#!/bin/bash
#SBATCH --output=logs/%x_%a.out

# --------------------- Add these here with --export=ALL --------------------- #
: "${QUESTIONS:?Error: You must provide a QUESTIONS dataset name.}"
: "${QUESTIONS_BATCH_LENGTH:?Error: You must provide the QUESTIONS_BATCH_LENGTH.}"
: "${MODEL:?Error: You must provide a MODEL name.}"
: "${GRAPH:?Error: You must provide a GRAPH name.}"
: "${METHODS:?Error: You must provide a list of METHODS.}"
# ---------------------------------------------------------------------------- #

Q_FROM=$(( QUESTIONS_BATCH_LENGTH * SLURM_ARRAY_TASK_ID ))
Q_TO=$(( Q_FROM + QUESTIONS_BATCH_LENGTH ))
OFFSET=$((SLURM_ARRAY_TASK_ID * 10))
export OLLAMA_PORT=$((15000 + OFFSET))
export OLLAMA_HOST="127.0.0.1:$OLLAMA_PORT"
export OLLAMA_CONTEXT_LENGTH=32768
export GRAPH_HTTP_PORT=$((25000 + OFFSET))
export GRAPH_BOLT_PORT=$((26000 + OFFSET))
export GRAPH_USERNAME="neo4j"
export GRAPH_PASSWORD="password"
DATA_DIR="$SCRATCH_DIR/neo4j_data/job_${SLURM_JOB_NAME}_${SLURM_ARRAY_TASK_ID}"
REPO_DIR="$HOME/FormaToG"
export GRAPH_IMPORT_VOL="$REPO_DIR/use_case"
export GRAPH_URL="https://query.wikidata.org/sparql"

echo "----------------------------------------------------------------"
echo "Job: $SLURM_JOB_NAME"
echo "Job ID: $SLURM_JOB_ID | Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $(hostname)"
echo "Ollama Port: $OLLAMA_PORT"
echo "Neo4j Ports: HTTP=$GRAPH_HTTP_PORT, Bolt=$GRAPH_BOLT_PORT"
echo "----------------------------------------------------------------"

set -e

echo "Activating environment"
source $SCRATCH_DIR/miniconda/bin/activate
conda activate venv

if [ "$GRAPH" == "neo4j" ]; then
    mkdir -p "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/plugins" "$DATA_DIR/conf"
    module load singularity
    echo "Starting Neo4j..."
    singularity run \
        --env NEO4J_AUTH=${GRAPH_USERNAME}/${GRAPH_PASSWORD} \
        --env NEO4J_server_default__listen__address=0.0.0.0 \
        --env NEO4J_server_http_listen__address=:${GRAPH_HTTP_PORT} \
        --env NEO4J_server_bolt_listen__address=:${GRAPH_BOLT_PORT} \
        --env NEO4J_PLUGINS='["apoc"]' \
        --env NEO4J_dbms_security_procedures_unrestricted="apoc.*" \
        --env NEO4J_apoc_import_file_enabled=true \
        --env NEO4J_apoc_export_file_enabled=true \
        --env NEO4J_apoc_import_file_use__neo4j__config=true \
        --bind "$DATA_DIR/data:/data" \
        --bind "$DATA_DIR/logs:/logs" \
        --bind "$DATA_DIR/plugins:/plugins" \
        --bind "$DATA_DIR/conf:/var/lib/neo4j/conf" \
        --bind "$GRAPH_IMPORT_VOL:/import" \
        --bind $HOME/neo4j/conf:/var/lib/neo4j/conf \
        "$SCRATCH_DIR/neo4j.sif" > "$HOME/logs/neo4j_${SLURM_JOB_NAME}_${SLURM_ARRAY_TASK_ID}.log" 2>&1 &
    NEO4J_PID=$!
    echo "Waiting for Neo4j..."
    cd $REPO_DIR
    python -m evaluation.hpc.check --url "http://localhost:${GRAPH_HTTP_PORT}" --timeout 600
    echo "Importing graph..."
    python -m use_case.generate_graph
fi

module load nvidia/cuda/12.2
module load nvidia/cudnn/9.0.0_cuda12
echo "Starting Ollama..."
ollama serve > "$HOME/logs/ollama_${SLURM_JOB_NAME}_${SLURM_ARRAY_TASK_ID}.log" 2>&1 &
OLLAMA_PID=$!
echo "Waiting for Ollama..."
cd $REPO_DIR
python -m evaluation.hpc.check --url "http://${OLLAMA_HOST}"

echo "Starting experiment..."
python -m evaluation.question_answering \
    --title "${SLURM_JOB_NAME}-${Q_FROM}-${Q_TO}" \
    --agent_provider ollama \
    --agent $MODEL \
    --graph $GRAPH \
    --questions $QUESTIONS \
    --questions_from $Q_FROM --questions_to $Q_TO \
    --methods $METHODS \
    --env_note "$(scontrol show node $HOSTNAME)"

echo "Stopping services..."
if [ "$GRAPH" == "neo4j" ]; then
    if ps -p $NEO4J_PID > /dev/null; then kill $NEO4J_PID; fi
fi
if ps -p $OLLAMA_PID > /dev/null; then kill $OLLAMA_PID; fi
echo "Job completed"