from django.contrib import admin
from .models import AnnihilationEvent, AnnihilationPolicy, DateTimeAnnihilation,\
    EnumerationContext, AnnihilationEnumContext

# Register your models here.
admin.site.register(DateTimeAnnihilation)
admin.site.register(AnnihilationEvent)
admin.site.register(AnnihilationPolicy)
admin.site.register(EnumerationContext)
admin.site.register(AnnihilationEnumContext)