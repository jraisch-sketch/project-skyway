from django.conf import settings
from django.db import models


class Conference(models.Model):
    name = models.CharField(max_length=150, unique=True)
    long_name = models.CharField(max_length=255, blank=True)
    acronym = models.CharField(max_length=30, blank=True, db_index=True)
    description = models.TextField(blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class School(models.Model):
    class TeamType(models.TextChoices):
        CLUB = 'Club', 'Club'
        VARSITY = 'Varsity', 'Varsity'

    class GeocodeStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ENRICHED = 'enriched', 'Enriched'
        GEOCODED = 'geocoded', 'Geocoded'
        REVIEW = 'review', 'Needs Review'
        FAILED = 'failed', 'Failed'

    class CyclingProgramStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        LIMITED = 'limited', 'Limited'
        INACTIVE = 'inactive', 'Inactive'
        UNKNOWN = 'unknown', 'Unknown'

    class InstitutionControl(models.TextChoices):
        PUBLIC = 'public', 'Public'
        PRIVATE_NONPROFIT = 'private_nonprofit', 'Private Nonprofit'
        PRIVATE_FOR_PROFIT = 'private_for_profit', 'Private For-Profit'
        UNKNOWN = 'unknown', 'Unknown'

    class InstitutionLevel(models.TextChoices):
        FOUR_YEAR = 'four_year', 'Four-Year'
        TWO_YEAR = 'two_year', 'Two-Year'
        LESS_THAN_TWO_YEAR = 'less_than_two_year', 'Less Than Two-Year'
        UNKNOWN = 'unknown', 'Unknown'

    name = models.CharField(max_length=255, db_index=True)
    proto_data = models.TextField(blank=True)
    conference = models.ForeignKey(
        Conference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schools',
    )
    team_type = models.CharField(max_length=20, choices=TeamType.choices, blank=True, db_index=True)

    roster_male = models.PositiveIntegerField(null=True, blank=True)
    roster_female = models.PositiveIntegerField(null=True, blank=True)
    contact_email = models.EmailField(blank=True)

    date_joined = models.DateField(null=True, blank=True)
    last_current = models.DateField(null=True, blank=True)
    mascot = models.CharField(max_length=255, blank=True)

    school_website = models.URLField(blank=True)
    athletic_dept_website = models.URLField(blank=True)
    cycling_website = models.URLField(blank=True)

    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=50, blank=True, db_index=True)
    zip_code = models.CharField(max_length=20, blank=True)
    address_complete = models.CharField(max_length=255, blank=True)
    geocode_raw = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True, db_index=True)
    longitude = models.FloatField(null=True, blank=True, db_index=True)
    geocode_status = models.CharField(
        max_length=20,
        choices=GeocodeStatus.choices,
        default=GeocodeStatus.PENDING,
        db_index=True,
    )
    geocode_confidence = models.FloatField(null=True, blank=True)
    geocode_query = models.CharField(max_length=255, blank=True)
    geocode_source = models.CharField(max_length=100, blank=True)
    geocode_source_url = models.URLField(blank=True)
    geocode_needs_review = models.BooleanField(default=False, db_index=True)
    geocode_notes = models.TextField(blank=True)
    geocode_updated_at = models.DateTimeField(null=True, blank=True)
    nces_unitid = models.CharField(max_length=20, blank=True, db_index=True)
    nces_name = models.CharField(max_length=255, blank=True)
    nces_schoolyear = models.CharField(max_length=20, blank=True)
    institution_control = models.CharField(
        max_length=30,
        choices=InstitutionControl.choices,
        default=InstitutionControl.UNKNOWN,
        db_index=True,
    )
    institution_level = models.CharField(
        max_length=30,
        choices=InstitutionLevel.choices,
        default=InstitutionLevel.UNKNOWN,
        db_index=True,
    )
    locale = models.CharField(max_length=120, blank=True, db_index=True)

    logo = models.ImageField(upload_to='school-logos/', blank=True)

    road = models.BooleanField(default=False)
    mtb_xc = models.BooleanField(default=False)
    mtb_st = models.BooleanField(default=False)
    mtb_enduro = models.BooleanField(default=False)
    mtb_downhill = models.BooleanField(default=False)
    mtb_slalom = models.BooleanField(default=False)
    cyclocross = models.BooleanField(default=False)
    track = models.BooleanField(default=False)
    cycling_program_status = models.CharField(
        max_length=20,
        choices=CyclingProgramStatus.choices,
        default=CyclingProgramStatus.ACTIVE,
        db_index=True,
    )

    head_coach = models.CharField(max_length=255, blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)

    program_strengths = models.TextField(blank=True)
    avg_cost = models.CharField(max_length=100, blank=True)
    enrollment = models.CharField(max_length=100, blank=True)
    acceptance_rate = models.CharField(max_length=100, blank=True)
    graduation_rate = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class FavoriteSchool(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = 'private', 'Private'
        PUBLIC = 'public', 'Public'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_schools')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='favorited_by')
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PRIVATE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'school')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.email} -> {self.school.name}'


class ImportSchema(models.Model):
    name = models.CharField(max_length=150)
    version = models.CharField(max_length=50, default='v1')
    description = models.TextField(blank=True)
    target_model = models.CharField(max_length=100, default='schools.School')
    mapping_json = models.JSONField(default=dict)
    unique_key_fields = models.JSONField(default=list)
    required_fields = models.JSONField(default=list)
    defaults_json = models.JSONField(default=dict)
    type_rules = models.JSONField(default=dict)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'version']
        unique_together = ('name', 'version')

    def __str__(self) -> str:
        return f'{self.name} ({self.version})'


class DataLoadJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    schema = models.ForeignKey(ImportSchema, on_delete=models.PROTECT, related_name='jobs')
    uploaded_file = models.FileField(upload_to='data-loads/input/')
    dry_run = models.BooleanField(default=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    report_file = models.FileField(upload_to='data-loads/reports/', blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='data_load_jobs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        mode = 'Dry Run' if self.dry_run else 'Commit'
        return f'{mode} #{self.id} - {self.schema}'
