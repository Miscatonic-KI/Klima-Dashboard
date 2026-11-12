import json
import os
from datetime import datetime, date, timedelta

def generate_evolution_page():
    # 1. data.json einlesen
    if not os.path.exists('data.json'):
        print("Fehler: data.json nicht gefunden. Bitte erst den Fetcher laufen lassen.")
        return

    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden von data.json: {e}")
        return

    meta = data.get("meta", {})
    feeds = data.get("feeds", [])

    # 2. HTML-Struktur aufbauen
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crisis-Tracker | Themen-Entwicklung</title>
    <style>
        :root {{
            --bg-color: #f3f4f6;
            --section-bg: #ffffff;
            --card-bg: #f9fafb;
            --card-hover: #f3f4f6;
            --text-main: #111827;
            --text-muted: #4b5563;
            --accent: #8b0000;
            --border: #e5e7eb;
            --link-color: #990000;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 30px;
        }}

        h1 {{
            color: var(--accent);
            font-size: 1.6rem;
            margin-top: 0;
            margin-bottom: 8px;
        }}

        .meta {{
            color: var(--text-muted);
            font-size: 0.85rem;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 10px;
            margin-bottom: 25px;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 15px;
            font-weight: 600;
            color: var(--accent);
            text-decoration: none;
            background: var(--section-bg);
            padding: 5px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}

        .evolution-card {{
            background: var(--section-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        .evolution-card h3 {{
            margin-top: 0;
            color: var(--text-main);
            font-size: 1.1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .cat-tag {{
            font-size: 0.75rem;
            background: #f3f4f6;
            color: var(--text-muted);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: normal;
        }}

        .section-title {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            margin: 12px 0 6px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .latest-item {{
            font-size: 0.9rem;
            background: var(--card-bg);
            padding: 10px 12px;
            border-radius: 6px;
            border-left: 3px solid var(--accent);
            margin-bottom: 12px;
        }}

        .latest-item a {{
            color: var(--link-color);
            text-decoration: none;
            font-weight: 600;
        }}

        .latest-item a:hover {{
            text-decoration: underline;
        }}

        .latest-time {{
            font-size: 0.75rem;
            color: var(--text-muted);
            display: block;
            margin-bottom: 3px;
        }}

        /* Mini-Balkendiagramm CSS */
        .chart-container {{
            display: flex;
            align-items: flex-end;
            gap: 6px;
            height: 60px;
            background: var(--card-bg);
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            margin-top: 8px;
        }}

        .chart-bar-wrapper {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100%;
            justify-content: flex-end;
        }}

        .chart-bar {{
            width: 100%;
            background-color: var(--accent);
            border-radius: 2px 2px 0 0;
            min-height: 3px;
            flex-shrink: 0;
            flex-grow: 0;
        }}

        .chart-label {{
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-top: 4px;
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Zurück zum Haupt-Dashboard</a>
        <header>
            <h1>📈 Themen-Entwicklung & Verlauf</h1>
            <p style="color: var(--text-muted); margin: 0;">Historische Aktivität und zeitliche Analyse der beobachteten Krisen-Signale</p>
        </header>
        <div class="meta">
            Datenstand: <strong>{meta.get('last_updated', 'Unbekannt')}</strong>
        </div>
    """

    for feed in feeds:
        title = feed.get("title", "Unbenannter Feed")
        category = feed.get("category", "Allgemein")
        items = feed.get("items", [])

        # 1. Letzte neue Meldung ermitteln
        latest_html = "<em>Keine Meldungen vorhanden.</em>"
        if items:
            first_item = items[0]
            raw_time = first_item.get("added_at", "")
            time_str = "Neu eingegangen"
            if raw_time:
                try:
                    dt = datetime.fromisoformat(raw_time)
                    time_str = dt.strftime("%d.%m.%Y, %H:%M Uhr")
                except Exception:
                    pass
            
            latest_html = f"""
                <span class="latest-time">⏱️ {time_str}</span>
                <a href="{first_item.get('link', '#')}" target="_blank" rel="noopener">{first_item.get('title', '')}</a>
            """

        # 2. Aktivität nach Tagen gruppieren (letzte 7 Tage)
        day_counts = {}
        for item in items:
            raw_time = item.get("added_at", "")
            if raw_time:
                try:
                    dt = datetime.fromisoformat(raw_time)
                    day_key = dt.strftime("%Y-%m-%d")
                    day_counts[day_key] = day_counts.get(day_key, 0) + 1
                except Exception:
                    pass

        today = date.today()
        max_count = 1
        last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        counts_list = []
        for d in last_7_days:
            d_str = d.strftime("%Y-%m-%d")
            c = day_counts.get(d_str, 0)
            counts_list.append((d.strftime("%d.%m."), c))
            if c > max_count:
                max_count = c

        bars_markup = ""
        for label, count in counts_list:
            # Maximale Balkenhöhe auf 35px skaliert
            height_px = int((count / max_count) * 35) if max_count > 0 else 3
            bars_markup += f"""
                <div class="chart-bar-wrapper" title="{count} Meldungen am {label}">
                    <span style="font-size: 0.65rem; color: var(--text-muted); margin-bottom: 2px;">{count if count > 0 else ''}</span>
                    <div class="chart-bar" style="height: {height_px}px;"></div>
                    <span class="chart-label">{label}</span>
                </div>
            """

        chart_block = f"""
            <div class="section-title">📊 Aktivität (Meldungen pro Tag)</div>
            <div class="chart-container">
                {bars_markup}
            </div>
        """

        # 3. Verlauf (Liste der letzten Meldungen)
        verlauf_items = items[:5]
        verlauf_list = ""
        if verlauf_items:
            for vi in verlauf_items:
                verlauf_list += f"<li style='margin-bottom: 4px;'><a href='{vi.get('link', '#')}' target='_blank' rel='noopener' style='color: var(--link-color); text-decoration: none;'>{vi.get('title', '')}</a></li>"
        else:
            verlauf_list = "<li>Keine Historie vorhanden.</li>"

        verlauf_block = f"""
            <div class="section-title">📜 Verlauf (Auszug neuester Meldungen)</div>
            <ul style="margin: 0; padding-left: 18px; font-size: 0.85rem; color: var(--text-muted);">
                {verlauf_list}
            </ul>
        """

        html_content += f"""
        <div class="evolution-card">
            <h3>
              <span>{title}</span>
              <span class="cat-tag">{category}</span>
            </h3>
            
            <div class="section-title">⚡ Letzte neue Meldung</div>
            <div class="latest-item">
                {latest_html}
            </div>

            {chart_block}
            {verlauf_block}
        </div>
        """

    html_content += """
    </div>
</body>
</html>
"""

    with open('evolution.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("evolution.html erfolgreich generiert!")

if __name__ == '__main__':
    generate_evolution_page()
