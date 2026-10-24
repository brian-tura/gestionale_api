import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CDSE_CLIENT_ID')
CLIENT_SECRET = os.getenv('CDSE_CLIENT_SECRET')

# Sostituisci con le coordinate reali del tuo apiario
LAT = 44.2227  # Metti la latitudine del tuo apiario
LON = 12.0407  # Metti la longitudine del tuo apiario

def get_token():
    """Richiede il token di accesso OAuth2 a Copernicus"""
    url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    res = requests.post(url, data=payload)
    if res.status_code != 200:
        print(f"Errore autenticazione: {res.status_code} - {res.text}")
        exit()
    return res.json()["access_token"]

def get_ndvi(token, lat, lon):
    """Interroga la Statistical API di Sentinel-2 per l'indice NDVI"""
    # Definisce un'area di ~1.5 km attorno all'apiario
    delta = 0.015
    bbox = [lon - delta, lat - delta, lon + delta, lat + delta]
    
    # Intervallo: ultimi 10 giorni
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
                "dataFilter": {
                    "maxCloudCoverage": 60
                }
            }]
        },
        "aggregation": {
            "timeRange": {"from": da_data, "to": a_data},
            "aggregationInterval": {"of": "P1D"},
            "evalscript": evalscript
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
    res = requests.post(url, json=payload, headers=headers)
    return res.json()

if __name__ == "__main__":
    print("Autenticazione con Copernicus...")
    token = get_token()
    print("Token ottenuto con successo!")

    print("Calcolo vigore flora (NDVI) tramite Sentinel-2...")
    risposta = get_ndvi(token, LAT, LON)
    print("\nRisultato:")
    print(risposta)