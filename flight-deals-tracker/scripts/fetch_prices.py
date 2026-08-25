"""
fetch_prices.py

Pobiera aktualne ceny lotów z Travelpayouts API dla lotnisk wylotu
zdefiniowanych w config.yml, filtruje wyniki wg widełek dat i długości
pobytu, a następnie aktualizuje data/history.json (min / max / średnia
cena dla każdej trasy) oraz zapisuje bieżące wyniki do data/latest.json.

Wymaga zmiennej środowiskowej TRAVELPAYOUTS_TOKEN.
"""

import os
import sys
import json
import yaml
import requests
from datetime import datetime, date

API_URL = "https://api.travelpayouts.com/v2/prices/latest"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.yml")
HISTORY_PATH = os.path.join(ROOT, "data", "history.json")
LATEST_PATH = os.path.join(ROOT, "data", "latest.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def stay_length_days(depart_date_str, return_date_str):
    try:
        d1 = datetime.strptime(depart_date_str, "%Y-%m-%d").date()
        d2 = datetime.strptime(return_date_str, "%Y-%m-%d").date()
        return (d2 - d1).days
    except (ValueError, TypeError):
        return None


def fetch_for_origin(origin, token, config):
    params = {
        "currency": config.get("currency", "pln"),
        "period_type": "year",
        "page": 1,
        "limit": config.get("results_limit", 1000),
        "show_to_affiliates": "true",
        "sorting": "price",
        "origin": origin,
        "beginning_of_period": config["date_from"],
        "one_way": "false" if config.get("round_trip", True) else "true",
        "token": token,
    }

    destinations = config.get("destinations") or []
    all_results = []

    if destinations:
        for dest in destinations:
            p = dict(params)
            p["destination"] = dest
            all_results.extend(_call_api(p))
    else:
        all_results.extend(_call_api(params))

    return all_results


def _call_api(params):
    try:
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        return payload.get("data", [])
    except requests.RequestException as e:
        print(f"[UWAGA] Błąd zapytania do API: {e}", file=sys.stderr)
        return []


def filter_results(results, config):
    date_from = datetime.strptime(config["date_from"], "%Y-%m-%d").date()
    date_to = datetime.strptime(config["date_to"], "%Y-%m-%d").date()
    stay_min = config.get("stay_min_days", 0)
    stay_max = config.get("stay_max_days", 999)
    max_changes = config.get("max_changes", 2)

    filtered = []
    for item in results:
        depart_date = item.get("depart_date")
        return_date = item.get("return_date")
        if not depart_date:
            continue
        try:
            d_depart = datetime.strptime(depart_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if not (date_from <= d_depart <= date_to):
            continue

        if config.get("round_trip", True) and return_date:
            nights = stay_length_days(depart_date, return_date)
            if nights is None or not (stay_min <= nights <= stay_max):
                continue

        if item.get("number_of_changes", 0) > max_changes:
            continue

        filtered.append(item)

    return filtered


def update_history(history, results, min_samples_before_deal):
    """Aktualizuje statystyki historyczne dla każdej trasy i zwraca
    listę wykrytych okazji."""
    deals = []
    now_iso = datetime.utcnow().isoformat() + "Z"

    for item in results:
        origin = item.get("origin")
        destination = item.get("destination")
        price = item.get("price")
        if not origin or not destination or price is None:
            continue

        key = f"{origin}-{destination}"
        record = history.get(key)

        if record is None:
            record = {
                "origin": origin,
                "destination": destination,
                "min_price": price,
                "max_price": price,
                "avg_price": price,
                "samples": 1,
                "last_price": price,
                "last_depart_date": item.get("depart_date"),
                "last_return_date": item.get("return_date"),
                "last_checked": now_iso,
                "is_deal": False,
            }
            history[key] = record
            continue

        is_deal = (
            record["samples"] >= min_samples_before_deal
            and price <= record["min_price"]
        )

        record["min_price"] = min(record["min_price"], price)
        record["max_price"] = max(record["max_price"], price)
        record["avg_price"] = round(
            (record["avg_price"] * record["samples"] + price) / (record["samples"] + 1),
            2,
        )
        record["samples"] += 1
        record["last_price"] = price
        record["last_depart_date"] = item.get("depart_date")
        record["last_return_date"] = item.get("return_date")
        record["last_checked"] = now_iso
        record["is_deal"] = is_deal

        if is_deal:
            deals.append(dict(record, key=key))

    return deals


def main():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        print("BŁĄD: brak zmiennej środowiskowej TRAVELPAYOUTS_TOKEN", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    history = load_json(HISTORY_PATH, {})

    all_results = []
    for origin in config["departure_airports"]:
        print(f"Pobieram oferty dla lotniska: {origin}")
        raw = fetch_for_origin(origin, token, config)
        filtered = filter_results(raw, config)
        print(f"  -> {len(raw)} wyników z API, {len(filtered)} po filtrowaniu")
        all_results.extend(filtered)

    deals = update_history(
        history, all_results, config.get("min_samples_before_deal_alert", 2)
    )

    save_json(HISTORY_PATH, history)
    save_json(
        LATEST_PATH,
        {
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "total_offers_checked": len(all_results),
            "deals_found": len(deals),
            "deals": deals,
        },
    )

    print(f"Gotowe. Sprawdzono {len(all_results)} ofert, znaleziono {len(deals)} okazji.")


if __name__ == "__main__":
    main()
