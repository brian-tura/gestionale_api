# 🐝 BeeManager — Gestionale Personale per Apiario

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Copernicus](https://img.shields.io/badge/ESA_Copernicus-Sentinel--2-003399?style=for-the-badge)

Un progetto personale sviluppato in **Python e Django** per supportare il lavoro pratico sul campo nella gestione delle arnie e delle colonie. 

---

## La storia dietro al progetto

Da tre anni gestisco una piccola attività di apicoltura. Lavorando sul campo, mi sono reso conto di quanto tempo si perde tra fogli volanti, quaderni di campo che si rovinano con la propoli e controlli meteo sparsi su app diverse prima di decidere se aprire o meno le casse.

Essendo appassionato di programmazione e avendo un percorso universitario scientifico (studi in astronomia e analisi dati), ho deciso di sviluppare da zero una web application su misura per le mie reali esigenze operative:
* Sapere esattamente **quali arnie sono attive e quali sono vuote in magazzino**.
* Avere sott'occhio il **microclima reale dell'apiario** (temperatura, vento, umidità e pioggia) tramite coordinate GPS.
* Monitorare il **vigore della flora circostante** tramite i dati satellitari europei **Copernicus Sentinel-2**, calcolando l'indice NDVI per capire lo stato del pascolo delle api senza dover perlustrare chilometri di campagna a piedi.

---

## Cosa fa l'applicazione

* **Gestione Casse & Colonie:** Suddivisione rapida tra arnie operative e materiale a magazzino, con storico degli interventi e trattamenti sanitari.
* **Meteo sul Campo (Open-Meteo API):** Chiamate API basate sulle coordinate GPS specifiche dell'apiario, con previsioni a 3 giorni per pianificare le visite nei momenti ideali (evitando giornate con troppo vento o pioggia).
* **Telemetria Satellitare (ESA Copernicus Sentinel-2):** Connessione tramite protocollo OAuth2 alle *Statistical API* dell'Agenzia Spaziale Europea. Il sistema estrae una matrice di pixel attorno all'apiario e calcola l'indice **NDVI** (Normalized Difference Vegetation Index), restituendo una stima percentuale del vigore vegetativo e delle fioriture.
* **Interfaccia Mobile-First:** Realizzata con Tailwind CSS in tema scuro, pensata per essere usata comodamente dallo smartphone direttamente all'aperto, con pulsanti grandi e contrasti elevati.

---

## Stack Tecnologico

* **Backend:** Python, Django 5
* **Database:** MySQL
* **Frontend:** Django Templates, Tailwind CSS, JavaScript vanilla
* **Integrazioni Esterne:** 
  * API Open-Meteo (dati atmosferici orari e giornalieri)
  * Copernicus Data Space Ecosystem (Sentinel-2 L2A, elaborazione radiometrica NDVI)
* **Sicurezza & Configurazione:** `python-dotenv` per la gestione delle chiavi e credenziali protette.

---

## Schermata
<img width="1224" height="569" alt="image" src="https://github.com/user-attachments/assets/8c03dbff-c2ad-4e89-a91f-3a5ffe1f57b9" />

---

## Come avviarlo in locale

### 1. Clona il repository
```
git clone https://github.com/tuo-username/gestionale-apicoltura.git
cd gestionale-apicoltura
```

2. Crea e attiva l'ambiente virtuale
```
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / Mac
python3 -m venv .venv
source .venv/bin/activate
```

3. Installa le dipendenze
```
pip install -r requirements.txt
```
4. Configura il file .env
Crea un file chiamato .env partendo dal template .env.example:
```
SECRET_KEY_DJANGO=la_tua_secret_key
DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=

DB_NAME=apicoltura_prj
DB_USER=root
DB_PASSWORD=tua_password
DB_HOST=localhost
DB_PORT=3306

CDSE_CLIENT_ID=tuo_client_id_copernicus
CDSE_CLIENT_SECRET=tuo_client_secret_copernicus
```

5. Applica le migrazioni e avvia
```
python manage.py migrate
python manage.py runserver
```

Apri il browser su http://127.0.0.1:8000/.

# Sviluppi futuri
Il progetto è in continua evoluzione man mano che emergono nuove esigenze in apiario.

# 👤 Autore
* Brian Tura
* Apicoltore & Sviluppatore Junior
* GitHub: https://github.com/brian-tura
* LinkedIn: www.linkedin.com/in/brian-tura
* Email: b.tura2002@gmail.com
