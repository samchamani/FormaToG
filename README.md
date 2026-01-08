# FormaToG

.env file in project root dir

```
NEO4J_HOST=localhost
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=test
NEO4J_BOLT_PORT=7687
NEO4J_HTTP_PORT=7474
```

Run neo4j database for KG in docker container

```
docker compose up -d
```

check knowledge graph with your browser

```
http://localhost:7474/browser/
```

Run ollama

```
ollama start
# or ollama serve
```

Run Think-on-Graph

```
python run.py --prompt "Your question" --agent llama3.1:8b-instruct-q6_K
```

## Local setup

```
conda create -n formatog python=3.12.7
conda activate formatog
pip install -r requirements.txt
```

Python versions tested: Python 3.12.7
