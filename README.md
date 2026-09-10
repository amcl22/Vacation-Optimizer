
# AI Vacation Destination Optimizer

A deploy-ready Streamlit dashboard for an MBA AI project.

## What it does
Users enter:
- travel dates
- total budget
- preferred maximum travel time
- preferred temperature range
- importance of nature, food, history, nightlife, and beaches

The model:
1. estimates total trip cost for each destination
2. converts raw factors into 0–100 scores
3. calculates a weighted overall destination score
4. ranks destinations
5. explains why a destination did or did not rank highly

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Put it online for classmates

### Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, and the `data` folder.
3. Sign in to Streamlit Community Cloud with GitHub.
4. Choose **Create app**.
5. Select your repository and set the main file path to `app.py`.
6. Deploy.
7. Share the generated URL.

## Current data strategy
The included version intentionally uses a curated demo dataset, which makes the project:
- reproducible
- easy to grade
- free to run
- independent of API keys

The airfare values are sample values, not live quotes. Seasonal weather and destination attributes are prototype values.

## Recommended production extensions
- Amadeus API: live airfare / itinerary information
- Open-Meteo API: historical or forecast weather
- Google Places API: attractions and destination characteristics
- LLM API: richer personalized explanations and follow-up Q&A

## Model weights
- Interest fit: 35%
- Budget fit: 25%
- Historical weather fit: 15%
- Flight price fit: 15%
- Travel time fit: 10%

These can easily be exposed as additional user-adjustable sliders if desired.
