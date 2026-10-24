from django import forms
from .models import Visita, Arnia, Famiglia, Trattamento, Raccolto, Regina, EventoCalendario, Apiario

class VisitaForm(forms.ModelForm):
    class Meta:
        model = Visita
        fields = ['data_visita', 'disposizione_telai', 'numero_melari', 'presenza_celle_reali', 'presenza_covata_fresca', 'note']
        widgets = {
            'data_visita': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Note sulla visita...'}),
        }

class RaccoltoForm(forms.ModelForm):
    class Meta:
        model = Raccolto
        fields = ['data_raccolto', 'kg_miele', 'tipo_miele', 'note']
        widgets = {
            'data_raccolto': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 rounded-xl border border-slate-200'}),
            'kg_miele': forms.NumberInput(attrs={'class': 'w-full p-3 rounded-xl border border-slate-200', 'step': '0.5'}),
            'tipo_miele': forms.Select(attrs={'class': 'w-full p-3 rounded-xl border border-slate-200'}),
            'note': forms.Textarea(attrs={'rows': 2, 'class': 'w-full p-3 rounded-xl border border-slate-200'}),
        }

class TrattamentoForm(forms.ModelForm):
    class Meta:
        model = Trattamento
        fields = ['data_inizio', 'data_fine', 'prodotto', 'nome_commerciale', 'note']
        widgets = {
            'data_inizio': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 rounded-xl border border-slate-200'}),
            'data_fine': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 rounded-xl border border-slate-200'}),
            'prodotto': forms.Select(attrs={'class': 'w-full p-3 rounded-xl border border-slate-200'}),
            'nome_commerciale': forms.TextInput(attrs={'class': 'w-full p-3 rounded-xl border border-slate-200', 'placeholder': 'Nome commerciale'}),
            'note': forms.Textarea(attrs={'rows': 2, 'class': 'w-full p-3 rounded-xl border border-slate-200'}),
        }

class ArniaForm(forms.ModelForm):
    class Meta:
        model = Arnia
        # Aggiungiamo 'colore' alla lista
        fields = ['codice_identificativo', 'categoria', 'colore'] 
        widgets = {
            'codice_identificativo': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-black text-xl uppercase', 'placeholder': 'Es: A-12'}),
            'categoria': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold bg-white'}),
            # Aggiungiamo il widget testuale per il colore
            'colore': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold bg-white', 'placeholder': 'Es: Giallo, Verde, Legno grezzo...'}),
        }

class FamigliaForm(forms.ModelForm):
    disposizione_telai = forms.CharField(max_length=10, initial="VVVVVVVVVV", widget=forms.HiddenInput())

    class Meta:
        model = Famiglia
        fields =['origine', 'indole', 'data_inserimento']
        widgets = {
            'origine': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold bg-white'}),
            'indole': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold bg-white'}),
            'data_inserimento': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold'}),
        }

class ReginaForm(forms.ModelForm):
    class Meta:
        model = Regina
        # Escludiamo famiglia dai campi compilabili dall'utente
        fields = ['anno_nascita', 'stato'] 
        widgets = {
            'anno_nascita': forms.NumberInput(attrs={'class': 'w-full p-4 rounded-2xl bg-[#121417] text-white border border-slate-700 font-black'}),
            'stato': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl bg-[#121417] text-white border border-slate-700 font-black'}),
        }

class EventoCalendarioForm(forms.ModelForm):
    class Meta:
        model = EventoCalendario
        fields = ['data', 'titolo', 'tipo', 'note']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold'}),
            'titolo': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-black text-lg', 'placeholder': 'Cosa devi fare?'}),
            'tipo': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold bg-white'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-4 rounded-2xl border border-slate-200', 'placeholder': 'Dettagli aggiuntivi...'}),
        }

class ApiarioForm(forms.ModelForm):
    class Meta:
        model = Apiario
        fields = ['luogo', 'fioritura', 'latitudine', 'longitudine', 'note']
        widgets = {
            'luogo': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold', 'placeholder': 'Luogo...'}),
            'fioritura': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-bold', 'placeholder': 'Es: Acacia, Castagno...'}),
            'latitudine': forms.NumberInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-mono', 'step': 'any', 'id': 'id_lat'}),
            'longitudine': forms.NumberInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 font-mono', 'step': 'any', 'id': 'id_lon'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-4 rounded-2xl border border-slate-200'}),
        }