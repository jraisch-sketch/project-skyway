from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cms.models import CMSNavItem, CMSNavigation, CMSPage


class Command(BaseCommand):
    help = 'Seed CMS pages and primary footer/header navigation structures.'

    def handle(self, *args, **options):
        top_nav, _ = CMSNavigation.objects.update_or_create(
            slug='main-top-nav',
            defaults={
                'name': 'Main Top Navigation',
                'description': 'Primary header navigation for public pages.',
                'is_published': True,
            },
        )

        about_page, _ = CMSPage.objects.update_or_create(
            slug='about-skyway',
            defaults={
                'title': 'About Skyway',
                'summary': 'Learn how Skyway helps students and families evaluate collegiate cycling programs.',
                'body': [
                    {
                        'type': 'paragraph',
                        'text': 'Collegiate Cycling Finder helps students and families explore college cycling programs by conference, location, team type, and discipline.',
                    },
                    {
                        'type': 'paragraph',
                        'text': 'Use our interactive map, school profiles, and conference navigation pages to quickly find cycling programs that fit your goals.',
                    },
                ],
                'status': CMSPage.Status.PUBLISHED,
                'published_at': timezone.now(),
                'show_sidebar_navigation': False,
                'navigation': top_nav,
                'nav_order': 10,
            },
        )

        team_types_page, _ = CMSPage.objects.update_or_create(
            slug='collegiate-cycling-team-types-club-vs-varsity',
            defaults={
                'title': 'Collegiate Cycling Team Types: Club vs. Varsity',
                'summary': 'Understand how club and varsity collegiate cycling programs differ in structure, support, and expectations.',
                'status': CMSPage.Status.PUBLISHED,
                'published_at': timezone.now(),
                'show_sidebar_navigation': True,
                'navigation': top_nav,
                'nav_order': 20,
            },
        )

        all_colleges_page, _ = CMSPage.objects.update_or_create(
            slug='all-colleges',
            defaults={
                'title': 'All Colleges',
                'summary': 'Browse all listed cycling schools through the structured directory pages.',
                'body': [
                    {
                        'type': 'paragraph',
                        'text': 'Browse colleges using navigation paths that mirror search filters. Use conference, team type, and state pages to find the best college cycling programs.',
                    },
                    {'type': 'link', 'text': 'Open School Table of Contents', 'href': '/schools/table-of-contents'},
                    {'type': 'link', 'text': 'Browse Varsity Cycling Schools', 'href': '/schools/by-team-type/varsity'},
                    {'type': 'link', 'text': 'Browse Club Cycling Schools', 'href': '/schools/by-team-type/club'},
                ],
                'status': CMSPage.Status.PUBLISHED,
                'published_at': timezone.now(),
                'show_sidebar_navigation': False,
                'navigation': top_nav,
                'nav_order': 30,
            },
        )

        correction_page, _ = CMSPage.objects.update_or_create(
            slug='submit-a-correction',
            defaults={
                'title': 'Submit a Correction',
                'summary': 'Report school or conference data issues for review.',
                'body': [
                    {
                        'type': 'paragraph',
                        'text': 'Found an issue in school or conference information? Please email correction details to info@yjroutdoors.com.',
                    },
                    {
                        'type': 'paragraph',
                        'text': 'Include the school/conference name, the current value shown, and the corrected value for the fastest review.',
                    },
                ],
                'status': CMSPage.Status.PUBLISHED,
                'published_at': timezone.now(),
                'show_sidebar_navigation': False,
                'navigation': top_nav,
                'nav_order': 40,
            },
        )

        blog_page, _ = CMSPage.objects.update_or_create(
            slug='skyway-blog',
            defaults={
                'title': 'Blog',
                'summary': 'News, updates, and guidance from Skyway Collegiate Cycling Finder.',
                'body': [
                    {
                        'type': 'paragraph',
                        'text': 'Skyway updates, conference insights, and college cycling guidance will appear here.',
                    },
                    {'type': 'paragraph', 'text': 'Check back soon for new posts.'},
                ],
                'status': CMSPage.Status.PUBLISHED,
                'published_at': timezone.now(),
                'show_sidebar_navigation': False,
                'navigation': top_nav,
                'nav_order': 50,
            },
        )

        contact_page, _ = CMSPage.objects.update_or_create(
            slug='contact-us',
            defaults={
                'title': 'Contact Us',
                'summary': 'Contact Skyway for listing support and data update questions.',
                'body': [
                    {'type': 'paragraph', 'text': 'Questions about school listings, account support, or data updates?'},
                    {'type': 'paragraph', 'text': 'Email: support@projectskyway.org'},
                    {
                        'type': 'paragraph',
                        'text': 'We review conference and school data updates regularly and can help you find the right cycling program path.',
                    },
                ],
                'status': CMSPage.Status.PUBLISHED,
                'published_at': timezone.now(),
                'show_sidebar_navigation': False,
                'navigation': top_nav,
                'nav_order': 60,
            },
        )

        items = [
            ('About Skyway', about_page, '', 10),
            ('Team Type Guide', team_types_page, '', 20),
            ('All Colleges', all_colleges_page, '', 30),
            ('Submit a Correction', correction_page, '', 40),
            ('Blog', blog_page, '', 50),
            ('Contact Us', contact_page, '', 60),
        ]

        for title, page, external_url, sort_order in items:
            CMSNavItem.objects.update_or_create(
                navigation=top_nav,
                parent=None,
                title=title,
                defaults={
                    'page': page,
                    'external_url': external_url,
                    'open_new_tab': False,
                    'sort_order': sort_order,
                    'is_published': True,
                },
            )

        footer_nav, _ = CMSNavigation.objects.update_or_create(
            slug='main-footer-nav',
            defaults={
                'name': 'Main Footer Navigation',
                'description': 'Primary footer navigation links.',
                'is_published': True,
            },
        )

        footer_items = [
            ('About', about_page, '', 10),
            ('Contact', contact_page, '', 20),
            ('School Table of Contents', None, '/schools/table-of-contents', 30),
        ]

        for title, page, external_url, sort_order in footer_items:
            CMSNavItem.objects.update_or_create(
                navigation=footer_nav,
                parent=None,
                title=title,
                defaults={
                    'page': page,
                    'external_url': external_url,
                    'open_new_tab': False,
                    'sort_order': sort_order,
                    'is_published': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Seeded main top/footer CMS pages and navigation.'))
