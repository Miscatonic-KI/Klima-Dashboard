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


def build_compact_digest(feeds, max_feeds=40, items_per_feed=5):
    """Verdichtet Meldungen kompakt, damit der Prompt schnell und zuverlässig bleibt."""
    lines = []
    for feed in feeds[:max_feeds]:
        cat = feed.get("category", "Allgemein")
        title = feed.get("title", "Feed")
        items = feed.get("items", [])[:items_per_feed]
        if not items:
            continue
        lines.append(f"[{cat} | {title}]")
        for it in items:
            t = (it.get("title") or "").replace("\n", " ").strip()
            d = (it.get("desc") or "").replace("\n", " ").strip()
            link = it.get("link") or "#"
            lines.append(f"- {t} | {d} | URL: {link}")
    return "\n".join(lines)


def fallback_html(meta_info):
    return f"""
    <div class="category-section">
        <div class="category-header">
            <h2>🎭 Akteure &amp; Hebel (Hinweis)</h2>
        </div>
        <p class="no-data">
            Aktuell konnte keine KI-Auswertung generiert werden (Stand: {meta_info.get("last_updated", "unbekannt")}).
            Beim nächsten Lauf wird die Analyse automatisch aktualisiert.
        </p>
    </div>
    """


def generate_actors():
    os.makedirs("generated", exist_ok=True)
    meta, feeds = load_data("data.json")

    now_cet = datetime.now(timezone(timedelta(hours=1)))
    last_updated = meta.get("last_updated") or now_cet.strftime("%d.%m.%Y, %H:%M Uhr")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Hinweis: GEMINI_API_KEY nicht gesetzt. Schreibe Fallback-Inhalt.")
        with open("generated/actors_content.html", "w", encoding="utf-8") as f:
            f.write(fallback_html({"last_updated": last_updated}))
        return

    digest_text = build_compact_digest(feeds)

    prompt = f"""
Du bist ein OSINT-Analyst für systemische Klimarisiken. Analysiere die folgenden aktuellen Meldungen
(Datenstand: {last_updated}) und ordne sie nach den 5 zentralen Akteurs- & Hebelgruppen.

Nutze EXAKT diese 5 Gruppen in dieser Reihenfolge als Abschnitte:
1. Staaten, Regierungen & Diplomatie (Gesetze, Klimaziele, Haushalte, COP-Verhandlungen, Förderprogramme)
2. Wirtschaft, Konzerne & Finanzsystem (Energie/Industrie, Lieferketten, Versicherer, Kapital & Nothilfe)
3. Wissenschaft, Daten & Institutionen (IPCC, Klimaforschung, Kipppunkte, Frühwarnsysteme, Umfragen)
4. Zivilgesellschaft, Öffentlichkeit & Debatten (Proteste, Aktivismus, Bildung, gesellschaftliche Diskurse)
5. Kommunen, Regionen & Einsatzkräfte vor Ort (Städte, Landkreise, Katastrophenschutz, lokale Anpassung)

Für JEDE der 5 Gruppen liefere:
- **Hebel & Dynamik**: 1–2 prägnante Sätze, wo in dieser Gruppe gerade der wichtigste Hebel oder Handlungsdruck liegt (nur auf Basis der Meldungen).
- **Konkrete Signale**: 2 bis 4 Stichpunkte mit passendem Meldungstitel, kurzem Einordnungssatz und – wo sinnvoll – verlinktem Titel (`<a href="..." target="_blank" rel="noopener">Titel</a>`).

Wichtige Regeln:
- Antworte auf Deutsch, sachlich, klar und ohne Floskeln.
- Erfinde keine Fakten oder Links hinzu; nutze nur Informationen aus den Meldungen unten.
- Gib NUR reines HTML zurück (ohne ```html ... ``` Codeblöcke), bestehend aus <section class="category-section"> Blöcken,
  in denen die Gruppenüberschrift in einem <h2> steht (wichtig für die automatische Menü-Erkennung).

MELDUNGEN:
{digest_text}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        html_out = (response.text or "").strip()
        if html_out.startswith("```"):
            lines = html_out.splitlines()
            html_out = "\n".join(line for line in lines if not line.strip().startswith("```")).strip()

        if not html_out:
            html_out = fallback_html({"last_updated": last_updated})

        with open("generated/actors_content.html", "w", encoding="utf-8") as f:
            f.write(html_out)
        print("generated/actors_content.html erfolgreich erstellt.")
    except Exception as e:
        print(f"Fehler bei generate_actors.py: {e}")
        with open("generated/actors_content.html", "w", encoding="utf-8") as f:
            f.write(fallback_html({"last_updated": last_updated}))


if __name__ == "__main__":
    generate_actors()
