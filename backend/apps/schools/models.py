from django.conf import settings
from django.db import models


class Conference(models.Model):
    name = models.CharField(max_length=150, unique=True)
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

    logo = models.ImageField(upload_to='school-logos/', blank=True)

    road = models.BooleanField(default=False)
    mtb_xc = models.BooleanField(default=False)
    mtb_st = models.BooleanField(default=False)
    mtb_enduro = models.BooleanField(default=False)
    mtb_downhill = models.BooleanField(default=False)
    mtb_slalom = models.BooleanField(default=False)
    cyclocross = models.BooleanField(default=False)
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
