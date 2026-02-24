from urllib.parse import urlencode

from django.core.files.base import ContentFile
from django.contrib import admin, messages
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .csv_import import import_schools_from_csv
from .forms import CSVUploadForm, DataLoadUploadForm
from .import_pipeline import parse_schema_json_file, run_data_load_job
from .models import Conference, DataLoadJob, FavoriteSchool, ImportSchema, School


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'long_name', 'acronym', 'contact_name', 'contact_email', 'updated_at')
    search_fields = ('name', 'long_name', 'acronym', 'contact_name', 'contact_email')


class NCESCoverageFilter(admin.SimpleListFilter):
    title = 'NCES Coverage'
    parameter_name = 'nces_coverage'

    def lookups(self, request, model_admin):
        return (
            ('missing', 'Missing NCES ID'),
            ('present', 'Has NCES ID'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'missing':
            return queryset.filter(nces_unitid='')
        if value == 'present':
            return queryset.exclude(nces_unitid='')
        return queryset


class AddressHealthFilter(admin.SimpleListFilter):
    title = 'Address Health'
    parameter_name = 'address_health'

    def lookups(self, request, model_admin):
        return (
            ('missing_any', 'Missing Any Address Field'),
            ('complete', 'Address Complete'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        missing_query = (
            Q(street_address='') |
            Q(city='') |
            Q(state='') |
            Q(zip_code='')
        )
        if value == 'missing_any':
            return queryset.filter(missing_query)
        if value == 'complete':
            return queryset.exclude(missing_query)
        return queryset


class CoordinatesHealthFilter(admin.SimpleListFilter):
    title = 'Coordinates Health'
    parameter_name = 'coordinates_health'

    def lookups(self, request, model_admin):
        return (
            ('missing', 'Missing Coordinates'),
            ('present', 'Has Coordinates'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        missing_query = Q(latitude__isnull=True) | Q(longitude__isnull=True)
        if value == 'missing':
            return queryset.filter(missing_query)
        if value == 'present':
            return queryset.exclude(missing_query)
        return queryset


class ProfileHealthFilter(admin.SimpleListFilter):
    title = 'Profile Health'
    parameter_name = 'profile_health'

    def lookups(self, request, model_admin):
        return (
            ('missing_locale', 'Missing Locale'),
            ('missing_enrollment', 'Missing Enrollment'),
            ('missing_acceptance', 'Missing Acceptance Rate'),
            ('missing_graduation', 'Missing Graduation Rate'),
            ('missing_any_core', 'Missing Any Core Profile Field'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        core_missing_query = (
            Q(locale='') |
            Q(enrollment='') |
            Q(acceptance_rate='') |
            Q(graduation_rate='')
        )
        if value == 'missing_locale':
            return queryset.filter(locale='')
        if value == 'missing_enrollment':
            return queryset.filter(enrollment='')
        if value == 'missing_acceptance':
            return queryset.filter(acceptance_rate='')
        if value == 'missing_graduation':
            return queryset.filter(graduation_rate='')
        if value == 'missing_any_core':
            return queryset.filter(core_missing_query)
        return queryset


class NCESDuplicateFilter(admin.SimpleListFilter):
    title = 'NCES Duplicate Health'
    parameter_name = 'nces_duplicates'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Duplicate NCES IDs'),
            ('no', 'No Duplicate NCES IDs'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        duplicate_unitids = (
            School.objects.exclude(nces_unitid='')
            .values('nces_unitid')
            .annotate(total=Count('id'))
            .filter(total__gt=1)
            .values_list('nces_unitid', flat=True)
        )

        if value == 'yes':
            return queryset.filter(nces_unitid__in=list(duplicate_unitids))
        if value == 'no':
            return queryset.exclude(nces_unitid__in=list(duplicate_unitids))
        return queryset


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'nces_unitid',
        'team_type',
        'cycling_program_status',
        'conference',
        'institution_control',
        'institution_level',
        'locale',
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
        NCESCoverageFilter,
        NCESDuplicateFilter,
        AddressHealthFilter,
        CoordinatesHealthFilter,
        ProfileHealthFilter,
        'institution_control',
        'institution_level',
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
            path('scorecard/', self.admin_site.admin_view(self.scorecard_view), name='schools_school_scorecard'),
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv), name='schools_school_upload_csv'),
        ]
        return custom_urls + urls

    def _school_changelist_url(self, params: dict[str, str]) -> str:
        base_url = reverse('admin:schools_school_changelist')
        return f'{base_url}?{urlencode(params)}'

    def scorecard_view(self, request: HttpRequest):
        total = School.objects.count()
        duplicate_unitids = list(
            School.objects.exclude(nces_unitid='')
            .values('nces_unitid')
            .annotate(total=Count('id'))
            .filter(total__gt=1)
            .values_list('nces_unitid', flat=True)
        )

        stats = [
            {
                'label': 'Missing NCES IDs',
                'count': School.objects.filter(nces_unitid='').count(),
                'href': self._school_changelist_url({'nces_coverage': 'missing'}),
                'description': 'Schools still missing NCES UNITID linkage.',
            },
            {
                'label': 'Duplicate NCES IDs',
                'count': School.objects.filter(nces_unitid__in=duplicate_unitids).count(),
                'href': self._school_changelist_url({'nces_duplicates': 'yes'}),
                'description': 'Potential duplicate school records sharing the same NCES ID.',
            },
            {
                'label': 'Missing Any Address Field',
                'count': School.objects.filter(
                    Q(street_address='') | Q(city='') | Q(state='') | Q(zip_code='')
                ).count(),
                'href': self._school_changelist_url({'address_health': 'missing_any'}),
                'description': 'Missing street, city, state, or zip.',
            },
            {
                'label': 'Missing Coordinates',
                'count': School.objects.filter(
                    Q(latitude__isnull=True) | Q(longitude__isnull=True)
                ).count(),
                'href': self._school_changelist_url({'coordinates_health': 'missing'}),
                'description': 'Missing latitude or longitude.',
            },
            {
                'label': 'Geocode Needs Review',
                'count': School.objects.filter(geocode_needs_review=True).count(),
                'href': self._school_changelist_url({'geocode_needs_review__exact': '1'}),
                'description': 'Geocode confidence below review threshold.',
            },
            {
                'label': 'Unknown Institution Control',
                'count': School.objects.filter(
                    institution_control=School.InstitutionControl.UNKNOWN
                ).count(),
                'href': self._school_changelist_url(
                    {'institution_control__exact': School.InstitutionControl.UNKNOWN}
                ),
                'description': 'Missing/unknown public vs private control data.',
            },
            {
                'label': 'Unknown Institution Level',
                'count': School.objects.filter(
                    institution_level=School.InstitutionLevel.UNKNOWN
                ).count(),
                'href': self._school_changelist_url(
                    {'institution_level__exact': School.InstitutionLevel.UNKNOWN}
                ),
                'description': 'Missing/unknown 2-year vs 4-year level data.',
            },
            {
                'label': 'Missing Locale',
                'count': School.objects.filter(locale='').count(),
                'href': self._school_changelist_url({'profile_health': 'missing_locale'}),
                'description': 'Locale classification missing.',
            },
            {
                'label': 'Missing Enrollment',
                'count': School.objects.filter(enrollment='').count(),
                'href': self._school_changelist_url({'profile_health': 'missing_enrollment'}),
                'description': 'Enrollment field missing.',
            },
            {
                'label': 'Missing Acceptance Rate',
                'count': School.objects.filter(acceptance_rate='').count(),
                'href': self._school_changelist_url({'profile_health': 'missing_acceptance'}),
                'description': 'Acceptance rate field missing.',
            },
            {
                'label': 'Missing Graduation Rate',
                'count': School.objects.filter(graduation_rate='').count(),
                'href': self._school_changelist_url({'profile_health': 'missing_graduation'}),
                'description': 'Graduation rate field missing.',
            },
        ]

        for item in stats:
            item['pct'] = round((item['count'] / total * 100), 1) if total else 0.0

        context = dict(
            self.admin_site.each_context(request),
            title='School Data Health Scorecard',
            total_schools=total,
            stats=stats,
            school_changelist_url=reverse('admin:schools_school_changelist'),
        )
        return TemplateResponse(request, 'admin/schools/school/scorecard.html', context)

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


@admin.register(ImportSchema)
class ImportSchemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'target_model', 'active', 'updated_at')
    list_filter = ('active', 'target_model')
    search_fields = ('name', 'version')


@admin.register(DataLoadJob)
class DataLoadJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'schema',
        'dry_run',
        'status',
        'created_count',
        'updated_count',
        'error_count',
        'triggered_by',
        'created_at',
        'commit_link',
    )
    list_filter = ('status', 'dry_run', 'schema')
    search_fields = ('schema__name', 'schema__version', '=id')
    readonly_fields = (
        'status',
        'created_count',
        'updated_count',
        'error_count',
        'error_message',
        'started_at',
        'finished_at',
        'created_at',
    )
    change_list_template = 'admin/schools/dataloadjob/change_list.html'
    actions = ('commit_selected_dry_runs',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-and-run/', self.admin_site.admin_view(self.upload_and_run), name='schools_dataloadjob_upload_and_run'),
            path('commit-job/<int:job_id>/', self.admin_site.admin_view(self.commit_job), name='schools_dataloadjob_commit_job'),
        ]
        return custom_urls + urls

    def commit_link(self, obj: DataLoadJob):
        if not obj.dry_run or obj.status != DataLoadJob.Status.COMPLETED:
            return '-'
        url = reverse('admin:schools_dataloadjob_commit_job', args=[obj.id])
        return format_html('<a class="button" href="{}">Commit from this dry run</a>', url)

    commit_link.short_description = 'Commit'

    def _create_schema_from_upload(self, cleaned_data):
        schema_file = cleaned_data.get('schema_file')
        if not schema_file:
            return cleaned_data['schema']

        payload = parse_schema_json_file(schema_file)
        mapping = payload.get('mapping') or payload.get('mapping_json') or {}
        unique_keys = payload.get('unique_key_fields') or []
        required_fields = payload.get('required_fields') or []
        defaults = payload.get('defaults') or payload.get('defaults_json') or {}
        type_rules = payload.get('type_rules') or {}
        target_model = payload.get('target_model') or 'schools.School'

        schema_version = (cleaned_data.get('schema_version') or '').strip() or 'v1'
        schema_name = cleaned_data['schema_name'].strip()
        schema, _ = ImportSchema.objects.update_or_create(
            name=schema_name,
            version=schema_version,
            defaults={
                'target_model': target_model,
                'mapping_json': mapping,
                'unique_key_fields': unique_keys,
                'required_fields': required_fields,
                'defaults_json': defaults,
                'type_rules': type_rules,
                'active': True,
            },
        )
        return schema

    def upload_and_run(self, request: HttpRequest):
        if request.method == 'POST':
            form = DataLoadUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    schema = self._create_schema_from_upload(form.cleaned_data)
                    data_file = form.cleaned_data['csv_file']
                    dry_run = bool(form.cleaned_data.get('dry_run'))
                    job = DataLoadJob(schema=schema, dry_run=dry_run, triggered_by=request.user)
                    job.uploaded_file.save(data_file.name, ContentFile(data_file.read()), save=False)
                    job.save()

                    run_data_load_job(job)

                    self.message_user(
                        request,
                        (
                            f'Job #{job.id} finished: '
                            f'{job.created_count} creates, {job.updated_count} updates, {job.error_count} errors.'
                        ),
                        level=messages.SUCCESS if job.status == DataLoadJob.Status.COMPLETED else messages.ERROR,
                    )
                    return HttpResponseRedirect('../')
                except Exception as exc:
                    self.message_user(request, f'Unable to run data load: {exc}', level=messages.ERROR)
        else:
            form = DataLoadUploadForm(initial={'dry_run': True})

        context = dict(
            self.admin_site.each_context(request),
            title='Upload Data + Run Loader',
            form=form,
        )
        return TemplateResponse(request, 'admin/schools/dataloadjob/upload_and_run.html', context)

    def _clone_file(self, source_field):
        source_field.open('rb')
        try:
            return ContentFile(source_field.read())
        finally:
            source_field.close()

    def _commit_from_dry_run(self, request: HttpRequest, dry_run_job: DataLoadJob):
        if not dry_run_job.dry_run or dry_run_job.status != DataLoadJob.Status.COMPLETED:
            self.message_user(request, 'Only completed dry-run jobs can be committed.', level=messages.ERROR)
            return None

        if dry_run_job.error_count:
            self.message_user(
                request,
                'Dry run contains errors. Resolve and re-run before commit.',
                level=messages.ERROR,
            )
            return None

        commit_job = DataLoadJob.objects.create(
            schema=dry_run_job.schema,
            dry_run=False,
            triggered_by=request.user,
        )
        commit_job.uploaded_file.save(
            dry_run_job.uploaded_file.name.rsplit('/', 1)[-1],
            self._clone_file(dry_run_job.uploaded_file),
            save=True,
        )
        run_data_load_job(commit_job)
        return commit_job

    def commit_job(self, request: HttpRequest, job_id: int):
        dry_run_job = self.get_object(request, job_id)
        if dry_run_job is None:
            self.message_user(request, 'Dry-run job not found.', level=messages.ERROR)
            return HttpResponseRedirect('../')

        commit_job = self._commit_from_dry_run(request, dry_run_job)
        if commit_job:
            self.message_user(
                request,
                (
                    f'Commit job #{commit_job.id} finished: '
                    f'{commit_job.created_count} creates, {commit_job.updated_count} updates, '
                    f'{commit_job.error_count} errors.'
                ),
                level=messages.SUCCESS if commit_job.status == DataLoadJob.Status.COMPLETED else messages.ERROR,
            )
        return HttpResponseRedirect('../../')

    @admin.action(description='Commit selected dry-run jobs')
    def commit_selected_dry_runs(self, request: HttpRequest, queryset):
        for dry_run_job in queryset:
            commit_job = self._commit_from_dry_run(request, dry_run_job)
            if commit_job:
                self.message_user(
                    request,
                    f'Committed dry run #{dry_run_job.id} as job #{commit_job.id}.',
                    level=messages.SUCCESS,
                )
