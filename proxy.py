from flask import Flask, jsonify, render_template_string, request
import requests, time

app = Flask(__name__)

ECONOMY_URL = "https://economy.roblox.com/v2/assets/{assetId}/details"
cache = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

def fetch_stats(asset_id: str):
    now = time.time()
    entry = cache.get(asset_id, {"data": None, "last_update": 0})

    if now - entry["last_update"] > 10 or not entry["data"]:
        try:
            url = ECONOMY_URL.format(assetId=asset_id)
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            j = r.json()

            name = j.get("Name")
            sales = j.get("Sales")
            price = j.get("PriceInRobux")

            entry["data"] = {
                "assetId": asset_id,
                "name": name,
                "sales": sales,
                "price": price
            }
        except Exception as e:
            entry["data"] = {"assetId": asset_id, "error": str(e)}

        entry["last_update"] = now
        cache[asset_id] = entry

    return entry["data"]

@app.route("/ugc")
def ugc_json():
    asset_id = request.args.get("assetId", "116103195460500")
    return jsonify(fetch_stats(asset_id))

@app.route("/")
def overlay():
    asset_id = request.args.get("assetId", "116103195460500")
    size = request.args.get("size", "48")
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        body {{
          background: transparent;
          color: white;
          font-size: {size}px;
          font-family: Arial, sans-serif;
          text-align: center;
        }}
        .flash {{ animation: flash 0.6s ease; }}
        @keyframes flash {{
          0% {{ transform: scale(1); }}
          40% {{ transform: scale(1.1); }}
          100% {{ transform: scale(1); }}
        }}
      </style>
    </head>
    <body>
      <div id="ugc">Loading…</div>
      <script>
        let prevSales = null;
        async function update() {{
          try {{
            const res = await fetch("/ugc?assetId={asset_id}&_=" + Date.now());
            const data = await res.json();
            const el = document.getElementById("ugc");

            if (data.error) {{
              el.innerText = "Error: " + data.error;
              return;
            }}
            el.innerText = data.name + "\\nSales: " + data.sales + " | Price: " + data.price + " R$";

            if (prevSales !== null && typeof data.sales === "number" && data.sales > prevSales) {{
              el.classList.remove("flash");
              void el.offsetWidth;
              el.classList.add("flash");
            }}
            prevSales = data.sales;
          }} catch (e) {{
            document.getElementById("ugc").innerText = "Fetch error";
          }}
        }}
        update();
        setInterval(update, 10000);
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
