
import pandas as pd


# ==========================================
# 1. NORMALISATION DES INDICATEURS
# Tous les scores sont compris entre 0 et 100
# ==========================================

def normalize(value, minimum, maximum):
    """Score croissant : plus la valeur est élevée,
    meilleur est le score."""

    score = (value - minimum) / (maximum - minimum) * 100
    return max(0, min(100, score))


# ==========================================
# 2. SCORE DU PIB
# ==========================================

def score_gdp(value):
    # -2 % = score 0 ; +4 % = score 100
    return normalize(value, -2, 4)


# ==========================================
# 3. SCORE DE L'INFLATION
# ==========================================

def score_inflation(value):
    # Objectif de référence : 2 %
    # Plus on s'éloigne de cet objectif,
    # plus le score diminue.

    score = 100 - abs(value - 2) * 25
    return max(0, min(100, score))


# ==========================================
# 4. SCORE DU CHOMAGE
# ==========================================

def score_unemployment(value):
    # 3 % = score 100 ; 12 % = score 0
    return normalize(12 - value, 0, 9)


# ==========================================
# 5. SCORE EURO STOXX 50
# ==========================================

def score_eurostoxx(history):
    """
    Mesure la position du dernier niveau de l'indice
    dans sa distribution historique sur 5 ans.

    Ce score mesure une position relative,
    pas directement la performance économique.
    """

    values = pd.to_numeric(history["Value"], errors="coerce").dropna()

    if values.empty:
        return None

    latest = values.iloc[-1]

    return float((values <= latest).mean() * 100)


# ==========================================
# 6. SCORE DU VIX
# ==========================================

def score_vix(value):
    # VIX à 10 = score 100
    # VIX à 40 ou plus = score 0
    return normalize(40 - value, 0, 30)


# ==========================================
# 7. CALCUL DE TOUS LES SCORES
# ==========================================

def calculate_scores(data):

    scores = {}

    if data.get("gdp") is not None and not data["gdp"].empty:
        scores["Croissance du PIB"] = score_gdp(
            float(data["gdp"]["Value"].iloc[-1])
        )

    if data.get("inflation") is not None and not data["inflation"].empty:
        scores["Inflation"] = score_inflation(
            float(data["inflation"]["Value"].iloc[-1])
        )

    if data.get("unemployment") is not None and not data["unemployment"].empty:
        scores["Chômage"] = score_unemployment(
            float(data["unemployment"]["Value"].iloc[-1])
        )

    if data.get("eurostoxx") is not None and not data["eurostoxx"].empty:
        scores["Euro Stoxx 50"] = score_eurostoxx(
            data["eurostoxx"]
        )

    if data.get("vix") is not None and not data["vix"].empty:
        scores["VIX"] = score_vix(
            float(data["vix"]["Value"].iloc[-1])
        )

    return scores


# ==========================================
# 8. SCORE GLOBAL PERSONNALISE
# ==========================================

def calculate_global_score(scores, weights):

    active = {
        name: weight
        for name, weight in weights.items()
        if name in scores and weight > 0
    }

    if not active:
        return None

    total_weight = sum(active.values())

    global_score = sum(
        scores[name] * weight
        for name, weight in active.items()
    ) / total_weight

    return round(global_score, 2)
