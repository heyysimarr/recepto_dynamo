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
   python get_input.py
	python gather_links/sele_google.py temp/input.json temp/google_links.json
	python gather_links/sele_ddg.py temp/input.json temp/ddg_links.json
	python transform.py
	python gather_linkedin_info/sele_linkedin_BD.py temp/merged_links.json temp/all_linkedin_profiles.json
   python get_similarity.py
	python get_final_rankings.py
	python confidence_scores.py	
   ```

## Results
The confidence scores will be available at:
```
temp/confidence_scores.csv
```
