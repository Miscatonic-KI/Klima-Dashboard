import json
import os
from datetime import datetime
from google import genai

def generate_briefing():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Fehler: GEMINI_API_KEY ist nicht gesetzt.")
        write_fallback("Kein API-Schlüssel konfiguriert. Das KI-Briefing ist vorübergehend deaktiviert.")
        return

    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden von data.json: {e}")
        write_fallback("Datenbasis konnte nicht geladen werden.")
        return

    # Feeds auslesen (unterstützt Liste oder Dict mit 'feeds')
    feeds = data if isinstance(data, list) else data.get('feeds', [])
    
    # Kompakte Textbasis mit Titeln UND Beschreibungen aufbauen
    items_summary = []
    for feed in feeds:
        category = feed.get('category', 'Allgemein')
        feed_title = feed.get('title', '')
        for item in feed.get('items', [])[:10]: # Top 10 pro Feed für tiefe Analyse
            title = item.get('title', '')
            desc = item.get('desc', '')
            link = item.get('link', '')
            if title:
                entry = f"Kategorie: {category} | Quelle: {feed_title}\nTitel: {title}"
                if desc:
                    entry += f"\nInhalt/Teaser: {desc}"
                if link:
                    entry += f"\nLink: {link}"
                items_summary.append(entry)

    if not items_summary:
        write_fallback("Keine aktuellen Meldungen für eine Analyse vorhanden.")
        return

    prompt_content = "\n---\n".join(items_summary[:60]) # Beschränkung für effizientes Token-Budget

    prompt = f"""
Du bist ein präziser Analyst für Klimakrise, globale Krisen und Systemrisiken.
Hier sind die aktuellsten Schlagzeilen und Artikel-Teaser aus verschiedenen RSS-Feeds:

{prompt_content}

Erstelle ein strukturiertes Lage-Briefing auf Deutsch im sauberen HTML-Format.

HALTE DICH STRIKT AN FOLGENDE STRUKTUR (keine umschließenden ```html Codeblocks, nur das reine HTML):

<div style="background: var(--section-bg); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 18px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <h3 style="margin-top:0; color: var(--accent); font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
    🤖 KI-Briefing des Tages ({datetime.now().strftime('%d.%m.%Y')})
  </h3>
  
  <div style="margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px dashed var(--border);">
    <strong style="color: var(--text-main); font-size: 0.9rem; display: block; margin-bottom: 8px;">🔗 Die wichtigsten Quell-Meldungen im Fokus:</strong>
    <ul style="margin: 0; padding-left: 18px; color: var(--text-muted); font-size: 0.85rem; line-height: 1.5;">
      <!-- Wähle 3 bis 5 der prägendsten Meldungen aus den Daten. Verlinke sie direkt mit ihrem Titel auf die Originalquelle (target="_blank" rel="noopener") und füge in 1-2 kurzen Sätzen hinzu, warum diese Meldung relevant ist. -->
      <li><a href="LINK" target="_blank" rel="noopener" style="color: var(--link-color); font-weight: 600; text-decoration: none;">ARTIKEL_TITEL</a> — Kurz-Einordnung / Teaser.</li>
    </ul>
  </div>

  <strong style="color: var(--text-main); font-size: 0.9rem; display: block; margin-bottom: 8px;">📊 Synthese & Lagebild:</strong>
  <ul style="margin: 0; padding-left: 18px; color: var(--text-muted); font-size: 0.88rem; line-height: 1.6;">
    <!-- Erstelle genau 3 prägnante, analysierende Stichpunkte zur Gesamtlage auf Basis der Artikel. Bilde wichtige Keywords fett (**Beispiel** -> <strong>Beispiel</strong>). -->
    <li><strong>Thema:</strong> Analyse...</li>
  </ul>
  
  <p style="text-align: right; margin: 12px 0 0 0; font-size: 0.72rem; color: #9ca3af;">Synthetisiert via Google Gemini Flash-Lite & Text-Teaser-Analyse</p>
</div>
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        briefing_html = response.text.strip()
        # Säubern von evtl. KI-Codeblock-Tags
        if briefing_html.startswith("```html"):
            briefing_html = briefing_html[7:]
        if briefing_html.startswith("```"):
            briefing_html = briefing_html[3:]
        if briefing_html.endswith("```"):
            briefing_html = briefing_html[:-3]
        briefing_html = briefing_html.strip()

        os.makedirs('generated', exist_ok=True)
        with open('generated/briefing.html', 'w', encoding='utf-8') as f:
            f.write(briefing_html)
        print("KI-Briefing erfolgreich generiert!")

    except Exception as e:
        print(f"KRITISCHER FEHLER BEI DER API-GENERIERUNG: {repr(e)}")
        raise e

def write_fallback(message):
    os.makedirs('generated', exist_ok=True)
    fallback_html = f"""
    <div style="background: var(--section-bg); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 18px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
      <h3 style="margin-top:0; color: var(--accent); font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
        🤖 KI-Briefing des Tages ({datetime.now().strftime('%d.%m.%Y')})
      </h3>
      <p style="color: var(--text-muted); font-size: 0.9rem; font-style: italic; margin: 0;">{message}</p>
      <p style="text-align: right; margin: 10px 0 0 0; font-size: 0.72rem; color: #9ca3af;">Synthetisiert via Google Gemini Flash-Lite</p>
    </div>
    """
    with open('generated/briefing.html', 'w', encoding='utf-8') as f:
        f.write(fallback_html)

if __name__ == "__main__":
    generate_briefing()
