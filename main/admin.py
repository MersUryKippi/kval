from django.contrib import admin

from .models import Record


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "price", "active", "on_date", "created")
    list_filter = ("active",)
    search_fields = ("name", "code")
    readonly_fields = ("created",)
