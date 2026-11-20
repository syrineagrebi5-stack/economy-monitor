
const API_URL = "http://127.0.0.1:8000/api/data";

const indicators = [
    {
        name: "Croissance du PIB",
        key: "Croissance du PIB",
        weight: 25,
        description: "Croissance économique"
    },
    {
        name: "Inflation",
        key: "Inflation",
        weight: 20,
        description: "Évolution des prix"
    },
    {
        name: "Chômage",
        key: "Chômage",
        weight: 20,
        description: "Marché du travail"
    },
    {
        name: "Euro Stoxx 50",
        key: "Euro Stoxx 50",
        weight: 20,
        description: "Marchés actions"
    },
    {
        name: "VIX",
        key: "VIX",
        weight: 15,
        description: "Volatilité financière"
    }
];

let dashboardData = null;

let activeIndicators = {
    "Croissance du PIB": true,
    "Inflation": true,
    "Chômage": true,
    "Euro Stoxx 50": true,
    "VIX": true
};

let weights = {};

indicators.forEach(indicator => {
    weights[indicator.key] = indicator.weight;
});

async function loadData() {
    const status = document.getElementById("global-status");
    status.textContent = "Récupération des données...";

    try {
        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Erreur API");
        }

        dashboardData = await response.json();

        renderDashboard();
        status.textContent = "Données actualisées avec succès.";

    } catch (error) {
        status.textContent =
            "Impossible de récupérer les données. Vérifiez que l'API est démarrée.";

        console.error(error);
    }
}

function calculateGlobalScore() {
    if (!dashboardData) return null;

    let totalWeight = 0;
    let totalScore = 0;
    const activeScores = dashboardData.scores;

    indicators.forEach(indicator => {
        const name = indicator.key;

        if (
            activeIndicators[name] &&
            activeScores[name] !== undefined &&
            activeScores[name] !== null &&
            weights[name] > 0
        ) {
            totalScore += activeScores[name] * weights[name];
            totalWeight += weights[name];
        }
    });

    if (totalWeight === 0) return null;

    return totalScore / totalWeight;
}

function getEffectiveWeights() {
    const total = indicators.reduce((sum, indicator) => {
        const name = indicator.key;

        if (
            activeIndicators[name] &&
            dashboardData.scores[name] !== undefined &&
            weights[name] > 0
        ) {
            return sum + weights[name];
        }

        return sum;
    }, 0);

    const result = {};

    indicators.forEach(indicator => {
        const name = indicator.key;

        result[name] =
            total > 0 && activeIndicators[name]
                ? weights[name] / total * 100
                : 0;
    });

    return result;
}

function getLatestValue(name) {
    const record = dashboardData.latest_values[name];

    if (!record) return "Indisponible";

    return record.Value.toLocaleString("fr-FR", {
        maximumFractionDigits: 2
    });
}

function getScoreColor(score) {
    if (score >= 70) return "#16865B";
    if (score >= 40) return "#D28A21";
    return "#C74747";
}

function renderIndicators() {
    const container = document.getElementById("indicators");
    container.innerHTML = "";

    const effectiveWeights = getEffectiveWeights();

    indicators.forEach(indicator => {
        const name = indicator.key;
        const score = dashboardData.scores[name];

        if (score === undefined || score === null) return;

        const enabled = activeIndicators[name];

        const card = document.createElement("div");
        card.className = "indicator-card";

        card.style.opacity = enabled ? "1" : "0.5";

        card.innerHTML = `
            <div class="indicator-top">
                <h3>${indicator.name}</h3>
                <input
                    type="checkbox"
                    ${enabled ? "checked" : ""}
                    aria-label="Activer ${indicator.name}"
                    data-toggle="${name}"
                >
            </div>

            <div class="indicator-value">
                ${getLatestValue(name)}
            </div>

            <div class="indicator-date">
                ${indicator.description}
            </div>

            <div class="score-line">
                <span>Score individuel</span>
                <strong>${score.toFixed(1)}/100</strong>
            </div>

            <div class="progress">
                <div
                    class="progress-fill"
                    style="width:${score}%; background:${getScoreColor(score)}"
                ></div>
            </div>

            <div class="weight-control">
                <label>
                    <span>Pondération</span>
                    <strong>${weights[name]}%</strong>
                </label>

                <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value="${weights[name]}"
                    data-weight="${name}"
                    ${enabled ? "" : "disabled"}
                >

                <small>
                    Poids effectif : ${effectiveWeights[name].toFixed(1)}%
                </small>
            </div>
        `;

        container.appendChild(card);
    });

    container.querySelectorAll("[data-toggle]").forEach(input => {
        input.addEventListener("change", event => {
            activeIndicators[event.target.dataset.toggle] =
                event.target.checked;

            renderDashboard();
        });
    });

    container.querySelectorAll("[data-weight]").forEach(input => {
        input.addEventListener("input", event => {
            weights[event.target.dataset.weight] =
                Number(event.target.value);

            renderDashboard();
        });
    });
}

function renderGlobalScore() {
    const score = calculateGlobalScore();

    document.getElementById("global-score").textContent =
        score === null ? "--" : score.toFixed(1);

    const status = document.getElementById("global-status");

    if (score === null) {
        status.textContent = "Aucun indicateur actif";
    } else if (score >= 70) {
        status.textContent = "Situation favorable";
    } else if (score >= 40) {
        status.textContent = "Situation intermédiaire";
    } else {
        status.textContent = "Situation dégradée";
    }

    const count = indicators.filter(indicator =>
        activeIndicators[indicator.key] &&
        dashboardData.scores[indicator.key] !== undefined
    ).length;

    document.getElementById("active-count").textContent =
        `${count} indicateur(s) actif(s)`;
}

function renderContributionChart() {
    const effectiveWeights = getEffectiveWeights();

    const names = [];
    const contributions = [];

    indicators.forEach(indicator => {
        const name = indicator.key;
        const score = dashboardData.scores[name];

        if (
            activeIndicators[name] &&
            score !== undefined &&
            effectiveWeights[name] > 0
        ) {
            names.push(name);
            contributions.push(
                score * effectiveWeights[name] / 100
            );
        }
    });

    Plotly.newPlot("contribution-chart", [{
        x: names,
        y: contributions,
        type: "bar",
        marker: { color: "#2563EB" },
        text: contributions.map(value => value.toFixed(2)),
        textposition: "outside"
    }], {
        margin: { t: 25, b: 90, l: 50, r: 20 },
        yaxis: {
            title: "Points apportés au score global",
            rangemode: "tozero"
        },
        xaxis: { automargin: true },
        paper_bgcolor: "white",
        plot_bgcolor: "white"
    }, {
        responsive: true,
        displayModeBar: false
    });
}


function renderHistoryChart() {
    const name = document.getElementById("history-indicator").value;
    const period = document.getElementById("history-period").value;

    const allRecords = dashboardData.histories[name] || [];

    let records = [...allRecords];

    if (period !== "all" && records.length > 0) {
        // On prend comme référence la date de la dernière donnée disponible
        const lastDate = new Date(records[records.length - 1].Date);

        const startDate = new Date(lastDate);
        startDate.setFullYear(
            startDate.getFullYear() - Number(period)
        );

        records = records.filter(item =>
            new Date(item.Date) >= startDate
        );
    }

    Plotly.newPlot("history-chart", [{
        x: records.map(item => item.Date),
        y: records.map(item => item.Value),
        type: "scatter",
        mode: "lines",
        line: { color: "#2563EB", width: 2 },
        name: name
    }], {
        margin: { t: 25, b: 55, l: 55, r: 20 },
        xaxis: { title: "Date" },
        yaxis: { title: name, automargin: true },
        paper_bgcolor: "white",
        plot_bgcolor: "white"
    }, {
        responsive: true,
        displayModeBar: false
    });
}


function renderInterpretation() {
    const score = calculateGlobalScore();
    const container = document.getElementById("interpretation");

    if (score === null) {
        container.textContent = "Activez au moins un indicateur.";
        return;
    }

    let html = `<p><strong>Score global : ${score.toFixed(1)}/100.</strong> `;

    if (score >= 70) {
        html += "Le baromètre indique une situation globalement favorable.";
    } else if (score >= 40) {
        html += "Le baromètre indique une situation intermédiaire et contrastée.";
    } else {
        html += "Le baromètre indique une situation globalement dégradée.";
    }

    html += "</p><p><strong>Points de vigilance macroéconomiques :</strong></p><ul>";

    ["Croissance du PIB", "Inflation", "Chômage"].forEach(name => {
        const value = dashboardData.scores[name];

        if (activeIndicators[name] && value !== undefined) {
            html += `<li>${name} : ${value.toFixed(1)}/100</li>`;
        }
    });

    html += "</ul><p><strong>Signaux des marchés financiers :</strong></p><ul>";

    ["Euro Stoxx 50", "VIX"].forEach(name => {
        const value = dashboardData.scores[name];

        if (activeIndicators[name] && value !== undefined) {
            html += `<li>${name} : ${value.toFixed(1)}/100</li>`;
        }
    });

    html += "</ul>";

    container.innerHTML = html;
}

function renderDashboard() {
    renderGlobalScore();
    renderIndicators();
    renderContributionChart();
    renderHistoryChart();
    renderInterpretation();
}

document.getElementById("refresh-button")
    .addEventListener("click", loadData);

document.getElementById("history-indicator")
    .addEventListener("change", renderHistoryChart);

document.getElementById("history-period")
    .addEventListener("change", renderHistoryChart);

loadData();
