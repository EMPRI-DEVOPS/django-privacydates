from django.contrib import admin
from .models import VanishingEvent, VanishingPolicy, VanishingDateTime,\
    OrderingContext, VanishingOrderingContext

# Register your models here.
admin.site.register(VanishingDateTime)
admin.site.register(VanishingEvent)
admin.site.register(VanishingPolicy)
admin.site.register(OrderingContext)
admin.site.register(VanishingOrderingContext)
