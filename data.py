
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
