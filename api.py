
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

from scoring import (
    calculate_scores,
    calculate_global_score,
    score_gdp,
    score_inflation,
    score_unemployment,
    score_eurostoxx,
    score_vix
)


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


def latest_value(df, date):
    if df is None or df.empty:
        return None

    history = df.copy()
    history["Date"] = pd.to_datetime(
        history["Date"], errors="coerce"
    )
    history["Value"] = pd.to_numeric(
        history["Value"], errors="coerce"
    )

    history = history.dropna(subset=["Date", "Value"])
    history = history[history["Date"] <= date]

    if history.empty:
        return None

    return float(history.sort_values("Date").iloc[-1]["Value"])


def calculate_historical_scores(data):
    valid_dates = []

    for df in data.values():
        if df is not None and not df.empty:
            dates = pd.to_datetime(df["Date"], errors="coerce").dropna()
            if not dates.empty:
                valid_dates.extend(dates.tolist())

    if not valid_dates:
        return []

    first_date = min(valid_dates)
    last_date = max(valid_dates)

    months = pd.date_range(
        start=first_date.to_period("M").to_timestamp(),
        end=last_date,
        freq="M"
    )

    history = []

    for date in months:
        values = {
            name: latest_value(df, date)
            for name, df in data.items()
        }

        scores = {}

        if values["gdp"] is not None:
            scores["Croissance du PIB"] = score_gdp(
                values["gdp"]
            )

        if values["inflation"] is not None:
            scores["Inflation"] = score_inflation(
                values["inflation"]
            )

        if values["unemployment"] is not None:
            scores["Chômage"] = score_unemployment(
                values["unemployment"]
            )

        if data["eurostoxx"] is not None:
            market_history = data["eurostoxx"].copy()
            market_history["Date"] = pd.to_datetime(
                market_history["Date"], errors="coerce"
            )
            market_history = market_history[
                market_history["Date"] <= date
            ]

            euro_score = score_eurostoxx(market_history)

            if euro_score is not None:
                scores["Euro Stoxx 50"] = euro_score

        if values["vix"] is not None:
            scores["VIX"] = score_vix(values["vix"])

        if scores:
            history.append({
                "Date": date.strftime("%Y-%m-%d"),
                "scores": scores
            })

    return history


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

    historical_scores = calculate_historical_scores(data)

    return {
        "global_score": global_score,
        "scores": scores,
        "weights": DEFAULT_WEIGHTS,
        "latest_values": latest_values,
        "histories": histories,
        "historical_scores": historical_scores
    }
