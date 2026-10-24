from django.db import models
from django.db.models import Sum
from datetime import date

class Apiario(models.Model):
    fioritura = models.CharField(max_length=100, blank=True, null=True)
    luogo = models.CharField(max_length=255, blank=True, null=True) # Questo rimane come descrizione generica
    latitudine = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitudine = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    @property
    def famiglie_attive(self):
        from .models import Famiglia
        # Filtra: arnia dell'apiario corrente + stato attivo
        return Famiglia.objects.filter(
            arnia__apiario=self, 
            stato='attiva'
        ).count()

    @property
    def arnie_vuote(self):
        from .models import Arnia
        # Conta le arnie di questo apiario che hanno lo stato 'vuota'
        return Arnia.objects.filter(
            apiario=self, 
            stato='vuota'
        ).count()

    class Meta:
        verbose_name = "Apiario"
        verbose_name_plural = "Apiari"

    def __str__(self):
        return self.luogo
    
class Arnia(models.Model):
    apiario = models.ForeignKey(Apiario, on_delete=models.CASCADE)
    codice_identificativo = models.CharField(max_length=50)
    categoria = models.CharField(max_length=20, choices=[('arnia','Arnia'),('portasciami','Portasciami')], default='arnia')
    stato = models.CharField(max_length=20, choices=[('occupata','Occupata'),('vuota','Vuota')], default='vuota')
    
    # AGGIUNGI QUESTA RIGA:
    colore = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self): return f"{self.codice_identificativo} ({self.apiario.nome})"
    class Meta:
        verbose_name = "Arnia"
        verbose_name_plural = "Arnie"

class Famiglia(models.Model):
    ORIGINE_CHOICES =[
        ('sciamatura naturale', 'Sciamatura Naturale'),
        ('sciamatura artificiale', 'Sciamatura Artificiale'),
        ('acquisto', 'Acquisto'),
    ]
    STATO_CHOICES =[
        ('attiva', 'Attiva'),
        ('morta', 'Morta'),
        ('fusa', 'Fusa'),
        ('venduta', 'Venduta'),
    ]
    INDOLE_CHOICES =[
        ('docile', 'Docile'),
        ('media', 'Media'),
        ('aggressiva', 'Aggressiva'),
    ]

    arnia = models.ForeignKey(Arnia, on_delete=models.RESTRICT)
    origine = models.CharField(max_length=30, choices=ORIGINE_CHOICES)
    indole = models.CharField(max_length=20, choices=INDOLE_CHOICES, default='media')
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='attiva')
    data_inserimento = models.DateField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    @property
    def produzione_totale_anno(self):
        anno_corrente = date.today().year
        totale = Raccolto.objects.filter(
            famiglia=self, 
            data_raccolto__year=anno_corrente
        ).aggregate(Sum('kg_miele'))['kg_miele__sum']
        return totale or 0

    def __str__(self):
        return f"Famiglia in {self.arnia.codice_identificativo}"
    
    class Meta:
        verbose_name = "Famiglia"
        verbose_name_plural = "Famiglie"

class Regina(models.Model):
    ORIGINE_CHOICES =[
        ('allevata', 'Allevata'),
        ('acquistata', 'Acquistata'),
        ('sostituzione naturale', 'Sostituzione Naturale'),
    ]
    STATO_CHOICES =[
        ('in deposizione', 'In Deposizione'),
        ('vergine', 'Vergine'),
        ('morta', 'Morta'),
        ('sciamata', 'Sciamata'),
        ('sostituita', 'Sostituita'),
    ]

    famiglia = models.ForeignKey(Famiglia, on_delete=models.CASCADE)
    anno_nascita = models.IntegerField()
    origine = models.CharField(max_length=30, choices=ORIGINE_CHOICES)
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='vergine')
    data_inserimento = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Regina {self.anno_nascita} ({self.stato})"
    
    class Meta:
        verbose_name = "Regina"
        verbose_name_plural = "Regine"

    def get_color_info(self):
        """Restituisce la classe CSS e il nome del colore internazionale"""
        ultima_cifra = self.anno_nascita % 10
        mappa = {
            1: ("bg-white text-slate-800 border border-slate-300", "Bianco"),
            6: ("bg-white text-slate-800 border border-slate-300", "Bianco"),
            2: ("bg-yellow-400 text-slate-900", "Giallo"),
            7: ("bg-yellow-400 text-slate-900", "Giallo"),
            3: ("bg-red-600 text-white", "Rosso"),
            8: ("bg-red-600 text-white", "Rosso"),
            4: ("bg-green-600 text-white", "Verde"),
            9: ("bg-green-600 text-white", "Verde"),
            5: ("bg-blue-600 text-white", "Blu"),
            0: ("bg-blue-600 text-white", "Blu"),
        }
        return mappa.get(ultima_cifra, ("bg-slate-200 text-slate-700", "N/A"))

class Visita(models.Model):
    famiglia = models.ForeignKey(Famiglia, on_delete=models.CASCADE)
    data_visita = models.DateField()
    
    # I telaini li teniamo tutti qui
    telai_vuoti = models.IntegerField(default=0)
    telai_scorta = models.IntegerField(default=0)
    telai_covata = models.IntegerField(default=0)
    telai_fogli_cerei = models.IntegerField(default=0)
    
    # editable=False nasconde il campo nel pannello di amministrazione
    # perché tanto lo calcola il sistema da solo
    telai_totali = models.IntegerField(default=0, editable=False)
    
    # Check di ispezione
    presenza_celle_reali = models.BooleanField(default=False)
    presenza_covata_fresca = models.BooleanField(default=True)
    disposizione_telai = models.CharField(max_length=12, default="VVVVVVVVVV")
    numero_melari = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Il trucco: Somma i telaini automaticamente ad ogni salvataggio della visita
        self.telai_totali = (
            self.telai_vuoti + 
            self.telai_scorta + 
            self.telai_covata + 
            self.telai_fogli_cerei
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Visita del {self.data_visita} - {self.famiglia}"
    
    class Meta:
        verbose_name = "Visita"
        verbose_name_plural = "Visite"

class Trattamento(models.Model):
    TIPO_PRODOTTO_CHOICES = [
        ('acido_ossalico', 'Acido Ossalico'),
        ('acido_formico', 'Acido Formico'),
        ('timolo', 'Timolo'),
        ('amitraz', 'Amitraz'),
        ('altro', 'Altro'),
    ]

    famiglia = models.ForeignKey(Famiglia, on_delete=models.CASCADE)
    data_inizio = models.DateField()
    data_fine = models.DateField(null=True, blank=True, help_text="Opzionale")
    prodotto = models.CharField(max_length=100, choices=TIPO_PRODOTTO_CHOICES)
    nome_commerciale = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Trattamento"
        verbose_name_plural = "Trattamenti"
        ordering = ['-data_inizio']

    def __str__(self):
        return f"{self.prodotto} - {self.famiglia}"
    
class Raccolto(models.Model):
    TIPO_MIELE_CHOICES = [
        ('acacia', 'Acacia'),
        ('millefiori', 'Millefiori'),
        ('castagno', 'Castagno'),
        ('tiglio', 'Tiglio'),
        ('melata', 'Melata'),
        ('tarassaco', 'Tarassaco'),
    ]

    famiglia = models.ForeignKey(Famiglia, on_delete=models.CASCADE)
    data_raccolto = models.DateField()
    kg_miele = models.DecimalField(max_digits=5, decimal_places=2) # es. 15.50
    tipo_miele = models.CharField(max_length=50, choices=TIPO_MIELE_CHOICES)
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Raccolto"
        verbose_name_plural = "Raccolti"
        ordering = ['-data_raccolto']

    def __str__(self):
        return f"{self.kg_miele}kg {self.tipo_miele} - {self.famiglia}"
    
class EventoCalendario(models.Model):
    TIPO_CHOICES =[
        ('fioritura', '🌸 Nuova Fioritura'),
        ('lavoro', '🔨 Lavoro in Apiario'),
        ('trattamento', '💉 Trattamento / Veterinaria'),
        ('nutrizione', '🍯 Nutrizione / Miele'),
        ('promemoria', '📌 Promemoria Generico'),
    ]

    data = models.DateField()
    # RIMOSSO IL PLACEHOLDER QUI SOTTO:
    titolo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='lavoro')
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Evento Calendario"
        verbose_name_plural = "Eventi Calendario"
        ordering = ['data']

    def __str__(self):
        return f"{self.data.strftime('%d/%m')} - {self.titolo}"
    
class Scorta(models.Model):
    CATEGORIA_CHOICES = [
        ('arnia', 'Cassa Arnia (non num.)'),
        ('melario', 'Melario'),
        ('nido_telaio', 'Telaio Nido (vuoto)'),
        ('melario_telaio', 'Telaio Melario (vuoto)'),
        ('foglio_cerei', 'Fogli Cerei (kg)'),
        ('nutritore_coprifavo', 'Nutritore coprifavo'),
        ('nutritore_tasca', 'Nutritore tasca'),
        ('diaframma', 'Diaframma'),
        ('doppio_melario', 'Doppio Melario')
    ]
    
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, unique=True)
    quantita = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Scorta"
        verbose_name_plural = "Scorte"

    def __str__(self):
        return f"{self.get_categoria_display()}: {self.quantita}"