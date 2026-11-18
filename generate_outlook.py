import json
import os
import re
from datetime import datetime, timedelta, timezone
from google import genai


def load_data(path="data.json"):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        meta = raw.get("meta", {})
        feeds = raw.get("feeds", [])
    else:
        meta = {}
        feeds = raw
    return meta, feeds


def load_import_matrix(path="import_matrix.json"):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def flatten_feed_items(feeds, max_items=160):
    items = []
    for feed in feeds:
        cat = (feed.get("category") or "Allgemein").strip()
        feed_title = (feed.get("title") or "Feed").strip()
        for it in feed.get("items", [])[:10]:
            title = (it.get("title") or "").replace("\n", " ").strip()
            desc = (it.get("desc") or "").replace("\n", " ").strip()
            link = (it.get("link") or "").strip()
            if title:
                items.append({
                    "category": cat,
                    "feed": feed_title,
                    "title": title,
                    "desc": desc,
                    "link": link,
                    "haystack": f"{title} {desc} {cat} {feed_title}".lower(),
                })
            if len(items) >= max_items:
                return items
    return items


def collect_valid_urls(items):
    valid = set()
    for it in items:
        url = (it.get("link") or "").strip()
        if url.startswith("https://") or url.startswith("http://"):
            valid.add(url)
    return valid


def normalize_country_token(entry):
    cleaned = re.sub(r"\([^)]*\)", "", entry).strip()
    return [p.strip() for p in re.split(r"[/,]", cleaned) if len(p.strip()) >= 3]


def match_matrix_to_news(matrix, items):
    """Ordnet aktuelle Meldungen gezielt den 64 Warengruppen & Herkunftsländern zu."""
    matched_entries = []

    for wg in matrix:
        countries = []
        for c in wg.get("laender", []):
            countries.extend(normalize_country_token(c))

        risk_tokens = [
            t.strip().lower()
            for t in re.split(r"[;/,]", wg.get("risiken", ""))
            if len(t.strip()) >= 4
        ]
        wg_tokens = [
            t.strip().lower()
            for t in re.split(r"[/(),\s]+", wg.get("warengruppe", ""))
            if len(t.strip()) >= 4
        ]

        hits = []
        for it in items:
            h = it["haystack"]
            country_hits = [c for c in countries if c.lower() in h]
            risk_hits = [r for r in risk_tokens if r in h]
            wg_hits = [w for w in wg_tokens if w in h]

            if (country_hits and (risk_hits or wg_hits)) or (wg_hits and risk_hits):
                score = len(country_hits) * 2 + len(risk_hits) + len(wg_hits)
                hits.append((score, country_hits, risk_hits, it))

        if hits:
            hits.sort(key=lambda x: x[0], reverse=True)
            top_hits = hits[:3]
            news_snippets = []
            for _, c_hits, r_hits, it in top_hits:
                tags = ", ".join(sorted(set(c_hits + r_hits)))
                url_part = f" | URL: {it['link']}" if it.get("link") else ""
                news_snippets.append(
                    f"  * Meldung: {it['title']} | Quelle: {it['feed']}{url_part}"
                    + (f" | Treffer: {tags}" if tags else "")
                    + (f" | Teaser: {it['desc'][:140]}" if it.get("desc") else "")
                )

            matched_entries.append(
                f"[{wg['id']} | Prio: {wg['prioritaet']}] {wg['warengruppe']} ({wg['bereich']})\n"
                f"  Länder/Lieferanten: {', '.join(wg.get('laender', []))}\n"
                f"  Laufzeit: {wg.get('laufzeit', '')} | Vorlauf: {wg.get('vorlauf_zwischenschritte', '')}\n"
                f"  Wirkung DE: {wg.get('wirkung_deutschland', '')}\n"
                f"  Hinweis: {wg.get('hinweis', '')}\n"
                + "\n".join(news_snippets)
            )

    if not matched_entries and matrix:
        prio_high = [w for w in matrix if w.get("prioritaet") == "Sehr hoch"][:8]
        for wg in prio_high:
            matched_entries.append(
                f"[{wg['id']} | Prio: {wg['prioritaet']}] {wg['warengruppe']} ({wg['bereich']})\n"
                f"  Länder/Lieferanten: {', '.join(wg.get('laender', []))}\n"
                f"  Laufzeit: {wg.get('laufzeit', '')} | Vorlauf: {wg.get('vorlauf_zwischenschritte', '')}\n"
                f"  Wirkung DE: {wg.get('wirkung_deutschland', '')}\n"
                f"  Hinweis: {wg.get('hinweis', '')}"
            )

    return "\n\n".join(matched_entries[:25])


def build_general_digest(items, max_items=50):
    lines = []
    for it in items[:max_items]:
        url_part = f" | URL: {it['link']}" if it.get("link") else ""
        lines.append(
            f"- [{it['category']}] {it['title']} ({it['feed']}) | {it['desc'][:140]}{url_part}"
        )
    return "\n".join(lines)


SECTION_KEYWORDS = {
    1: ["peru", "fidschi", "el niño", "el nino", "dürre", "drought", "flood", "überschwemmung", "storm", "sturm", "länder", "region", "export", "import", "germanwatch", "klima"],
    2: ["lebensmittel", "agrar", "ernte", "food", "crop", "dünger", "fertilizer", "kaffee", "kakao", "weizen", "mais", "soja", "obst", "gemüse", "avocado", "bananen", "wasser"],
    3: ["energie", "energy", "strom", "gas", "lng", "öl", "oil", "metall", "kupfer", "lithium", "seltene erden", "zellstoff", "papier", "chemie", "halbleiter", "chip", "hafen", "port", "fracht", "shipping", "lieferkette"],
    4: ["gesundheit", "health", "arzneimittel", "wirkstoff", "pharma", "medizin", "klinik", "krankenhaus", "infektion", "antibiotika", "wasser"],
    5: ["wohnen", "versicherung", "insurance", "bau", "gebäude", "hochwasser", "starkregen", "sturm", "schaden", "kosten", "inflation", "preis"],
    6: ["planung", "saison", "lager", "vertrag", "wechselkurs", "risiko", "resilienz", "versorgung", "deutschland"],
}


def pick_section_sources(sec_index, items, max_links=3):
    """Wählt passende echte Feed-Einträge mit gültiger URL für einen Bereich aus."""
    keywords = SECTION_KEYWORDS.get(sec_index, [])
    scored = []
    for it in items:
        url = (it.get("link") or "").strip()
        if not (url.startswith("https://") or url.startswith("http://")):
            continue
        h = it["haystack"]
        score = sum(1 for kw in keywords if kw in h)
        scored.append((score, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = [it for score, it in scored if score > 0][:max_links]

    # Fallback: falls keine Schlüsselwörter matchen, die ersten gültigen Links nehmen
    if not chosen:
        start = ((sec_index - 1) * max_links) % max(1, len([x for _, x in scored]))
        valid_items = [x for _, x in scored]
        for offset in range(len(valid_items)):
            cand = valid_items[(start + offset) % len(valid_items)]
            if cand not in chosen:
                chosen.append(cand)
            if len(chosen) >= min(2, len(valid_items)):
                break

    return chosen


def ensure_section_sources(html_out, items, valid_urls):
    """Bereinigt ungültige Links und stellt sicher, dass jede Sektion echte Links hat."""
    def clean_link(match):
        href = match.group(1).strip()
        return match.group(0) if href in valid_urls else ""

    cleaned = re.sub(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</a>',
        clean_link,
        html_out,
        flags=re.IGNORECASE | re.DOTALL,
    )

    sections = re.findall(
        r'(<section\b[^>]*>)(.*?)(</section>)',
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not sections:
        return cleaned

    rebuilt = []
    for idx, (open_tag, body, close_tag) in enumerate(sections, start=1):
        existing_links = re.findall(r'href=["\'](https?://[^"\']+)["\']', body, flags=re.IGNORECASE)
        existing_links = [u for u in existing_links if u in valid_urls]

        # Bestehenden Belege-Block entfernen, damit wir sauber neu aufbauen können
        body_without_sources = re.sub(
            r'<div\b[^>]*class=["\'][^"\']*outlook-sources[^"\']*["\'][^>]*>.*?</div>\s*$',
            "",
            body,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        chosen_items = pick_section_sources(idx, items, max_links=3)
        if chosen_items:
            li_html = "\n".join(
                f'<li><a href="{it["link"]}" target="_blank" rel="noopener noreferrer">{it["title"]}</a> <span class="outlook-source-feed">({it["feed"]})</span></li>'
                for it in chosen_items
            )
            sources_block = (
                f'\n<div class="outlook-sources">\n'
                f'  <strong>Belege:</strong>\n'
                f'  <ul>\n    {li_html}\n  </ul>\n'
                f'</div>'
            )
        else:
            sources_block = '\n<div class="outlook-sources"><strong>Belege:</strong> <span class="outlook-no-direct-link">Keine direkten Links im aktuellen Datenstand.</span></div>'

        rebuilt.append(f"{open_tag}\n{body_without_sources}{sources_block}\n{close_tag}")

    return "\n".join(rebuilt)


def write_fallback(last_updated, message):
    os.makedirs("generated", exist_ok=True)
    html = f"""
    <section class="category-section outlook-card">
        <h2>💶 3-Monats-Ausblick: Finanzen &amp; Planung ({last_updated})</h2>
        <p class="no-data">{message}</p>
    </section>
    """
    with open("generated/outlook_content.html", "w", encoding="utf-8") as f:
        f.write(html.strip())


def generate_outlook():
    os.makedirs("generated", exist_ok=True)
    meta, feeds = load_data("data.json")
    matrix = load_import_matrix("import_matrix.json")

    now_cet = datetime.now(timezone(timedelta(hours=1)))
    last_updated = meta.get("last_updated") or now_cet.strftime("%d.%m.%Y, %H:%M Uhr")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Hinweis: GEMINI_API_KEY nicht gesetzt. Schreibe Fallback-Inhalt.")
        write_fallback(last_updated, "Kein API-Schlüssel konfiguriert. Der 3-Monats-Ausblick ist vorübergehend deaktiviert.")
        return

    items = flatten_feed_items(feeds)
    if not items:
        write_fallback(last_updated, "Keine aktuellen Meldungen in data.json vorhanden.")
        return

    valid_urls = collect_valid_urls(items)
    matched_block = match_matrix_to_news(matrix, items)
    general_block = build_general_digest(items)

    prompt = f"""
Du bist ein nüchterner Analyst für Versorgungs-, Lieferketten- und Preisrisiken mit Bezug auf Deutschland.
Aufgabe: Leite aus aktuellen Meldungen (Datenstand: {last_updated}) und den deutschen Import-/Warengruppen-Daten
ab, was in den **nächsten 3 Monaten** für Finanzen, Preise, Versorgung und Planung in Deutschland relevant sein kann.

Wichtige Prinzipien:
- Erst Herkunftsländer/Regionen und gemeldete Ereignisse betrachten, dann Laufzeit/Vorlauf und Lieferkette prüfen,
  und erst dann mögliche Folgen in Deutschland für das 3-Monats-Fenster einordnen.
- Kennzeichne Aussagen klar mit `[Belegt]`, `[Plausibel]` oder `[Offen]`.
- Keine Finanz- oder Anlageberatung. Erfinde keine Zahlen, Preise, Länder oder URLs – nutze ausschließlich die Daten unten.

Strukturiere die Ausgabe in **6 Sektionen** (`<section class="category-section outlook-card">`):
1. `<h2>🌍 Herkunftsländer &amp; aktuelle Signale</h2>`
2. `<h2>🥦 Lebensmittel, Agrar &amp; Dünger</h2>`
3. `<h2>⚡ Energie, Rohstoffe &amp; Industrie-Inputs</h2>`
4. `<h2>🏥 Gesundheit &amp; Versorgungssicherheit</h2>`
5. `<h2>🏠 Wohnen, Versicherungen &amp; Alltagskosten</h2>`
6. `<h2>🧭 3-Monats-Planung &amp; Gegenfaktoren</h2>` (Gib NUR reines HTML ohne ```html Codeblöcke zurück.)

ABGLEICH MIT IMPORT- & WARENGRUPPEN-MATRIX (64 Gruppen):
{matched_block}

AKTUELLE MELDUNGEN AUS DATA.JSON:
{general_block}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )

        html_out = (response.text or "").strip()
        if html_out.startswith("```html"):
            html_out = html_out[7:]
        if html_out.startswith("```"):
            html_out = html_out[3:]
        if html_out.endswith("```"):
            html_out = html_out[:-3]
        html_out = html_out.strip()

        if not html_out:
            write_fallback(last_updated, "Die KI-Antwort für den 3-Monats-Ausblick war leer.")
            return

        html_out = ensure_section_sources(html_out, items, valid_urls)

        with open("generated/outlook_content.html", "w", encoding="utf-8") as f:
            f.write(html_out)
        print("generated/outlook_content.html erfolgreich erstellt.")

    except Exception as e:
        print(f"Fehler bei generate_outlook.py: {repr(e)}")
        write_fallback(last_updated, "Aktuell gab es eine vorübergehende Störung bei der KI-Generierung. Beim nächsten Lauf wird der Ausblick aktualisiert.")


if __name__ == "__main__":
    generate_outlook()
