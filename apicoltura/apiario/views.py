import json
import calendar
from datetime import date, timedelta, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import ExtractYear
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests

from .models import Apiario, Arnia, Famiglia, Regina, Visita, Trattamento, Raccolto, EventoCalendario, Scorta
from .forms import ArniaForm, FamigliaForm, VisitaForm, ReginaForm, TrattamentoForm, RaccoltoForm, EventoCalendarioForm, ApiarioForm
from django.db.models.functions import Length
from .satellite import calcola_vigore_flora

def dashboard_view(request):
    apiari = Apiario.objects.all()
    return render(request, 'apiario/dashboard.html', {'apiari': apiari})

def inventario_view(request):
    # Forza la creazione delle categorie che mancano nel database
    for cat_slug, cat_nome in Scorta.CATEGORIA_CHOICES:
        Scorta.objects.get_or_create(categoria=cat_slug)
    
    # Prende solo le scorte che sono effettivamente definite nel modello attuale
    scorte = Scorta.objects.filter(
        categoria__in=[c[0] for c in Scorta.CATEGORIA_CHOICES]
    ).order_by('categoria')
    
    return render(request, 'apiario/inventario.html', {'scorte': scorte})

@csrf_exempt
def aggiorna_scorta_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        scorta = get_object_or_404(Scorta, pk=data['id'])
        scorta.quantita += data['delta']
        if scorta.quantita < 0: scorta.quantita = 0
        scorta.save()
        return JsonResponse({'nuova_qty': scorta.quantita})

@csrf_exempt
def imposta_scorta_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            scorta = get_object_or_404(Scorta, pk=data['id'])
            # Prendiamo il valore esatto inviato dall'utente
            nuovo_valore = int(data['valore'])
            scorta.quantita = max(0, nuovo_valore) # Evitiamo negativi
            scorta.save()
            return JsonResponse({'status': 'ok', 'nuova_qty': scorta.quantita})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def _get_bee_icon(code):
                # 00-02: Sereno
                if code in [0, 1, 2]:
                    return '☀️'
                
                # 03: Coperto / Nuvole in sviluppo
                if code == 3:
                    return '☁️'
                
                # 04-12, 28, 30-35, 40-49: Visibilità ridotta, Nebbia, Polvere
                if (4 <= code <= 12) or code == 28 or (30 <= code <= 35) or (40 <= code <= 49):
                    return '🌫️'
                
                # 13-16: Fenomeni distanti o vicini senza precipitazione immediata
                if 13 <= code <= 16:
                    return '🌤️'
                
                # 17-19, 29, 95, 97, 98: Temporale / Tempesta (senza grandine)
                if code in [17, 18, 19, 29, 95, 97, 98]:
                    return '🌩️'
                
                # 20-21, 24, 25, 50-55, 58, 59: Pioggerella / Pioggia leggera o intermittente
                if code in [20, 21, 24, 25, 50, 51, 52, 53, 54, 55, 58, 59]:
                    return '🌦️'
                
                # 56, 57, 66, 67, 83, 84: Pioggia o pioggerella GELATA (Mix Ghiaccio/Neve)
                if code in [56, 57, 66, 67, 83, 84]:
                    return '🌧️❄️'
                
                # 60-65, 68, 69, 80-82, 91, 92: Pioggia continua, forte o rovesci
                if (60 <= code <= 65) or code in [68, 69, 80, 81, 82, 91, 92]:
                    return '🌧️'
                
                # 22, 23, 26, 36-39, 70-79, 93, 94: Neve o granelli di neve
                if code in [22, 23, 26] or (36 <= code <= 39) or (70 <= code <= 79) or code in [93, 94]:
                    return '🌨️'
                
                # 85, 86: Rovesci di neve
                if code in [85, 86]:
                    return '❄️⛈️'
                
                # 27, 87-90, 96, 99: Grandine (associata a rovesci o temporali)
                if code == 27 or (87 <= code <= 90) or code in [96, 99]:
                    return '⛈️❄️'
                
                return '❓' # Default per codici non previsti

def lista_arnie_view(request, apiario_id):
    apiario = get_object_or_404(Apiario, pk=apiario_id)
    
    info_meteo = {'temperatura': "--", 'citta': apiario.luogo or "Apiario", 'umidita': "--", 'vento': "--"}
    previsioni = []
    flora = {'pct': 0, 'stato': "N/D", 'colore': "text-slate-500", 'bg': "bg-slate-700"}
    
    if apiario.latitudine and apiario.longitudine:
        lat, lon = apiario.latitudine, apiario.longitudine
        try:
            # 1. API METEO (Oraria per pioggia, Giornaliera per il resto)
            meteo_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"current=temperature_2m,relative_humidity_2m,wind_speed_10m&"
                f"hourly=precipitation_probability&"
                f"daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,wind_speed_10m_max,relative_humidity_2m_max&"
                f"timezone=auto&forecast_days=4&models=icon_seamless"
            )
            res = requests.get(meteo_url, timeout=5).json()

            # Dati Attuali
            info_meteo['temperatura'] = round(res['current']['temperature_2m'])
            info_meteo['umidita'] = res['current']['relative_humidity_2m']
            info_meteo['vento'] = round(res['current']['wind_speed_10m'])

            # Calcolo Previsioni (Oggi, Domani, Dopodomani)
            for i in range(0, 3):
                alba = datetime.fromisoformat(res['daily']['sunrise'][i])
                tramonto = datetime.fromisoformat(res['daily']['sunset'][i])
                
                # Media pioggia ore di luce
                pioggia_ore = res['hourly']['precipitation_probability'][i*24 : (i+1)*24]
                ore_giorno = res['hourly']['time'][i*24 : (i+1)*24]
                piogge_diurne = [p for t, p in zip(ore_giorno, pioggia_ore) if alba <= datetime.fromisoformat(t) <= tramonto]
                media_pioggia = sum(piogge_diurne) / len(piogge_diurne) if piogge_diurne else 0

                data_vera = datetime.strptime(res['daily']['time'][i], '%Y-%m-%d').date()
                previsioni.append({
                    'data': data_vera,
                    'icona': _get_bee_icon(res['daily']['weather_code'][i]),
                    'max': round(res['daily']['temperature_2m_max'][i]),
                    'min': round(res['daily']['temperature_2m_min'][i]),
                    'pioggia': round(media_pioggia),
                    'vento': round(res['daily']['wind_speed_10m_max'][i]),
                    'umidita': res['daily']['relative_humidity_2m_max'][i],
                })

            flora = calcola_vigore_flora(lat, lon)

            # 3. API CITTA
            geo_url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=it"
            geo_res = requests.get(geo_url, timeout=2).json()
            info_meteo['citta'] = geo_res.get('city') or geo_res.get('locality') or apiario.luogo

        except Exception as e: print(f"Errore: {e}")

    # Filtri Arnie
    stato_filtro = request.GET.get('stato', 'occupata')
    arnie = Arnia.objects.filter(apiario=apiario).order_by(Length('codice_identificativo'), 'codice_identificativo')
    if stato_filtro == 'magazzino':
        arnie = arnie.filter(stato='vuota')
    else:
        arnie = arnie.filter(stato='occupata')

    return render(request, 'apiario/lista_arnie.html', {
        'apiario': apiario,
        'arnie': arnie,
        'stato_filtro': stato_filtro,
        'info_meteo': info_meteo,
        'previsioni': previsioni,
        'flora': flora
    })

def dettagli_famiglia_view(request, famiglia_id):
    famiglia = get_object_or_404(Famiglia, pk=famiglia_id)
    regina = Regina.objects.filter(famiglia=famiglia).exclude(stato='morta').last()
    
    # 1. Colore Regina (rimane uguale)
    regina_color_class = "bg-slate-200 text-slate-700"
    if regina:
        ultima_cifra = regina.anno_nascita % 10
        if ultima_cifra in [1, 6]: regina_color_class = "bg-white text-slate-800 border border-slate-300"
        elif ultima_cifra in [2, 7]: regina_color_class = "bg-yellow-400 text-slate-900"
        elif ultima_cifra in [3, 8]: regina_color_class = "bg-red-600 text-white"
        elif ultima_cifra in [4, 9]: regina_color_class = "bg-green-600 text-white"
        elif ultima_cifra in [5, 0]: regina_color_class = "bg-blue-600 text-white"

    # 2. Logica Telai (rimane uguale)
    numero_telai = 6 if famiglia.arnia.categoria == 'portasciami' else 10
    
    # --- NUOVA LOGICA VISITE ---
    # Prendiamo tutte le visite di questa famiglia
    tutte_le_visite = Visita.objects.filter(famiglia=famiglia).order_by('-data_visita', '-id')
    
    # A. ULTIMA VISITA
    ultima_visita = tutte_le_visite.first()
    
    # B. VISITE PINNED (escludiamo l'ultima se è già pinned per non vederla due volte)
    visite_pinned = tutte_le_visite.filter(is_pinned=True)
    if ultima_visita:
        visite_pinned = visite_pinned.exclude(id=ultima_visita.id)
    # ---------------------------

    if ultima_visita and ultima_visita.disposizione_telai:
        stringa_telai = (ultima_visita.disposizione_telai + "V" * 10)[:numero_telai]
    else:
        stringa_telai = "V" * numero_telai
        
    mappa_telaini = list(stringa_telai)
    trattamenti = Trattamento.objects.filter(famiglia=famiglia).order_by('-data_inizio')

    # Dati Grafico Miele (rimane uguale)
    stats_produzione = Raccolto.objects.filter(famiglia=famiglia).annotate(anno=ExtractYear('data_raccolto')).values('anno').annotate(totale=Sum('kg_miele')).order_by('anno')
    anni = [item['anno'] for item in stats_produzione]
    kg_totali = [float(item['totale']) for item in stats_produzione]

    return render(request, 'apiario/dettagli_famiglia.html', {
        'famiglia': famiglia,
        'regina': regina,
        'regina_color_class': regina_color_class,
        'ultima_visita': ultima_visita, # Passiamo solo l'ultima
        'visite_pinned': visite_pinned, # Passiamo le importanti
        'mappa_telaini': mappa_telaini,
        'trattamenti': trattamenti,
        'anno_corrente': date.today().year,
        'grafico_anni': json.dumps(anni),
        'grafico_kg': json.dumps(kg_totali),
    })

def storico_visite_view(request, famiglia_id):
    famiglia = get_object_or_404(Famiglia, pk=famiglia_id)
    visite = Visita.objects.filter(famiglia=famiglia).order_by('-data_visita', '-id')
    return render(request, 'apiario/storico_visite.html', {'famiglia': famiglia, 'visite': visite})

# FUNZIONE PER PINNARE/SPINNARE (Veloce)
def toggle_pin_visita(request, visita_id):
    visita = get_object_or_404(Visita, pk=visita_id)
    visita.is_pinned = not visita.is_pinned
    visita.save()
    return redirect('dettagli_famiglia', famiglia_id=visita.famiglia.id)

def nuova_visita_view(request, famiglia_id):
    famiglia = get_object_or_404(Famiglia, pk=famiglia_id)
    
    # LOGICA DINAMICA TELAI (6 o 10)
    numero_telai = 6 if famiglia.arnia.categoria == 'portasciami' else 10
    range_telai = "".join(str(i) for i in range(numero_telai))

    ultima_visita = Visita.objects.filter(famiglia=famiglia).order_by('-data_visita', '-id').first()
    if ultima_visita and ultima_visita.disposizione_telai:
        disposizione_precedente = (ultima_visita.disposizione_telai + "V" * 10)[:numero_telai]
    else:
        disposizione_precedente = "V" * numero_telai

    if request.method == 'POST':
        form = VisitaForm(request.POST)
        if form.is_valid():
            visita = form.save(commit=False)
            visita.famiglia = famiglia
            visita.save()
            return redirect('dettagli_famiglia', famiglia_id=famiglia.id)
    else:
        form = VisitaForm(initial={'data_visita': timezone.now().date(), 'numero_melari': ultima_visita.numero_melari if ultima_visita else 0})
    
    return render(request, 'apiario/nuova_visita.html', {
        'form': form, 
        'famiglia': famiglia,
        'range_telai': range_telai,
        'disposizione_precedente': disposizione_precedente
    })

def nuova_famiglia_view(request, arnia_id):
    arnia = get_object_or_404(Arnia, pk=arnia_id)
    
    # LOGICA DINAMICA TELAI (6 o 10)
    numero_telai = 6 if arnia.categoria == 'portasciami' else 10
    range_telai = "".join(str(i) for i in range(numero_telai))
    disposizione_vuota = "V" * numero_telai

    if request.method == 'POST':
        form = FamigliaForm(request.POST)
        if form.is_valid():
            famiglia = form.save(commit=False)
            famiglia.arnia = arnia
            famiglia.stato = 'attiva'
            famiglia.save()

            arnia.stato = 'occupata'
            arnia.save()

            Visita.objects.create(
                famiglia=famiglia,
                data_visita=famiglia.data_inserimento or timezone.now().date(),
                disposizione_telai=form.cleaned_data.get('disposizione_telai', disposizione_vuota),
                note="Inserimento iniziale famiglia"
            )
            return redirect('dettagli_famiglia', famiglia_id=famiglia.id)
    else:
        form = FamigliaForm(initial={'data_inserimento': timezone.now().date()})
        
    return render(request, 'apiario/nuova_famiglia.html', {
        'form': form, 
        'arnia': arnia,
        'range_telai': range_telai,
        'disposizione_vuota': disposizione_vuota
    })

def nuova_arnia_view(request, apiario_id):
    apiario = get_object_or_404(Apiario, pk=apiario_id)
    if request.method == 'POST':
        form = ArniaForm(request.POST)
        if form.is_valid():
            arnia = form.save(commit=False)
            arnia.apiario = apiario
            arnia.save()
            return redirect('lista_arnie', apiario_id=apiario.id)
    else:
        form = ArniaForm()
    return render(request, 'apiario/nuova_arnia.html', {'form': form, 'apiario': apiario})

def lista_regine_view(request):
    regine = Regina.objects.select_related('famiglia__arnia__apiario').exclude(stato='morta').order_by('-anno_nascita')
    for r in regine:
        ultima_cifra = r.anno_nascita % 10
        if ultima_cifra in[1, 6]: r.color_class, r.color_name = "bg-white text-slate-800 border border-slate-300", "Bianco"
        elif ultima_cifra in[2, 7]: r.color_class, r.color_name = "bg-yellow-400 text-slate-900", "Giallo"
        elif ultima_cifra in [3, 8]: r.color_class, r.color_name = "bg-red-600 text-white", "Rosso"
        elif ultima_cifra in [4, 9]: r.color_class, r.color_name = "bg-green-600 text-white", "Verde"
        elif ultima_cifra in [5, 0]: r.color_class, r.color_name = "bg-blue-600 text-white", "Blu"
        else: r.color_class, r.color_name = "bg-slate-200 text-slate-700", "N/A"
    return render(request, 'apiario/lista_regine.html', {'regine': regine})

def nuova_regina_view(request, famiglia_id):
    famiglia = get_object_or_404(Famiglia, pk=famiglia_id)
    
    if request.method == 'POST':
        form = ReginaForm(request.POST)
        if form.is_valid():
            regina = form.save(commit=False)
            regina.famiglia = famiglia # Associao la famiglia qui!
            regina.save()
            return redirect('dettagli_famiglia', famiglia_id=famiglia.id)
        else:
            # Se il form non è valido, stampiamo l'errore nel terminale per debug
            print("ERRORI FORM REGINA:", form.errors)
    else:
        form = ReginaForm(initial={'anno_nascita': date.today().year})
    
    return render(request, 'apiario/nuova_regina.html', {'form': form, 'famiglia': famiglia})

def nuovo_trattamento_view(request, famiglia_id):
    famiglia = get_object_or_404(Famiglia, pk=famiglia_id)
    if request.method == 'POST':
        form = TrattamentoForm(request.POST)
        if form.is_valid():
            trattamento = form.save(commit=False)
            trattamento.famiglia = famiglia
            trattamento.save()
            return redirect('dettagli_famiglia', famiglia_id=famiglia.id)
    return render(request, 'apiario/nuovo_trattamento.html', {'form': TrattamentoForm(initial={'data_inizio': timezone.now().date()}), 'famiglia': famiglia})

def trattamento_massa_view(request, apiario_id):
    apiario = get_object_or_404(Apiario, pk=apiario_id)
    famiglie = Famiglia.objects.filter(arnia__apiario=apiario, stato='attiva')
    if request.method == 'POST':
        form = TrattamentoForm(request.POST)
        famiglie_selezionate = request.POST.getlist('famiglie_scelte')
        if form.is_valid() and famiglie_selezionate:
            per_salvare =[]
            for f_id in famiglie_selezionate:
                per_salvare.append(Trattamento(
                    famiglia_id=f_id,
                    data_inizio=form.cleaned_data['data_inizio'],
                    data_fine=form.cleaned_data['data_fine'],
                    prodotto=form.cleaned_data['prodotto'],
                    nome_commerciale=form.cleaned_data['nome_commerciale'],
                    note=form.cleaned_data['note']
                ))
            Trattamento.objects.bulk_create(per_salvare)
            return redirect('lista_arnie', apiario_id=apiario.id)
    else:
        form = TrattamentoForm(initial={'data_inizio': timezone.now().date()})
    return render(request, 'apiario/trattamento_massa.html', {'apiario': apiario, 'famiglie': famiglie, 'form': form})

def nuovo_raccolto_view(request, famiglia_id):
    famiglia = get_object_or_404(Famiglia, pk=famiglia_id)
    if request.method == 'POST':
        form = RaccoltoForm(request.POST)
        if form.is_valid():
            raccolto = form.save(commit=False)
            raccolto.famiglia = famiglia
            raccolto.save()
            return redirect('dettagli_famiglia', famiglia_id=famiglia.id)
    return render(request, 'apiario/nuovo_raccolto.html', {'form': RaccoltoForm(initial={'data_raccolto': timezone.now().date()}), 'famiglia': famiglia})

def calendario_fioriture_view(request):
    anno_corrente = date.today().year
    mese_corrente = date.today().month
    giorno_corrente = date.today().day

    # Struttura base dei mesi (Senza fiori hard-coded)
    mesi_base = [
        {'id': 1, 'nome': 'Gennaio', 'stagione': 'Inverno'},
        {'id': 2, 'nome': 'Febbraio', 'stagione': 'Inverno'},
        {'id': 3, 'nome': 'Marzo', 'stagione': 'Primavera'},
        {'id': 4, 'nome': 'Aprile', 'stagione': 'Primavera'},
        {'id': 5, 'nome': 'Maggio', 'stagione': 'Primavera'},
        {'id': 6, 'nome': 'Giugno', 'stagione': 'Estate'},
        {'id': 7, 'nome': 'Luglio', 'stagione': 'Estate'},
        {'id': 8, 'nome': 'Agosto', 'stagione': 'Estate'},
        {'id': 9, 'nome': 'Settembre', 'stagione': 'Autunno'},
        {'id': 10, 'nome': 'Ottobre', 'stagione': 'Autunno'},
        {'id': 11, 'nome': 'Novembre', 'stagione': 'Autunno'},
        {'id': 12, 'nome': 'Dicembre', 'stagione': 'Inverno'},
    ]

    # SIMULAZIONE CHIAMATA API OPEN SOURCE
    # Qui potresti usare 'requests' per chiamare un'API reale come Trefle o GBIF
    # Per ora carichiamo un dizionario che simula la risposta di un'API esterna
    fioriture_api = {
        3: ['Tarassaco', 'Melo', 'Pesco', 'Rosmarino'],
        4: ['Ciliegio', 'Biancospino', 'Colza', 'Salice'],
        5: ['Acacia', 'Agrumi', 'Millefiori', 'Erba Medica'],
        6: ['Tiglio', 'Castagno', 'Rovo', 'Ailanto'],
        # ... questa lista può essere popolata dinamicamente tramite API
    }

    cal = calendar.Calendar(firstweekday=0)
    
    for mese in mesi_base:
        # Recupero fioriture dall'API (simulata)
        mese['fioriture'] = fioriture_api.get(mese['id'], ['Nessun dato API'])
        
        # Eventi Utente
        eventi_mese = list(EventoCalendario.objects.filter(data__year=anno_corrente, data__month=mese['id']).order_by('data'))
        mese['eventi_utente'] = eventi_mese
        
        # Griglia Giorni
        griglia = []
        for week in cal.monthdayscalendar(anno_corrente, mese['id']):
            for day in week:
                if day == 0: griglia.append(None)
                else:
                    ev_giorno = [e for e in eventi_mese if e.data.day == day]
                    griglia.append({'giorno': day, 'eventi': ev_giorno})
        mese['griglia'] = griglia

    return render(request, 'apiario/calendario.html', {
        'calendario': mesi_base,
        'mese_corrente': mese_corrente,
        'giorno_corrente': giorno_corrente,
        'anno_corrente': anno_corrente
    })

def nuovo_evento_view(request):
    if request.method == 'POST':
        form = EventoCalendarioForm(request.POST)
        if form.is_valid():
            evento_principale = form.save()

            # --- LOGICA AUTOMATISMI (TRIGGER) ---
            titolo_low = evento_principale.titolo.lower()
            
            # Automatismo 1: Cella Reale -> Nascita (+15 giorni)
            if "cella" in titolo_low or "cella reale" in titolo_low:
                EventoCalendario.objects.create(
                    data = evento_principale.data + timedelta(days=15),
                    titolo = f"Nascita Regina (da {evento_principale.titolo})",
                    tipo = 'promemoria',
                    note = "Generato automaticamente dall'inserimento della cella reale."
                )
            
            # Automatismo 2: Regina Vergine -> Controllo Covata (+10 giorni)
            if "vergine" in titolo_low:
                EventoCalendario.objects.create(
                    data = evento_principale.data + timedelta(days=10),
                    titolo = f"Controllo Deposizione ({evento_principale.titolo})",
                    tipo = 'lavoro',
                    note = "Generato automaticamente: controlla se la regina si è fecondata."
                )

            return redirect('calendario')
    else:
        form = EventoCalendarioForm(initial={'data': date.today()})
    return render(request, 'apiario/nuovo_evento.html', {'form': form})

def elimina_evento_view(request, evento_id):
    evento = get_object_or_404(EventoCalendario, pk=evento_id)
    evento.delete() # Elimina dal database
    return redirect('calendario')

def modifica_evento_view(request, evento_id):
    evento = get_object_or_404(EventoCalendario, pk=evento_id)
    if request.method == 'POST':
        form = EventoCalendarioForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return redirect('calendario')
    else:
        form = EventoCalendarioForm(instance=evento)
    
    # Riutilizziamo il template nuovo_evento.html
    return render(request, 'apiario/nuovo_evento.html', {
        'form': form, 
        'edit_mode': True, 
        'evento': evento
    })

def nuovo_apiario_view(request):
    if request.method == 'POST':
        form = ApiarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ApiarioForm()
    return render(request, 'apiario/nuovo_apiario.html', {'form': form})

def trasferisci_famiglia_view(request, famiglia_id):
    famiglia = get_object_or_404(Famiglia, pk=famiglia_id)
    # Anche qui, ordiniamo le casse vuote per numero
    arnie_disponibili = Arnia.objects.filter(
        apiario=famiglia.arnia.apiario, 
        stato='vuota'
    ).order_by(Length('codice_identificativo'), 'codice_identificativo')

    if request.method == 'POST':
        nuova_arnia_id = request.POST.get('nuova_arnia_id')
        nuova_arnia = get_object_or_404(Arnia, pk=nuova_arnia_id)

        # 1. Svuotiamo la vecchia
        vecchia_arnia = famiglia.arnia
        vecchia_arnia.stato = 'vuota'
        vecchia_arnia.save()

        # 2. Occupiamo la nuova
        nuova_arnia.stato = 'occupata'
        nuova_arnia.save()

        # 3. Spostiamo la famiglia
        famiglia.arnia = nuova_arnia
        famiglia.save()

        # 4. Nota storica
        Visita.objects.create(
            famiglia=famiglia,
            data_visita=timezone.now().date(),
            note=f"TRAVASO: Spostata da {vecchia_arnia.codice_identificativo} a {nuova_arnia.codice_identificativo}",
            disposizione_telai="VVVVVVVVVV" if nuova_arnia.categoria == 'arnia' else "VVVVVV"
        )
        return redirect('dettagli_famiglia', famiglia_id=famiglia.id)

    return render(request, 'apiario/trasferisci_famiglia.html', {'famiglia': famiglia, 'arnie_disponibili': arnie_disponibili})

def elimina_arnia_view(request, arnia_id):
    arnia = get_object_or_404(Arnia, pk=arnia_id)
    apiario_id = arnia.apiario.id
    
    # Sicurezza: eliminiamo solo se non ci sono api dentro
    if arnia.stato == 'vuota':
        arnia.delete()
    
    return redirect('lista_arnie', apiario_id=apiario_id)