from django.contrib import admin
from django_admin_geomap import ModelAdmin

from .models import Location


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ("id", "name", "lat", "lon")
    list_display_links = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)

    # Поля модели, которые карта заполняет при выборе точки.
    geomap_field_longitude = "id_lon"
    geomap_field_latitude = "id_lat"

    # Центр карты по умолчанию — Владикавказ.
    geomap_default_longitude = "44.6818"
    geomap_default_latitude = "43.0367"
    geomap_default_zoom = "12"

    # Настройки отображения.
    geomap_item_zoom = "16"
    geomap_height = "520px"
    geomap_show_map_on_list = True
