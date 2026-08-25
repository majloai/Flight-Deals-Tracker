"""
build_page.py

Generuje docs/index.html na podstawie data/history.json i data/latest.json.
Ten plik jest publikowany przez GitHub Pages jako strona główna.
"""

import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(ROOT, "data", "history.json")
LATEST_PATH = os.path.join(ROOT, "data", "latest.json")
OUTPUT_PATH = os.path.join(ROOT, "docs", "index.html")

CURRENCY_SYMBOLS = {"pln": "zł", "usd": "$", "eur": "€"}


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def fmt_price(value, currency):
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    return f"{value:,.0f} {symbol}".replace(",", " ")


def build_html(history, latest, currency):
    updated_at = latest.get("updated_at", "brak danych")
    deals = sorted(latest.get("deals", []), key=lambda d: d["last_price"])

    all_routes = sorted(
        history.values(), key=lambda r: r.get("last_price", float("inf"))
    )

    deals_html = ""
    if deals:
        rows = ""
        for d in deals:
            rows += f"""
            <tr class="deal-row">
                <td>{d['origin']} → {d['destination']}</td>
                <td>{fmt_price(d['last_price'], currency)}</td>
                <td>{fmt_price(d['min_price'], currency)} (rekord)</td>
                <td>{d.get('last_depart_date', '-')}</td>
                <td>{d.get('last_return_date', '-')}</td>
                <td><span class="badge">🔥 OKAZJA</span></td>
            </tr>"""
        deals_html = f"""
        <h2>🔥 Wykryte okazje ({len(deals)})</h2>
        <table>
            <thead>
                <tr><th>Trasa</th><th>Cena</th><th>Najniższa zaobserwowana</th>
                <th>Wylot</th><th>Powrót</th><th></th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
    else:
        deals_html = "<h2>🔥 Wykryte okazje</h2><p class='muted'>Obecnie brak okazji spełniających kryteria (nowy rekord cenowy). Program sprawdza to przy każdym uruchomieniu.</p>"

    all_rows = ""
    for r in all_routes:
        deal_marker = " class='deal-row'" if r.get("is_deal") else ""
        all_rows += f"""
        <tr{deal_marker}>
            <td>{r['origin']} → {r['destination']}</td>
            <td>{fmt_price(r['last_price'], currency)}</td>
            <td>{fmt_price(r['min_price'], currency)}</td>
            <td>{fmt_price(r['max_price'], currency)}</td>
            <td>{fmt_price(r['avg_price'], currency)}</td>
            <td>{r['samples']}</td>
        </tr>"""

    all_table_html = f"""
    <h2>📊 Wszystkie śledzone trasy</h2>
    <table>
        <thead>
            <tr><th>Trasa</th><th>Aktualna cena</th><th>Min</th><th>Max</th>
            <th>Średnia</th><th>Liczba obserwacji</th></tr>
        </thead>
        <tbody>{all_rows if all_rows else "<tr><td colspan='6' class='muted'>Brak danych - poczekaj na pierwsze uruchomienie programu.</td></tr>"}</tbody>
    </table>
    """

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flight Deals Tracker</title>
<style>
    :root {{
        --bg: #0f172a;
        --card: #1e293b;
        --accent: #22c55e;
        --text: #e2e8f0;
        --muted: #94a3b8;
        --deal-bg: rgba(34, 197, 94, 0.15);
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background: var(--bg);
        color: var(--text);
        margin: 0;
        padding: 2rem 1rem;
    }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    h1 {{ font-size: 1.8rem; margin-bottom: 0.25rem; }}
    .updated {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 2rem; }}
    h2 {{ margin-top: 2.5rem; font-size: 1.3rem; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        background: var(--card);
        border-radius: 8px;
        overflow: hidden;
        margin-top: 1rem;
    }}
    th, td {{
        padding: 0.7rem 1rem;
        text-align: left;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        font-size: 0.9rem;
    }}
    th {{ color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }}
    tr.deal-row {{ background: var(--deal-bg); }}
    .badge {{
        background: var(--accent);
        color: #052e16;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
    }}
    .muted {{ color: var(--muted); padding: 1rem; }}
    footer {{ margin-top: 3rem; color: var(--muted); font-size: 0.8rem; text-align: center; }}
</style>
</head>
<body>
<div class="container">
    <h1>✈️ Flight Deals Tracker</h1>
    <div class="updated">Ostatnia aktualizacja: {updated_at}</div>
    {deals_html}
    {all_table_html}
    <footer>Dane: Travelpayouts API · Strona generowana automatycznie przez GitHub Actions</footer>
</div>
</body>
</html>
"""


def main():
    history = load_json(HISTORY_PATH, {})
    latest = load_json(LATEST_PATH, {})

    # currency is not stored per-record; default fallback
    currency = "pln"

    html = build_html(history, latest, currency)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Strona zapisana: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
