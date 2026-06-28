# Reproduces the ranking step exactly as Stage-3 will run it.
# CPU-only, no network needed at run time. Build then run:
#
#   docker build -t redrob-ranker .
#   docker run --rm --network none -v "$PWD":/data redrob-ranker \
#       python rank.py --candidates /data/candidates.jsonl --out /data/submission.csv
#
# The engine has no third-party dependencies, so this image is tiny and the run
# is fully deterministic.
FROM python:3.11-slim

WORKDIR /app
COPY src/ ./src/
COPY rank.py ./rank.py

ENV PYTHONHASHSEED=0
ENTRYPOINT ["python", "rank.py"]
CMD ["--candidates", "/data/candidates.jsonl", "--out", "/data/submission.csv"]
