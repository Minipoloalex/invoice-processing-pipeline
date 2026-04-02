# Guidelines of how to run the project
Use 2 terminals, one to run the backend API and the other to run the dashboard.

## Running the backend API
```bash
uv run uvicorn main:app --reload
```

The `--reload` flag is used during development for hot-reloading.

## Running the dashboard

```bash
uv run streamlit run dashboard.py
```
