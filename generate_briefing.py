import os
import json
import datetime
from google import genai

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Hinweis: GEMINI_API_KEY ist nicht gesetzt. Überspringe KI-Briefing.")
        return

    # 1. Frische Feed-Daten aus der data.json lesen
    data_path = "data.json"
    if not os.path.exists(data_path):
        print("Keine data.json gefunden. Bitte erst fetcher.py ausführen.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        dashboard_data = json.load(f)

    # Schlagzeilen für den Prompt aufbereiten (max. 30 aktuellste Headlines)
    headlines = []
    feeds = dashboard_data.get("feeds", [])
    for feed in feeds:
        for item in feed.get("items", [])[:3]: # Die Top 3 pro Kategorie reichen für den Überblick
            headlines.append(f"- [{feed.get('title')}] {item.get('title')}")

    headlines_text = "\n".join(headlines[:40]) # Deckel bei 40 Schlagzeilen

    today = datetime.datetime.now().strftime("%d.%m.%Y")
    
    prompt = f"""
    Du bist ein präziser Klima-Analyst. Hier sind die aktuellsten Schlagzeilen unseres Monitoring-Dashboards vom {today}:

    {headlines_text}

    Analysiere diese Meldungen und erstelle ein kompaktes, professionelles 'Tages-Briefing' (genau 3 prägende Kernerkenntnisse) für das Klima-Dashboard.
    Fokussiere dich auf Extreme Wetterereignisse, politische Entwicklungen (wie COP-Konferenzen) und wissenschaftliche Trends.
    Formatiere das Ergebnis in sauberem HTML (nutze <ul>, <li>, <strong>), ohne <html>- oder <body>-Tags, direkt einbettbar.
    """

    client = genai.Client(api_key=api_key)

    print("Sende Anfrage an Gemini (gemini-3.1-flash-lite)...")
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )
        ai_content = response.text
    except Exception as e:
        print(f"Fehler bei der API-Abfrage: {e}")
        # Fallback-HTML erzeugen, damit der Build nicht abbricht
        ai_content = "<p><em>Das KI-Briefing ist aufgrund hoher Serverlast aktuell nicht verfügbar. Updates folgen beim nächsten Lauf.</em></p>"

    # 2. Ausgabedatei schreiben
    output_html = f"""
    <div class="ai-briefing-box" style="background: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid #8b0000; padding: 15px; border-radius: 8px; margin-bottom: 25px;">
        <h3 style="margin-top:0; color: #8b0000; font-size: 1.1rem;">🤖 KI-Briefing des Tages ({today})</h3>
        <div style="font-size: 0.9rem; color: #374151;">
            {ai_content}
        </div>
        <p style="margin-bottom:0; font-size: 0.75rem; color: #9ca3af; text-align: right;"><small>Synthetisiert via Google Gemini Flash-Lite</small></p>
    </div>
    """

    os.makedirs("generated", exist_ok=True)
    with open("generated/briefing.html", "w", encoding="utf-8") as f:
        f.write(output_html)
    
    print("Briefing erfolgreich unter generated/briefing.html gespeichert!")

if __name__ == "__main__":
    main()

