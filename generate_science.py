import json
import os
from datetime import datetime, timedelta, timezone
from google import genai

SCIENCE_CATEGORY = "Wissenschaft & Studien"


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


def filter_science_feeds(feeds):
    """Filtert gezielt die Wissenschafts-Feeds aus data.json."""
    science_feeds = [
        f for f in feeds
        if SCIENCE_CATEGORY.lower() in (f.get("category") or "").lower()
    ]
    return science_feeds


def build_science_digest(science_feeds, items_per_feed=10):
    lines = []
    for feed in science_feeds:
        title = feed.get("title", "Wissenschafts-Feed")
        items = feed.get("items", [])[:items_per_feed]
        if not items:
            continue
        lines.append(f"[{title}]")
        for it in items:
            t = (it.get("title") or "").replace("\n", " ").strip()
            d = (it.get("desc") or "").replace("\n", " ").strip()
            link = it.get("link") or "#"
            lines.append(f"- {t} | {d} | URL: {link}")
    return "\n".join(lines)


def build_sources_html(science_feeds):
    """Erzeugt unterhalb der KI-Synthese die verifizierbare Quellenliste."""
    blocks = []
    for feed in science_feeds:
        title = feed.get("title", "Quelle")
        items = feed.get("items", [])[:12]
        if items:
            lis = "\n".join(
                f'<li><a href="{it.get("link", "#")}" target="_blank" rel="noopener">{it.get("title", "Ohne Titel")}</a>'
                + (f'<div class="item-teaser">{it["desc"]}</div>' if it.get("desc") else "")
                + "</li>"
                for it in items
            )
            content = f"<ul class='source-list'>{lis}</ul>"
        else:
            content = "<p class='no-data'>Aktuell keine neuen Treffer in diesem Feed.</p>"

        blocks.append(f"""
        <section class="category-section">
            <h2>📚 {title}</h2>
            {content}
        </section>
        """)
    return "\n".join(blocks)


def fallback_html(last_updated, sources_html):
    return f"""
    <section class="category-section">
        <h2>🔬 5 Kernaussagen aus der Forschung</h2>
        <p class="no-data">
            Aktuell konnte keine KI-Synthese erstellt werden (Stand: {last_updated}).
            Unten findest du die ungefilterten Original-Feeds aus Journals, Institutionen und von Forschenden.
        </p>
    </section>
    {sources_html}
    """


def generate_science():
    os.makedirs("generated", exist_ok=True)
    meta, feeds = load_data("data.json")

    now_cet = datetime.now(timezone(timedelta(hours=1)))
    last_updated = meta.get("last_updated") or now_cet.strftime("%d.%m.%Y, %H:%M Uhr")

    science_feeds = filter_science_feeds(feeds)
    sources_html = build_sources_html(science_feeds)

    if not science_feeds:
        html_out = """
        <section class="category-section">
            <h2>🔬 Was sagt die Wissenschaft?</h2>
            <p class="no-data">
                Noch keine Wissenschafts-Feeds in der <code>feeds.json</code> unter der Kategorie
                <strong>"Wissenschaft &amp; Studien"</strong> hinterlegt.
            </p>
        </section>
        """
        with open("generated/science_content.html", "w", encoding="utf-8") as f:
            f.write(html_out)
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Hinweis: GEMINI_API_KEY nicht gesetzt. Schreibe Fallback-Inhalt.")
        with open("generated/science_content.html", "w", encoding="utf-8") as f:
            f.write(fallback_html(last_updated, sources_html))
        return

    digest_text = build_science_digest(science_feeds)

    prompt = f"""
Du bist ein Wissenschafts-Analyst für Klimaforschung. Analysiere die folgenden aktuellen Meldungen
aus Fachzeitschriften (Nature, Science, PLOS etc.), Forschungsinstitutionen (IPCC, WMO, Copernicus, PIK etc.)
und von internationalen Klimaforscherinnen und -forschern (Datenstand: {last_updated}).

Erstelle daraus EXAKT 5 Kernaussagen („Was sagt die Wissenschaft aktuell?“).

Aufbau für jede der 5 Kernaussagen:
- Eine prägnante Überschrift im <h2>-Tag mit Nummerierung (z. B. `<h2>1. [Prägnante Kernaussage]</h2>`)
- **Befund & Einordnung**: 2–3 klare, sachliche Sätze, was die Studien, Daten oder Forschenden konkret zeigen und warum es systemisch relevant ist.
- **Beleg**: Mindestens eine direkte Quellenangabe aus den Meldungen unten mit verlinktem Originaltitel (`<a href="..." target="_blank" rel="noopener">Titel</a>`) sowie Nennung des Journals, Instituts oder Forschenden.

Wichtige Regeln:
- Antworte auf Deutsch, evidenzbasiert, nüchtern und ohne Spekulationen.
- Erfinde keine Studien, Zahlen oder URLs – stütze dich ausschließlich auf die Meldungen unten.
- Gib NUR reines HTML zurück (ohne ```html ... ``` Codeblöcke), bestehend aus 5 `<section class="category-section">` Blöcken.

WISSENSCHAFTS-MELDUNGEN:
{digest_text}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt,
        )
        synthesis_html = (response.text or "").strip()
        if synthesis_html.startswith("```"):
            lines = synthesis_html.splitlines()
            synthesis_html = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()

        if not synthesis_html:
            html_out = fallback_html(last_updated, sources_html)
        else:
            html_out = f"{synthesis_html}\n\n{sources_html}"

        with open("generated/science_content.html", "w", encoding="utf-8") as f:
            f.write(html_out)
        print("generated/science_content.html erfolgreich erstellt.")
    except Exception as e:
        print(f"Fehler bei generate_science.py: {e}")
        with open("generated/science_content.html", "w", encoding="utf-8") as f:
            f.write(fallback_html(last_updated, sources_html))


if __name__ == "__main__":
    generate_science()
