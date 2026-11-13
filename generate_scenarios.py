import json
import os
from datetime import datetime
from google import genai

def generate_scenarios():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Fehler: GEMINI_API_KEY ist nicht gesetzt.")
        write_fallback("Kein API-Schlüssel konfiguriert.")
        return

    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden von data.json: {e}")
        write_fallback("Datenbasis konnte nicht geladen werden.")
        return

    feeds = data if isinstance(data, list) else data.get('feeds', [])
    
    items_summary = []
    for feed in feeds:
        category = feed.get('category', 'Allgemein')
        for item in feed.get('items', [])[:8]:
            title = item.get('title', '')
            desc = item.get('desc', '')
            if title:
                entry = f"[{category}] {title}"
                if desc:
                    entry += f" – {desc}"
                items_summary.append(entry)

    if not items_summary:
        write_fallback("Keine aktuellen Meldungen für Szenarien vorhanden.")
        return

    prompt_content = "\n".join(items_summary[:55])

    prompt = f"""
Du bist ein strategischer Risiko-Analyst für komplexe Systemkrisen, Klimafolgen und Kaskadeneffekte (Red-Teaming).
Hier sind die aktuellen Fakten-Meldungen aus unseren Feeds:

{prompt_content}

Deine Aufgabe: Identifiziere 3 bis 4 plausible, aber noch nicht eingetretene **Zweit- und Drittrundeneffekte (Kaskaden-Szenarien)**, die sich aus der Kombination dieser Meldungen in den kommenden Wochen oder Monaten ergeben könnten. 
WICHTIG: Trenne strikt zwischen dem realen Auslöser (Fakt) und deiner strategischen Hypothese (Spekulation). Vermeide reißerische Weltuntergangs-Rhetorik – bleibe analytisch, kühl und systemisch.

HALTE DICH STRIKT AN FOLGENDE HTML-STRUKTUR (keine ```html Codeblocks):

<div style="background: #fffbeb; border: 1px solid #f59e0b; border-left: 4px solid #d97706; border-radius: 8px; padding: 16px; margin-bottom: 25px; color: #78350f; font-size: 0.88rem; line-height: 1.5;">
  <strong>🧪 Experimentelles Red-Teaming & Szenarien-Labor (Stand: {datetime.now().strftime('%d.%m.%Y')})</strong><br>
  <em>Hinweis zur Einordnung:</em> Die folgenden Überlegungen sind <strong>bewusste KI-gestützte Hypothesen</strong> über mögliche Dominoeffekte auf Basis aktueller Meldungen. Sie stellen keine Fakten oder gesicherten Prognosen dar, sondern dienen dazu, blinde Flecken und systemische Wechselwirkungen frühzeitig sichtbar zu machen.
</div>

<!-- Erstelle 3 bis 4 solcher Karten: -->
<div class="scenario-card" style="background: var(--section-bg); border: 1px solid var(--border); border-radius: 12px; padding: 18px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 12px;">
    <h3 style="margin: 0; font-size: 1.1rem; color: var(--accent);">🔮 [Prägnanter Titel des Szenarios]</h3>
    <span style="font-size: 0.75rem; background: var(--card-bg); border: 1px solid var(--border); padding: 2px 8px; border-radius: 12px; color: var(--text-muted);">Zeithorizont: [z.B. Kurzfristig / Mittelfristig]</span>
  </div>
  
  <p style="margin: 0 0 10px 0; font-size: 0.88rem; color: var(--text-main);">
    <strong>📌 Realer Auslöser (Fakt):</strong> [Welche konkreten Meldungen aus den Feeds bilden den Ausgangspunkt?]
  </p>
  
  <p style="margin: 0 0 10px 0; font-size: 0.88rem; color: var(--text-muted); line-height: 1.5;">
    <strong>⛓️ Mögliche Kaskade (Hypothese):</strong> [Wie könnten diese Faktoren ineinandergreifen und welche unerwarteten Nebenwirkungen auf Wirtschaft, Gesellschaft oder Infrastruktur auslösen?]
  </p>

  <div style="background: var(--card-bg); padding: 10px 12px; border-radius: 6px; border-left: 3px solid #6b7280; font-size: 0.82rem; color: var(--text-muted);">
    <strong>🔭 Frühindikatoren (Worauf achten?):</strong> [Welche konkreten Schlagzeilen oder Signale würden in den nächsten Wochen zeigen, dass dieses Szenario tatsächlich eintritt?]
  </div>
</div>
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
        )
        
        html_out = response.text.strip()
        if html_out.startswith("```html"):
            html_out = html_out[7:]
        if html_out.startswith("```"):
            html_out = html_out[3:]
        if html_out.endswith("```"):
            html_out = html_out[:-3]

        os.makedirs('generated', exist_ok=True)
        with open('generated/scenarios_content.html', 'w', encoding='utf-8') as f:
            f.write(html_out.strip())
        print("Szenarien erfolgreich generiert!")

    except Exception as e:
        print(f"Fehler bei der Szenarien-Generierung: {repr(e)}")
        raise e

def write_fallback(message):
    os.makedirs('generated', exist_ok=True)
    with open('generated/scenarios_content.html', 'w', encoding='utf-8') as f:
        f.write(f'<p style="color: var(--text-muted); text-align: center;">{message}</p>')

if __name__ == "__main__":
    generate_scenarios()
