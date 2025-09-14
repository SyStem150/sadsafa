from flask import Flask, jsonify, render_template_string, request
import requests, time

app = Flask(__name__)

CATALOG_DETAILS_URL = "https://catalog.roblox.com/v1/catalog/items/details"
cache = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; UGCOverlay/1.0)",
    "Accept": "application/json"
}

def fetch_stats(asset_id: str):
    now = time.time()
    entry = cache.get(asset_id, {"data": None, "last_update": 0})

    if now - entry["last_update"] > 10 or not entry["data"]:
        try:
            payload = {"items": [{"itemType": "Asset", "id": int(asset_id)}]}
            r = requests.post(CATALOG_DETAILS_URL, json=payload, headers=HEADERS, timeout=10)
            r.raise_for_status()
            j = r.json()

            if "data" in j and j["data"]:
                item = j["data"][0]
                name = item.get("name")
                total = item.get("totalQuantity")
                left = item.get("unitsAvailableForConsumption")
                sold = (total - left) if isinstance(total, int) and isinstance(left, int) else None

                entry["data"] = {
                    "assetId": asset_id,
                    "name": name,
                    "copies_left": left,
                    "total_copies": total,
                    "sold": sold
                }
            else:
                entry["data"] = {"assetId": asset_id, "error": "No data from Roblox API"}
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
        let prevLeft = null;
        async function update() {{
          try {{
            const res = await fetch("/ugc?assetId={asset_id}&_=" + Date.now());
            const data = await res.json();
            const el = document.getElementById("ugc");

            if (data.error) {{
              el.innerText = "Error: " + data.error;
              return;
            }}
            el.innerText = data.name + "\\nCopies Left: " + data.copies_left + "/" + data.total_copies;

            if (prevLeft !== null && typeof data.copies_left === "number" && data.copies_left < prevLeft) {{
              el.classList.remove("flash");
              void el.offsetWidth; // restart animation
              el.classList.add("flash");
            }}
            prevLeft = data.copies_left;
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
