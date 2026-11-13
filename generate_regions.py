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
    
    # Kompakte Textbasis aufbauen
    items_summary = []
    for feed in feeds:
        category = feed.get('category', 'Allgemein')
        feed_title = feed.get('title', '')
        for item in feed.get('items', [])[:10]: # Top 10 pro Feed
            title = item.get('title', '')
            desc = item.get('desc', '')
            link = item.get('link', '')
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

    prompt_content = "\n---\n".join(items_summary[:60])

    prompt = f"""
Du bist ein präziser OSINT-Analyst für globale Krisen und Klimarisiken.
Hier sind die aktuellen Schlagzeilen und Artikel aus verschiedenen Feeds:

{prompt_content}

Analysiere diese Meldungen und erstelle eine strukturierte Regionalanalyse auf Deutsch im sauberen HTML-Format.

HALTE DICH STRIKT AN FOLGENDE STRUKTUR (keine umschließenden ```html Codeblocks, nur das reine HTML):

1. Ein Highlight-Kasten ganz oben für den neuesten Lauf:
<div style="background: var(--section-bg); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 18px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <h3 style="margin-top:0; color: var(--accent); font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
    🚨 Im letzten Lauf neu im Fokus ({datetime.now().strftime('%d.%m.%Y')})
  </h3>
  <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; margin: 0;">
    [Schreibe hier 2 prägnante Sätze darüber, wo im aktuellen Lauf die dramatischsten Schwerpunkte, Neuzugänge oder Verschiebungen liegen.]
  </p>
</div>

2. Danach exakt 6 Regionen-Sektionen als HTML-Blöcke (Verwende genau diese Überschriften als h2 mit passendem Emoji):
- 🇪🇺 Europa & DACH (inkl. Mittelmeerraum)
- 🌎 Nord- & Südamerika (inkl. Karibik)
- 🌏 Asien & Pazifik (inkl. Australien & Inselstaaten)
- 🌍 Afrika & Naher Osten
- 🧊 Polarregionen & Ozeane
- 🌐 Global & Systemisch (UN, COP, globale Finanzmärkte, Studien)

Für JEDE dieser 6 Sektionen erstellst du folgendes HTML-Raster:
<div class="category-section" style="margin-bottom: 30px; background: var(--section-bg); border: 1px solid var(--border); border-radius: 12px; padding: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <div style="border-bottom: 2px solid var(--accent); padding-bottom: 10px; margin-bottom: 15px;">
    <h2 style="margin: 0; font-size: 1.25rem; color: var(--accent); font-weight: 600;">[EMOJI] [Regionsname]</h2>
    <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: var(--text-muted); font-style: italic;">[1 kurzer Satz KI-Fazit zu dieser Region in diesem Lauf]</p>
  </div>
  <ul style="margin: 0; padding-left: 18px; font-size: 0.88rem; line-height: 1.6; color: var(--text-muted);">
    <!-- Wähle passende Artikel aus den Daten aus, die thematisch in diese Region passen. Formatiere sie so: -->
    <li style="margin-bottom: 10px;">
      <a href="LINK_AUS_DEN_DATEN" target="_blank" rel="noopener" style="color: var(--link-color); font-weight: 600; text-decoration: none;">ARTIKEL_TITEL</a> 
      <span style="font-size: 0.75rem; background: var(--card-bg); border: 1px solid var(--border); padding: 1px 5px; border-radius: 4px; margin-left: 5px;">Thema: [Themen-Kategorie]</span>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">Kurz-Teaser oder Einordnung.</div>
    </li>
  </ul>
</div>
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
        )
        
        regions_html = response.text.strip()
        if regions_html.startswith("```html"):
            regions_html = regions_html[7:]
        if regions_html.startswith("```"):
            regions_html = regions_html[3:]
        if regions_html.endswith("```"):
            regions_html = regions_html[:-3]
        regions_html = regions_html.strip()

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
    <div style="background: var(--section-bg); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 18px; margin-bottom: 25px;">
      <h3 style="margin-top:0; color: var(--accent);">🚨 Im letzten Lauf neu im Fokus</h3>
      <p style="color: var(--text-muted); font-style: italic; margin: 0;">{message}</p>
    </div>
    """
    with open('generated/regions_content.html', 'w', encoding='utf-8') as f:
        f.write(fallback_html)

if __name__ == "__main__":
    generate_regions_page()
