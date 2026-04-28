# City Permit Search App

A Streamlit app that helps search for permit submissions in Salem and nearby Oregon cities:

- Salem
- Aumsville
- Turner
- Silverton
- Keizer
- Brooks
- McMinnville
- Woodburn
- Albany
- Corvallis
- Monmouth
- Independence
- Stayton

## What it does

- Runs a city-by-city web search focused on permit-related pages.
- Scores likely matches so you can prioritize the best leads.
- Lets you export results to CSV.
- Generates one-click search links per city.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

This app searches publicly indexed pages. Some city permit records live in systems that are not indexed by search engines, so always verify results against official city permit portals.
