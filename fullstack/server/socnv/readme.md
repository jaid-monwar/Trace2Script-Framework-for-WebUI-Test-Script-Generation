```bash

python sconv.py parse --input agent_history.json --output parse.json

python sconv.py refine --input parse.json --output refine.json

python sconv.py generate --input refine.json --output script.py

```