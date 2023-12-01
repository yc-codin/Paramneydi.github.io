from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')), # Keeping this outside i18n_patterns
]

urlpatterns += i18n_patterns(
    path('', include('paramneydi.urls')),
    path('admin/', admin.site.urls),
)




