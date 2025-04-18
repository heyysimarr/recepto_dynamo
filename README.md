# NLP Recepto - Team Dynamo Setup

## Installation Instructions
1. Setup the .env file with:
```bash
API_KEY=
DATASET_ID=
BASE=

PROXY=

AZURE_ENDPOINT=
AZURE_API_KEY=

```

2. Place the testing file at:
   ```
   dataset/test.json
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   make run
   ```

## Results
The confidence scores will be available at:
```
temp/confidence_scores.csv
```
