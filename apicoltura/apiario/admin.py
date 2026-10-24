from django.contrib import admin
from .models import Apiario, Arnia, Famiglia, Regina, Visita

# Questo rende l'interfaccia molto più bella e leggibile
@admin.register(Apiario)
class ApiarioAdmin(admin.ModelAdmin):
    # Visualizziamo fioritura, luogo e i due conteggi automatici
    list_display = ('fioritura', 'luogo', 'famiglie_attive_count', 'arnie_vuote_count')

    def famiglie_attive_count(self, obj):
        return obj.famiglie_attive
    famiglie_attive_count.short_description = "Famiglie Attive"

    def arnie_vuote_count(self, obj):
        return obj.arnie_vuote
    arnie_vuote_count.short_description = "Arnie Vuote"
    
@admin.register(Arnia)
class ArniaAdmin(admin.ModelAdmin):
    list_display = ('codice_identificativo', 'apiario', 'categoria', 'stato')
    list_filter = ('apiario', 'categoria', 'stato')

@admin.register(Famiglia)
class FamigliaAdmin(admin.ModelAdmin):
    list_display = ('id', 'arnia', 'stato', 'indole')
    list_filter = ('stato', 'indole')

@admin.register(Regina)
class ReginaAdmin(admin.ModelAdmin):
    list_display = ('famiglia', 'anno_nascita', 'stato')

@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ('data_visita', 'famiglia', 'telai_totali', 'presenza_celle_reali')
    list_filter = ('data_visita', 'famiglia')