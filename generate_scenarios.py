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
        category = (feed.get('category') or 'Allgemein').strip()
        feed_title = (feed.get('title') or '').strip()
        for item in feed.get('items', [])[:8]:
            title = (item.get('title') or '').replace('\n', ' ').strip()
            desc = (item.get('desc') or '').replace('\n', ' ').strip()
            if title:
                prefix = f"[{category} | {feed_title}]" if feed_title else f"[{category}]"
                entry = f"{prefix} {title}"
                if desc:
                    entry += f" – {desc}"
                items_summary.append(entry)

    if not items_summary:
        write_fallback("Keine aktuellen Meldungen für Szenarien vorhanden.")
        return

    prompt_content = "\n".join(items_summary[:80])
    today_str = datetime.now().strftime('%d.%m.%Y')

    prompt = f"""
Du bist ein strategischer Risiko-Analyst für komplexe Systemkrisen, Klimafolgen und Kaskadeneffekte (Red-Teaming).
Hier sind aktuelle Meldungen aus unseren Feeds über verschiedene Themenbereiche hinweg:

{prompt_content}

Deine Aufgabe: Erstelle **4 bis 5 plausible, aber noch nicht eingetretene Zweit- und Drittrundeneffekte (Kaskaden-Szenarien)**, die möglichst unterschiedliche Kernbereiche abdecken (z. B. Extremwetter & Naturkatastrophen, Klimawissenschaft & Kipppunkte, Wasser/Ozeane/Kryosphäre, Ökosysteme/Biodiversität, Infrastruktur/Energie/Rohstoffe, Wirtschaft/Landwirtschaft/Ernährung oder Politik/Recht/Akteure).

WICHTIG:
- Trenne strikt zwischen realem Auslöser (Fakt aus den Meldungen) und strategischer Hypothese (mögliche Dominoeffekte).
- Erfinde keine Fakten, Zahlen oder Ereignisse, die in den Meldungen nicht vorkommen.
- Vermeide reißerische Weltuntergangs-Rhetorik – bleibe analytisch, nüchtern und systemisch.
- Gib NUR reines HTML zurück (keine ```html ... ``` Codeblöcke).

HALTE DICH STRIKT AN FOLGENDE HTML-STRUKTUR:

<div class="scenario-card" style="border-left: 4px solid #d97706; background: #fffbeb; border-color: #f59e0b; color: #78350f;">
  <h3 style="color: #92400e; margin-bottom: 6px;">🧪 Experimentelles Red-Teaming &amp; Szenarien-Labor (Stand: {today_str})</h3>
  <p style="margin: 0; font-size: 0.88rem; line-height: 1.5; color: #78350f;">
    <em>Hinweis zur Einordnung:</em> Die folgenden Überlegungen sind <strong>bewusste KI-gestützte Hypothesen</strong> über mögliche Dominoeffekte auf Basis aktueller Meldungen. Sie stellen keine Fakten oder gesicherten Prognosen dar, sondern dienen dazu, blinde Flecken und systemische Wechselwirkungen frühzeitig sichtbar zu machen.
  </p>
</div>

<!-- Erstelle 4 bis 5 solcher Szenario-Karten für unterschiedliche Bereiche: -->
<div class="scenario-card">
  <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 12px;">
    <h3>🔮 [Prägnanter Titel des Szenarios]</h3>
    <div style="display: flex; flex-wrap: wrap; gap: 6px;">
      <span style="font-size: 0.75rem; background: var(--card-bg); border: 1px solid var(--border); padding: 2px 8px; border-radius: 12px; color: var(--accent); font-weight: 600;">Bereich: [z. B. Extremwetter &amp; Infrastruktur]</span>
      <span style="font-size: 0.75rem; background: var(--card-bg); border: 1px solid var(--border); padding: 2px 8px; border-radius: 12px; color: var(--text-muted);">Zeithorizont: [Kurzfristig / Mittelfristig]</span>
    </div>
  </div>

  <p style="margin: 0 0 10px 0; font-size: 0.88rem; color: var(--text-main);">
    <strong>📌 Realer Auslöser (Fakt):</strong> [Welche konkreten Meldungen aus den Feeds bilden den Ausgangspunkt?]
  </p>

  <p style="margin: 0 0 10px 0; font-size: 0.88rem; color: var(--text-muted); line-height: 1.5;">
    <strong>⛓️ Mögliche Kaskade (Hypothese):</strong> [Wie könnten diese Faktoren ineinandergreifen und welche Folgeeffekte in anderen Bereichen auslösen?]
  </p>

  <div style="background: var(--card-bg); padding: 10px 12px; border-radius: 6px; border-left: 3px solid #6b7280; font-size: 0.82rem; color: var(--text-muted);">
    <strong>🔭 Frühindikatoren (Worauf achten?):</strong> [Welche konkreten Signale oder Meldungen würden in den nächsten Wochen zeigen, dass sich das Szenario zuspitzt?]
  </div>
</div>
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
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
            write_fallback("Die KI-Antwort für die Szenarien war leer.")
            return

        os.makedirs('generated', exist_ok=True)
        with open('generated/scenarios_content.html', 'w', encoding='utf-8') as f:
            f.write(html_out)
        print("Szenarien erfolgreich generiert!")

    except Exception as e:
        print(f"Fehler bei der Szenarien-Generierung: {repr(e)}")
        raise e


def write_fallback(message):
    os.makedirs('generated', exist_ok=True)
    with open('generated/scenarios_content.html', 'w', encoding='utf-8') as f:
        f.write(f'<div class="scenario-card"><p class="no-data" style="text-align: center;">{message}</p></div>')


if __name__ == "__main__":
    generate_scenarios()
