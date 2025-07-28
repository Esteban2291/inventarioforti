from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Redirige la raíz a la página de login (o dashboard si ya estás logueado)
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),
    path('', include('core.urls')), # <--- ¡Añade esta línea para incluir las URLs de core!
]