from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .csv_import import import_schools_from_csv
from .forms import CSVUploadForm
from .models import Conference, FavoriteSchool, School


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'contact_email', 'updated_at')
    search_fields = ('name', 'contact_name', 'contact_email')


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'nces_unitid',
        'team_type',
        'cycling_program_status',
        'conference',
        'city',
        'state',
        'geocode_status',
        'geocode_confidence',
        'geocode_needs_review',
        'updated_at',
    )
    list_filter = (
        'team_type',
        'cycling_program_status',
        'state',
        'conference',
        'road',
        'mtb_xc',
        'cyclocross',
        'geocode_status',
        'geocode_needs_review',
    )
    search_fields = ('name', 'nces_unitid', 'city', 'state', 'conference__name')
    change_list_template = 'admin/schools/school/change_list.html'
    readonly_fields = ('openstreetmap_link', 'openstreetmap_embed', 'next_needs_review_link')

    def openstreetmap_link(self, obj: School):
        if obj.latitude is None or obj.longitude is None:
            return 'Coordinates not available'
        url = f'https://www.openstreetmap.org/?mlat={obj.latitude}&mlon={obj.longitude}#map=15/{obj.latitude}/{obj.longitude}'
        return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">Open in OpenStreetMap</a>', url)

    openstreetmap_link.short_description = 'OpenStreetMap Link'

    def openstreetmap_embed(self, obj: School):
        if obj.latitude is None or obj.longitude is None:
            return 'Coordinates not available'

        lat = float(obj.latitude)
        lon = float(obj.longitude)
        delta = 0.01
        left = lon - delta
        right = lon + delta
        bottom = lat - delta
        top = lat + delta
        embed_url = (
            'https://www.openstreetmap.org/export/embed.html'
            f'?bbox={left:.6f}%2C{bottom:.6f}%2C{right:.6f}%2C{top:.6f}'
            '&layer=mapnik'
            f'&marker={lat:.6f}%2C{lon:.6f}'
        )
        return format_html(
            '<iframe width="100%" height="340" frameborder="0" scrolling="no" '
            'marginheight="0" marginwidth="0" src="{}" style="border:1px solid #ccc;"></iframe>',
            embed_url,
        )

    openstreetmap_embed.short_description = 'OpenStreetMap Preview'

    def next_needs_review_link(self, obj: School):
        next_school = (
            School.objects.filter(geocode_needs_review=True, id__gt=obj.id)
            .order_by('id')
            .first()
        )
        if not next_school:
            next_school = (
                School.objects.filter(geocode_needs_review=True)
                .exclude(id=obj.id)
                .order_by('id')
                .first()
            )

        if not next_school:
            return 'No schools currently flagged for review'

        next_url = reverse('admin:schools_school_change', args=[next_school.id])
        return format_html(
            '<a class="button" href="{}">Open Next Needs Review: {}</a>',
            next_url,
            next_school.name,
        )

    next_needs_review_link.short_description = 'Review Queue'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv), name='schools_school_upload_csv'),
        ]
        return custom_urls + urls

    def upload_csv(self, request: HttpRequest):
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                imported = import_schools_from_csv(request.FILES['csv_file'])
                self.message_user(request, f'Imported/updated {imported} schools.', level=messages.SUCCESS)
                return HttpResponseRedirect('../')
        else:
            form = CSVUploadForm()

        context = dict(
            self.admin_site.each_context(request),
            title='Upload School CSV',
            form=form,
        )
        return TemplateResponse(request, 'admin/schools/school/upload_csv.html', context)


@admin.register(FavoriteSchool)
class FavoriteSchoolAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'visibility', 'created_at')
    list_filter = ('visibility',)
    search_fields = ('user__email', 'school__name')
