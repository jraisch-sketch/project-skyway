from django.db import models


class CMSNavigation(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class CMSPage(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    class Template(models.TextChoices):
        STANDARD = 'standard', 'Standard'
        WIDE = 'wide', 'Wide'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )
    summary = models.TextField(blank=True)
    body = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    template = models.CharField(max_length=20, choices=Template.choices, default=Template.STANDARD)
    show_title = models.BooleanField(default=True)
    navigation = models.ForeignKey(
        CMSNavigation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pages',
    )
    show_sidebar_navigation = models.BooleanField(default=True)
    nav_order = models.IntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nav_order', 'title']

    def __str__(self) -> str:
        return self.title


class CMSNavItem(models.Model):
    navigation = models.ForeignKey(CMSNavigation, on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    title = models.CharField(max_length=150)
    page = models.ForeignKey(CMSPage, on_delete=models.SET_NULL, null=True, blank=True, related_name='nav_items')
    external_url = models.URLField(blank=True)
    open_new_tab = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return f'{self.navigation.name}: {self.title}'


class CMSWidget(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.JSONField(default=list)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class CMSWidgetPlacement(models.Model):
    class Slot(models.TextChoices):
        CONTENT_TOP = 'content_top', 'Content Top'
        CONTENT_BOTTOM = 'content_bottom', 'Content Bottom'
        SIDEBAR = 'sidebar', 'Sidebar'
        HOME = 'home', 'Home'

    widget = models.ForeignKey(CMSWidget, on_delete=models.CASCADE, related_name='placements')
    page = models.ForeignKey(CMSPage, on_delete=models.CASCADE, null=True, blank=True, related_name='widget_placements')
    route_path = models.CharField(max_length=255, blank=True, help_text='Use values like / for homepage or /about')
    slot = models.CharField(max_length=30, choices=Slot.choices, default=Slot.CONTENT_BOTTOM)
    sort_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['slot', 'sort_order', 'id']

    def __str__(self) -> str:
        target = self.page.title if self.page_id else (self.route_path or 'unassigned')
        return f'{self.widget.name} -> {target} ({self.slot})'


class SiteConfiguration(models.Model):
    name = models.CharField(max_length=120, default='Default configuration')
    invitation_code_required = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site configuration'
        verbose_name_plural = 'Site configuration'

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        config, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'Default configuration',
                'invitation_code_required': True,
            },
        )
        return config
