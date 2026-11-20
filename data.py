
import yfinance as yf
import pandas as pd


def get_market_data(ticker, period="5y"):
    """
    Récupère l'historique d'un indice financier
    depuis Yahoo Finance.
    """

    try:
        data = yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if data.empty:
            return None

        # Gestion des éventuelles colonnes multi-index
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.reset_index()

        data = data[["Date", "Close"]].dropna()

        data.columns = ["Date", "Value"]

        return data

    except Exception as error:
        print(f"Erreur de récupération pour {ticker}: {error}")
        return None


def get_eurostoxx():
    return get_market_data("^STOXX50E")


def get_vix():
    return get_market_data("^VIX")

import itertools
import requests


def get_eurostat_data(dataset, filters, start_period):
    """
    Récupère et décode les données Eurostat au format JSON-stat.
    """

    url = (
        "https://ec.europa.eu/eurostat/api/"
        "dissemination/statistics/1.0/data/"
        + dataset
    )

    params = {
        "lang": "en",
        "format": "JSON",
        **filters,
        "sinceTimePeriod": start_period
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        body = response.json()

        dimensions = body["id"]
        categories = []

        for dimension in dimensions:
            index = body["dimension"][dimension]["category"]["index"]
            ordered = [None] * len(index)

            for code, position in index.items():
                ordered[position] = code

            categories.append(ordered)

        rows = []
        values = body.get("value", {})

        for i, combination in enumerate(
            itertools.product(*categories)
        ):
            value = values.get(str(i))

            if value is not None:
                row = dict(zip(dimensions, combination))
                row["Value"] = value
                rows.append(row)

        df = pd.DataFrame(rows)

        if df.empty:
            return None

        time_column = "time" if "time" in df.columns else "TIME_PERIOD"

        df["Date"] = pd.to_datetime(
            df[time_column].astype(str).str.replace(
                r"-(\d)$", r"-0\1", regex=True
            ),
            errors="coerce"
        )

        df = df.dropna(subset=["Date"])
        df = df.sort_values("Date")

        return df[["Date", "Value"]].reset_index(drop=True)

    except Exception as error:
        print(f"Erreur Eurostat ({dataset}): {error}")
        return None


def get_gdp():
    return get_eurostat_data(
        "namq_10_gdp",
        {
            "geo": "EA21",
            "unit": "CLV_PCH_PRE",
            "s_adj": "SCA",
            "na_item": "B1GQ"
        },
        "2021-Q1"
    )


def get_inflation():
    return get_eurostat_data(
        "prc_hicp_minr",
        {
            "geo": "EA21",
            "unit": "RCH_A",
            "coicop18": "TOTAL"
        },
        "2021-01"
    )


def get_unemployment():
    return get_eurostat_data(
        "une_rt_m",
        {
            "geo": "EA21",
            "s_adj": "SA",
            "age": "TOTAL",
            "sex": "T",
            "unit": "PC_ACT"
        },
        "2021-01"
    )
