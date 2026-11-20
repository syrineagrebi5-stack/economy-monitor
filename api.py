
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from data import (
    get_gdp,
    get_inflation,
    get_unemployment,
    get_eurostoxx,
    get_vix
)

from scoring import calculate_scores, calculate_global_score


app = FastAPI(title="ECONOMY MONITOR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_WEIGHTS = {
    "Croissance du PIB": 25,
    "Inflation": 20,
    "Chômage": 20,
    "Euro Stoxx 50": 20,
    "VIX": 15
}


def dataframe_to_records(df):
    if df is None or df.empty:
        return []

    result = df.copy()
    result["Date"] = pd.to_datetime(
        result["Date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    result["Value"] = pd.to_numeric(
        result["Value"], errors="coerce"
    )

    result = result.dropna(subset=["Date", "Value"])

    return result[["Date", "Value"]].to_dict("records")


@app.get("/")
def home():
    return {
        "application": "ECONOMY MONITOR",
        "status": "API opérationnelle"
    }


@app.get("/api/data")
def get_dashboard_data():

    data = {
        "gdp": get_gdp(),
        "inflation": get_inflation(),
        "unemployment": get_unemployment(),
        "eurostoxx": get_eurostoxx(),
        "vix": get_vix()
    }

    scores = calculate_scores(data)

    global_score = calculate_global_score(
        scores,
        DEFAULT_WEIGHTS
    )

    histories = {
        "Croissance du PIB": dataframe_to_records(data["gdp"]),
        "Inflation": dataframe_to_records(data["inflation"]),
        "Chômage": dataframe_to_records(data["unemployment"]),
        "Euro Stoxx 50": dataframe_to_records(data["eurostoxx"]),
        "VIX": dataframe_to_records(data["vix"])
    }

    latest_values = {}

    for name, records in histories.items():
        if records:
            latest_values[name] = records[-1]

    return {
        "global_score": global_score,
        "scores": scores,
        "weights": DEFAULT_WEIGHTS,
        "latest_values": latest_values,
        "histories": histories
    }
