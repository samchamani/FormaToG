# How to run the evaluation on TU Berlin's HPC cluster

1. Get access by being added to a team
2. Set up TUB's VPN and activate it
3. Move this project to the home directory

   ```
   export HPC_USER=your-user-name
   export REPO_PARENT_DIR=/path/to/workspace
   rsync -av --delete \
   --exclude='.git' \
   --exclude='.venv' \
   --exclude='__pycache__' \
   --exclude='*.pyc' \
   --exclude='results' \
   --exclude='.env' \
   --exclude-'.DS_Store' \
   $REPO_PARENT_DIR/FormaToG \
   $HPC_USER@gateway.hpc.tu-berlin.de:~/
   ```

4. Access the cluster's frontend node
   ```
   ssh $HPC_USER@gateway.hpc.tu-berlin.de
   ```
5. Get a computing node to run scripts on
   ```
   srun --partition=standard --time=02:00:00 --mem=8G --pty bash
   ```
6. Go through these setup steps

   1. Set up environment variables and directories
      ```
      echo 'export SCRATCH_DIR=/scratch/$USER' >> ~/.bashrc
      echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
      echo 'export OLLAMA_MODELS=$SCRATCH_DIR/ollama_models' >> ~/.bashrc
      echo 'export SINGULARITY_CACHEDIR=$SCRATCH_DIR/.cache' >> ~/.bashrc
      source ~/.bashrc
      mkdir -p $SCRATCH_DIR/.cache $SCRATCH_DIR/ollama_models $SCRATCH_DIR/neo4j_data ~/logs
      ```
   2. Download and install miniconda, then create environment with needed python version
      ```
      cd $SCRATCH_DIR
      wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      bash Miniconda3-latest-Linux-x86_64.sh -b -p $SCRATCH_DIR/miniconda
      cd ~
      source $SCRATCH_DIR/miniconda/bin/activate
      conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
      conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
      conda create -n venv python=3.12.7 -y
      conda activate venv
      ```
   3. Move to repository and install dependencies
      ```
      cd ~/FormaToG
      pip install -r ./requirements.txt
      ```
   4. Set up Ollama
      ```
      cd ~
      wget -O ~/ollama.tgz https://ollama.com/download/ollama-linux-amd64.tgz
      tar -xzf ~/ollama.tgz
      chmod +x ~/bin/ollama
      rm -rf ~/ollama.tgz
      ```
   5. Run Ollama in the background, then download models (adjust to try out other models!)
      ```
      ollama serve > ~/logs/ollama_pull.log 2>&1 &
      OLLAMA_PID=$!
      ollama pull llama3.1:8b # Size 4.9GB / 128K Context length / Input: Text / 8b params
      ollama pull llama4:scout # Size 67GB / 10M Context length / Input: Text, Image / 109b=16x17b params (16 experts)
      sleep 5
      kill $OLLAMA_PID
      ```
   6. Load neo4j image and convert it to sif file
      ```
      module load singularity
      singularity pull $SCRATCH_DIR/neo4j.sif docker://neo4j:5.28.2
      ```
   7. Finally, `exit` the computing node to get back to the frontend node.

7. Run sbatch scripts from the **frontend node** to run slurm jobs (Find more examples in `results/[exp]/hpc_command.txt`)

   ```
   (
   export QUESTIONS="lndw25"
   export QUESTIONS_BATCH_LENGTH=10
   export MODEL="llama3.1:8b"
   export GRAPH="neo4j"
   export METHODS="formatog_d3_p3 formatog_noctx_d3_p3 tog_d3_p3 cot io_zero_shot io_few_shot"
   sbatch \
   --job-name=slm_on_lndw25 \
   --array=0-9 \
   --partition=gpu \
   --gres=gpu:1 \
   --mem=60G \
   --cpus-per-task=4 \
   --time=02:00:00 \
   --export=ALL \
   ~/FormaToG/evaluation/hpc/job.sbatch
   )
   ```

8. Wait for completion
9. Fetch results back into your local machine

   ```
   export HPC_USER=your-user-name
   export OUTPUT_DIR=/path/to/
   rsync -avzP $HPC_USER@gateway.hpc.tu-berlin.de:~/FormaToG/results $OUTPUT_DIR
   ```

10. Before running the next experiment:

    1. Check the logs for canceled jobs, highly frequent truncated prompts, or other suspicious things. You might need to run (parts of) the experiment again.
    2. Whipe the data on hpc node, to make sure it doesn't interfer with the next experiment

       ```
       rm -rf ~/FormaToG/results/*
       ```

11. If you are done using the HPC cluster cleanup your home directory and scratch directory.
