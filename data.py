
import yfinance as yf
import pandas as pd
import requests
import itertools


# ==========================================
# 1. DONNEES BOURSIERES : YAHOO FINANCE
# ==========================================

def get_market_data(ticker, period="5y"):
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

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.reset_index()
        data = data[["Date", "Close"]].dropna()
        data.columns = ["Date", "Value"]

        return data

    except Exception as error:
        print(f"Erreur Yahoo Finance ({ticker}): {error}")
        return None


def get_eurostoxx():
    return get_market_data("^STOXX50E")


def get_vix():
    return get_market_data("^VIX")


# ==========================================
# 2. RECUPERATION DES DONNEES EUROSTAT
# ==========================================

def get_eurostat_data(dataset, filters, start_period):
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
            if isinstance(values, dict):
                value = values.get(str(i))
            else:
                value = values[i] if i < len(values) else None

            if value is not None:
                row = dict(zip(dimensions, combination))
                row["Value"] = value
                rows.append(row)

        df = pd.DataFrame(rows)

        if df.empty:
            return None

        time_column = next(
            (col for col in df.columns if col.lower() == "time"),
            None
        )

        if time_column is None:
            return None

        # Conversion des dates trimestrielles et mensuelles
        dates = df[time_column].astype(str)

        if dates.str.contains("-Q").any():
            dates = dates.str.replace(
                r"(\d{4})-Q([1-4])",
                lambda m: f"{m.group(1)}-{(int(m.group(2))-1)*3+1:02d}-01",
                regex=True
            )

        df["Date"] = pd.to_datetime(dates, errors="coerce")
        df = df.dropna(subset=["Date"])
        df = df.sort_values("Date")

        return df[["Date", "Value"]].reset_index(drop=True)

    except Exception as error:
        print(f"Erreur Eurostat ({dataset}): {error}")
        return None


# ==========================================
# 3. CROISSANCE DU PIB
# ==========================================

def get_gdp():
    return get_eurostat_data(
        "namq_10_gdp",
        {
            "freq": "Q",
            "geo": "EA21",
            "unit": "CLV_PCH_PRE",
            "s_adj": "SCA",
            "na_item": "B1GQ"
        },
        "2021-Q1"
    )


# ==========================================
# 4. INFLATION
# ==========================================

def get_inflation():
    # Ancienne série : jusqu'en septembre 2025
    old = get_eurostat_data(
        "prc_hicp_manr",
        {
            "freq": "M",
            "geo": "EA",
            "unit": "RCH_A",
            "coicop": "CP00"
        },
        "2021-01"
    )

    # Nouvelle série : à partir d'octobre 2025
    new = get_eurostat_data(
        "prc_hicp_minr",
        {
            "freq": "M",
            "geo": "EA",
            "unit": "RCH_A",
            "coicop18": "TOTAL"
        },
        "2025-10"
    )

    if old is not None:
        old = old[old["Date"] < "2025-10-01"]

    if old is None and new is None:
        return None

    frames = [df for df in [old, new] if df is not None]

    return (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=["Date"], keep="last")
        .sort_values("Date")
        .reset_index(drop=True)
    )


# ==========================================
# 5. TAUX DE CHOMAGE
# ==========================================

def get_unemployment():
    return get_eurostat_data(
        "une_rt_m",
        {
            "freq": "M",
            "geo": "EA21",
            "s_adj": "SA",
            "age": "TOTAL",
            "sex": "T",
            "unit": "PC_ACT"
        },
        "2021-01"
    )
