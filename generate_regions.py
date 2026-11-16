import json
import os
from datetime import datetime
from google import genai


def generate_regions_page():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Fehler: GEMINI_API_KEY ist nicht gesetzt.")
        write_fallback("Kein API-Schlüssel konfiguriert. Die Regionen-Ansicht ist vorübergehend deaktiviert.")
        return

    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden von data.json: {e}")
        write_fallback("Datenbasis konnte nicht geladen werden.")
        return

    feeds = data if isinstance(data, list) else data.get('feeds', [])

    # Kompakte Textbasis mit Kategorien, Quellen, Titeln, Teasern und Links aufbauen
    items_summary = []
    for feed in feeds:
        category = feed.get('category', 'Allgemein')
        feed_title = feed.get('title', '')
        for item in feed.get('items', [])[:10]:
            title = (item.get('title') or '').replace('\n', ' ').strip()
            desc = (item.get('desc') or '').replace('\n', ' ').strip()
            link = (item.get('link') or '').strip()
            if title:
                entry = f"Kategorie: {category} | Quelle: {feed_title}\nTitel: {title}"
                if desc:
                    entry += f"\nInhalt: {desc}"
                if link:
                    entry += f"\nLink: {link}"
                items_summary.append(entry)

    if not items_summary:
        write_fallback("Keine aktuellen Meldungen für die Regionalanalyse vorhanden.")
        return

    prompt_content = "\n---\n".join(items_summary[:80])
    today_str = datetime.now().strftime('%d.%m.%Y')

    prompt = f"""
Du bist ein präziser OSINT-Analyst für globale Krisen und Klimarisiken.
Hier sind aktuelle Schlagzeilen, Teaser und Links aus verschiedenen Feeds:

{prompt_content}

Analysiere diese Meldungen und erstelle eine strukturierte Regionalanalyse auf Deutsch im sauberen HTML-Format.

HALTE DICH STRIKT AN FOLGENDE STRUKTUR (keine umschließenden ```html Codeblocks, nur das reine HTML):

1. Ein Highlight-Kasten ganz oben für den neuesten Lauf:
<div class="category-section" style="border-left: 4px solid var(--accent);">
  <h2 style="margin-top:0; color: var(--accent); font-size: 1.15rem; border-bottom: none; padding-bottom: 0;">
    🚨 Im letzten Lauf neu im Fokus ({today_str})
  </h2>
  <p style="color: var(--text-muted); font-size: 0.92rem; line-height: 1.55; margin: 8px 0 0 0;">
    [Schreibe hier 2 bis 3 prägnante Sätze darüber, wo im aktuellen Lauf die wichtigsten regionalen Schwerpunkte, Neuzugänge oder Verschiebungen liegen.]
  </p>
</div>

2. Danach EXAKT diese 6 Regionen-Sektionen in dieser Reihenfolge (mit genau diesen Überschriften im h2):
- 🇪🇺 Europa & DACH (inkl. Mittelmeerraum)
- 🌎 Nord- & Südamerika (inkl. Karibik)
- 🌏 Asien & Pazifik (inkl. Australien & Inselstaaten)
- 🌍 Afrika & Naher Osten
- 🧊 Polarregionen & Ozeane
- 🌐 Global & Systemisch (UN, COP, globale Finanzmärkte, Studien)

Für JEDE dieser 6 Sektionen erstellst du folgendes HTML-Raster:
<div class="category-section">
  <div style="border-bottom: 2px solid var(--accent); padding-bottom: 10px; margin-bottom: 15px;">
    <h2 style="margin: 0; font-size: 1.25rem; color: var(--accent); font-weight: 600;">[EMOJI] [Regionsname]</h2>
    <p style="margin: 6px 0 0 0; font-size: 0.9rem; color: var(--text-muted); line-height: 1.45;">
      <strong>Regions-Fazit:</strong> [1–2 präzise Sätze, warum diese Region im aktuellen Lauf im Fokus steht und welche Muster sichtbar sind.]
    </p>
  </div>
  <ul style="margin: 0; padding-left: 18px; font-size: 0.88rem; line-height: 1.6; color: var(--text-muted);">
    <!-- Wähle bis zu 5 passende Artikel aus den obigen Daten aus, die geografisch oder thematisch zu dieser Region passen. -->
    <!-- Nutze ausschließlich echte Links und Titel aus den obigen Daten. Wenn weniger als 5 passende Meldungen vorliegen, nimm alle passenden und erfinde keine hinzu. -->
    <li style="margin-bottom: 10px;">
      <a href="LINK_AUS_DEN_DATEN" target="_blank" rel="noopener" style="color: var(--link-color); font-weight: 600; text-decoration: none;">ARTIKEL_TITEL</a>
      <span style="font-size: 0.75rem; background: var(--card-bg); border: 1px solid var(--border); padding: 1px 6px; border-radius: 4px; margin-left: 6px;">Thema: [Themen-Kategorie]</span>
      <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 3px;">[Kurze, sachliche Einordnung in 1 Satz auf Basis des Teasers/Titels.]</div>
    </li>
  </ul>
</div>

Wichtige Regeln:
- Erfinde keine URLs, Titel oder Fakten; verwende nur Einträge aus den obigen Meldungen.
- Ziele pro Region auf bis zu 5 relevante Meldungen ab, damit das Bild greifbar bleibt, ohne unpassende Treffer hineinzupressen.
- Gib NUR reines HTML zurück (ohne Markdown-Codeblöcke).
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
        )

        regions_html = (response.text or "").strip()
        if regions_html.startswith("```html"):
            regions_html = regions_html[7:]
        if regions_html.startswith("```"):
            regions_html = regions_html[3:]
        if regions_html.endswith("```"):
            regions_html = regions_html[:-3]
        regions_html = regions_html.strip()

        if not regions_html:
            write_fallback("Die KI-Antwort für die Regionalanalyse war leer.")
            return

        os.makedirs('generated', exist_ok=True)
        with open('generated/regions_content.html', 'w', encoding='utf-8') as f:
            f.write(regions_html)
        print("Regionen-Ansicht erfolgreich generiert!")

    except Exception as e:
        print(f"KRITISCHER FEHLER BEI DER REGIONS-API: {repr(e)}")
        raise e


def write_fallback(message):
    os.makedirs('generated', exist_ok=True)
    fallback_html = f"""
    <div class="category-section" style="border-left: 4px solid var(--accent);">
      <h2 style="margin-top:0; color: var(--accent);">🚨 Im letzten Lauf neu im Fokus</h2>
      <p style="color: var(--text-muted); font-style: italic; margin: 0;">{message}</p>
    </div>
    """
    with open('generated/regions_content.html', 'w', encoding='utf-8') as f:
        f.write(fallback_html)


if __name__ == "__main__":
    generate_regions_page()
