.PHONY: rank validate test sandbox docker clean

CANDIDATES ?= ../candidates.jsonl
OUT        ?= submission.csv

# Produce the submission CSV (the single reproduction command).
rank:
	python rank.py --candidates $(CANDIDATES) --out $(OUT)

# Validate the CSV against the official challenge validator.
validate:
	python ../validate_submission.py $(OUT)

# Run the pipeline tests (format validity, honeypot gate, determinism).
test:
	python tests/test_pipeline.py

# Launch the interactive demo locally.
sandbox:
	pip install -r requirements-sandbox.txt && streamlit run sandbox/app.py

# Reproduce inside Docker exactly as Stage-3 will (no network).
docker:
	docker build -t redrob-ranker . && \
	docker run --rm --network none -v "$$PWD/..":/data redrob-ranker \
	  python rank.py --candidates /data/candidates.jsonl --out /data/submission.csv

clean:
	rm -f submission.csv
