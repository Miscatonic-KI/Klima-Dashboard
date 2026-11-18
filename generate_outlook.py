import json
import os
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


def build_compact_digest(feeds, max_feeds=45, items_per_feed=6):
    lines = []
    for feed in feeds[:max_feeds]:
        cat = (feed.get("category") or "Allgemein").strip()
        title = (feed.get("title") or "Feed").strip()
        items = feed.get("items", [])[:items_per_feed]
        if not items:
            continue
        lines.append(f"[{cat} | {title}]")
        for it in items:
            t = (it.get("title") or "").replace("\n", " ").strip()
            d = (it.get("desc") or "").replace("\n", " ").strip()
            link = (it.get("link") or "#").strip()
            lines.append(f"- {t} | {d} | URL: {link}")
    return "\n".join(lines)


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

    now_cet = datetime.now(timezone(timedelta(hours=1)))
    last_updated = meta.get("last_updated") or now_cet.strftime("%d.%m.%Y, %H:%M Uhr")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Hinweis: GEMINI_API_KEY nicht gesetzt. Schreibe Fallback-Inhalt.")
        write_fallback(last_updated, "Kein API-Schlüssel konfiguriert. Der 3-Monats-Ausblick ist vorübergehend deaktiviert.")
        return

    digest_text = build_compact_digest(feeds)
    if not digest_text.strip():
        write_fallback(last_updated, "Keine aktuellen Meldungen in data.json vorhanden.")
        return

    prompt = f"""
Du bist ein Analyst für systemische Risiken, Lieferketten und alltagsnahe wirtschaftliche Wirkungsketten.
Analysiere die folgenden aktuellen Meldungen (Datenstand: {last_updated}) und erstelle eine kompakte,
nüchterne Orientierungshilfe für die **nächsten 3 Monate** (keine Anlage- oder Finanzberatung).

Strukturiere die Antwort in **6 Sektionen** (`<section class="category-section outlook-card">`) mit jeweils einer klaren `<h2>`-Überschrift:
1. `<h2>🥦 Lebensmittel &amp; Landwirtschaft</h2>`
2. `<h2>⚡ Energie &amp; Rohstoffe</h2>`
3. `<h2>🚢 Lieferketten &amp; Versorgung</h2>`
4. `<h2>🏠 Wohnen &amp; Versicherungen</h2>`
5. `<h2>🏥 Gesundheit &amp; medizinische Versorgung</h2>`
6. `<h2>🧭 3-Monats-Planung &amp; Gegenprüfung</h2>`

In den Sektionen 1 bis 5 gehe auf diese drei Fragen ein:
- **Was könnte teurer, knapper oder schwieriger werden?** (konkrete Ableitung aus den Meldungen, mit Status-Label `[Belegt]`, `[Plausibel]` oder `[Offen]`).
- **Mögliche Wirkungskette & Ursprungsregionen:** Welche Zwischenschritte oder Regionen hängen zusammen, und wo fehlen noch harte Preis-/Marktdaten?
- **Belege aus den Meldungen:** 1 bis 2 passende Links aus den Daten (`<a href="..." target="_blank" rel="noopener">Titel</a>`) – falls für einen Bereich keine direkte Meldung passt, ehrlich kennzeichnen statt erfinden.

In Sektion 6 (`3-Monats-Planung & Gegenprüfung`):
- Nenne 3–4 praktische Prüfpunkte für die eigene Planung der nächsten 3 Monate und weise kurz auf andere Einflussfaktoren hin (Saison, Wechselkurse, Verträge, allgemeine Inflation).

Wichtige Regeln:
- Antworte auf Deutsch, sachlich, unaufgeregt und ohne Weltuntergangs-Rhetorik.
- Erfinde keine Fakten, Zahlen, Preise oder URLs; nutze nur Einträge aus den Meldungen unten.
- Gib NUR reines HTML zurück (ohne ```html ... ``` Codeblöcke).

MELDUNGEN:
{digest_text}
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

        with open("generated/outlook_content.html", "w", encoding="utf-8") as f:
            f.write(html_out)
        print("generated/outlook_content.html erfolgreich erstellt.")

    except Exception as e:
        print(f"Fehler bei generate_outlook.py: {repr(e)}")
        write_fallback(last_updated, "Aktuell gab es eine vorübergehende Störung bei der KI-Generierung. Beim nächsten Lauf wird der Ausblick aktualisiert.")


if __name__ == "__main__":
    generate_outlook()
