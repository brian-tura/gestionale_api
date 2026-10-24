import os
import requests
from datetime import datetime, timedelta, timezone

CLIENT_ID = os.getenv('CDSE_CLIENT_ID')
CLIENT_SECRET = os.getenv('CDSE_CLIENT_SECRET')

def get_copernicus_token():
    """Richiede il token temporaneo OAuth2 a Copernicus"""
    try:
        url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        res = requests.post(url, data=payload, timeout=5)
        if res.status_code == 200:
            return res.json().get("access_token")
    except Exception as e:
        print(f"Errore recupero token Copernicus: {e}")
    return None

def calcola_vigore_flora(lat, lon):
    """
    Interroga Sentinel-2 (Statistical API) e calcola l'indice NDVI
    negli ultimi 10 giorni sul raggio dell'apiario.
    """
    flora_default = {'pct': 0, 'stato': "Dato non disp.", 'colore': "text-slate-400", 'bg': "bg-slate-800"}

    token = get_copernicus_token()
    if not token:
        return flora_default

    try:
        delta = 0.015
        bbox = [float(lon) - delta, float(lat) - delta, float(lon) + delta, float(lat) + delta]

        oggi = datetime.now(timezone.utc)
        da_data = (oggi - timedelta(days=10)).strftime("%Y-%m-%dT00:00:00Z")
        a_data = oggi.strftime("%Y-%m-%dT23:59:59Z")

        evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: [{ bands: ["B04", "B08", "dataMask"] }],
            output: [
              { id: "default", bands: 1, sampleType: "FLOAT32" },
              { id: "dataMask", bands: 1 }
            ]
          };
        }
        function evaluatePixel(samples) {
          let ndvi = (samples.B08 - samples.B04) / (samples.B08 + samples.B04);
          return {
            default: [ndvi],
            dataMask: [samples.dataMask]
          };
        }
        """

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {"maxCloudCoverage": 80}
                }]
            },
            "aggregation": {
                "timeRange": {"from": da_data, "to": a_data},
                "aggregationInterval": {"of": "P1D"},
                "width": 256,
                "height": 256,
                "evalscript": evalscript
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
        res = requests.post(url, json=payload, headers=headers, timeout=10).json()

        # Cerchiamo l'ultimo passaggio valido del satellite a ritroso
        data_list = res.get("data", [])
        ndvi_trovato = None

        for blocco in reversed(data_list):
            stats = blocco["outputs"]["default"]["bands"]["B0"]["stats"]
            if stats.get("mean") is not None:
                ndvi_trovato = stats["mean"]
                break

        if ndvi_trovato is not None:
            pct = max(0, min(100, round(ndvi_trovato * 100)))

            # Classificazione dello stato vegetativo
            if pct >= 65:
                return {'pct': pct, 'stato': "Pascolo Ottimo", 'colore': "text-emerald-400", 'bg': "bg-emerald-950"}
            elif pct >= 40:
                return {'pct': pct, 'stato': "Vegetazione Buona", 'colore': "text-green-400", 'bg': "bg-green-950"}
            elif pct >= 25:
                return {'pct': pct, 'stato': "Moderata / Autunnale", 'colore': "text-amber-400", 'bg': "bg-amber-950"}
            else:
                return {'pct': pct, 'stato': "Flora Scarsa / Riposo", 'colore': "text-rose-400", 'bg': "bg-rose-950"}

    except Exception as e:
        print(f"Errore calcolo satellite: {e}")

    return flora_default