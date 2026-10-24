from django.contrib import admin
from django.urls import path
from apiario import views
from django.views.generic import RedirectView

urlpatterns =[
    # Interfaccia nativa Django
    path('admin/', admin.site.urls),

    # Dashboard e Navigazione principale
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Gestione Arnie e Famiglie
    path('apiario/<int:apiario_id>/', views.lista_arnie_view, name='lista_arnie'),
    path('apiario/<int:apiario_id>/nuova-arnia/', views.nuova_arnia_view, name='nuova_arnia'),
    path('famiglia/<int:famiglia_id>/nuova-regina/', views.nuova_regina_view, name='nuova_regina'),
    path('arnia/<int:arnia_id>/elimina/', views.elimina_arnia_view, name='elimina_arnia'),
    path('arnia/<int:arnia_id>/nuova-famiglia/', views.nuova_famiglia_view, name='nuova_famiglia'),
    path('famiglia/<int:famiglia_id>/', views.dettagli_famiglia_view, name='dettagli_famiglia'),
    path('famiglia/<int:famiglia_id>/trasferisci/', views.trasferisci_famiglia_view, name='trasferisci_famiglia'),
    
    # Operazioni sulla Famiglia (Visite, Miele, Cure)
    path('famiglia/<int:famiglia_id>/nuova-visita/', views.nuova_visita_view, name='nuova_visita'),
    path('famiglia/<int:famiglia_id>/nuovo-raccolto/', views.nuovo_raccolto_view, name='nuovo_raccolto'),
    path('famiglia/<int:famiglia_id>/nuovo-trattamento/', views.nuovo_trattamento_view, name='nuovo_trattamento'),
    
    # Operazioni massive
    path('apiario/<int:apiario_id>/trattamento-massa/', views.trattamento_massa_view, name='trattamento_massa'),

    # Calendario e Agenda
    path('calendario/', views.calendario_fioriture_view, name='calendario'),
    path('calendario/nuovo-evento/', views.nuovo_evento_view, name='nuovo_evento'),
    path('calendario/elimina-evento/<int:evento_id>/', views.elimina_evento_view, name='elimina_evento'),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('calendario/modifica-evento/<int:evento_id>/', views.modifica_evento_view, name='modifica_evento'),
    path('apiario/nuovo/', views.nuovo_apiario_view, name='nuovo_apiario'),
    path('inventario/', views.inventario_view, name='inventario'),
    path('api/aggiorna-scorta/', views.aggiorna_scorta_api, name='aggiorna_scorta_api'),
    path('api/imposta-scorta/', views.imposta_scorta_api, name='imposta_scorta_api'),
    path('famiglia/<int:famiglia_id>/storico/', views.storico_visite_view, name='storico_visite'),
    path('visita/<int:visita_id>/toggle-pin/', views.toggle_pin_visita, name='toggle_pin'),

]