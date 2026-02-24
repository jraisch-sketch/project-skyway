from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cms.models import CMSNavItem, CMSNavigation, CMSPage, CMSWidget, CMSWidgetPlacement


class Command(BaseCommand):
    help = 'Seed a CMS page and widget for club vs varsity collegiate cycling content.'

    def handle(self, *args, **options):
        navigation, _ = CMSNavigation.objects.update_or_create(
            slug='guides',
            defaults={
                'name': 'Guides',
                'description': 'Educational content and reference guides.',
                'is_published': True,
            },
        )

        body = [
            {
                'type': 'paragraph',
                'text': (
                    'In collegiate cycling, teams generally compete under one of two institutional models: '
                    'Club or Varsity. Both can participate in USA Cycling collegiate competition, but the '
                    'difference is less about whether they race and more about how the program is organized, '
                    'funded, and supported by the school. USA Cycling formally recognizes both categories '
                    'in collegiate cycling.'
                ),
            },
            {
                'type': 'paragraph',
                'text': (
                    'For students and families evaluating programs, this distinction matters because it affects '
                    'things like coaching structure, scholarships, training expectations, and administrative support. '
                    'In practice, many collegiate cycling teams are club-based and student-led, while varsity teams '
                    'tend to operate more like traditional school athletic programs.'
                ),
            },
            {'type': 'heading', 'level': 2, 'text': 'Club Team'},
            {
                'type': 'paragraph',
                'text': (
                    'Most collegiate cycling programs in the U.S. are structured as club teams, which are typically '
                    'student-led organizations housed under campus recreation or student affairs. These teams often '
                    'compete intercollegiately, but students usually take on a larger role in organizing operations '
                    'such as leadership, budgeting, travel coordination, and recruitment.'
                ),
            },
            {
                'type': 'callout',
                'title': 'Clean Definition (Club)',
                'text': (
                    'A Club collegiate cycling team is a student-run campus sport organization that competes '
                    'in intercollegiate cycling and is typically administered through campus recreation/student '
                    'affairs rather than as a fully school-supported varsity athletics program.'
                ),
            },
            {'type': 'heading', 'level': 2, 'text': 'Varsity Team'},
            {
                'type': 'paragraph',
                'text': (
                    'A smaller number of colleges and universities sponsor cycling as a varsity program, which '
                    'usually means the school has made cycling a more formal athletic offering. USA Cycling varsity '
                    'language emphasizes institutional support, including an official coach and additional school resources.'
                ),
            },
            {
                'type': 'callout',
                'title': 'Clean Definition (Varsity)',
                'text': (
                    'A Varsity collegiate cycling team is a school-supported cycling program recognized by '
                    'USA Cycling that has an official coach and receives additional institutional resources/support '
                    'from the college or university. Varsity programs are the collegiate cycling programs eligible '
                    'to offer athletic scholarships.'
                ),
            },
            {'type': 'heading', 'level': 2, 'text': 'Comparison Table: Club vs. Varsity Collegiate Cycling'},
            {
                'type': 'table',
                'caption': 'Club vs Varsity comparison',
                'headers': ['Attribute', 'Club Team', 'Varsity Team'],
                'rows': [
                    ['Basic structure', 'Student-run sport club organization', 'School-supported athletic program'],
                    ['Primary campus home', 'Usually campus recreation/student affairs/club sports', 'Athletics department or equivalent institutional athletic structure'],
                    ['USA Cycling status', 'Recognized collegiate category', 'Recognized collegiate category'],
                    ['Coaching requirement', 'May have coaches/instructors, but often student-led operations', 'Official coach is part of varsity program definition'],
                    ['School resources/support', 'Varies widely; often limited/moderate', 'Generally higher and more formalized institutional support'],
                    ['Athletic scholarships', 'No (USA Cycling says only varsity programs can offer athletic scholarships)', 'Yes (eligible)'],
                    ['Student leadership role', 'Typically high (budgeting, organization, travel, recruitment)', 'Usually lower in operations; more staff/coach-led'],
                    ['Commitment style', 'Can be flexible to highly competitive depending on team', 'Often more structured and training-driven'],
                    ['Common recruiting signal', 'Club sports page/student organization page', 'Varsity team page/athletics-supported program page'],
                    ['Competition opportunities', 'Can compete in collegiate races/championship pathways', 'Can compete in collegiate races/championship pathways'],
                ],
            },
            {
                'type': 'paragraph',
                'text': 'Sources framework: USA Cycling varsity definition and collegiate FAQ, plus Penn State club sports descriptions.',
            },
        ]

        page, _ = CMSPage.objects.update_or_create(
            slug='collegiate-cycling-team-types-club-vs-varsity',
            defaults={
                'title': 'Collegiate Cycling Team Types: Club vs. Varsity',
                'summary': (
                    'Understand how club and varsity collegiate cycling programs differ in support, structure, '
                    'coaching, scholarships, and student leadership.'
                ),
                'body': body,
                'status': CMSPage.Status.PUBLISHED,
                'template': CMSPage.Template.WIDE,
                'navigation': navigation,
                'show_sidebar_navigation': True,
                'show_title': True,
                'nav_order': 10,
                'published_at': timezone.now(),
            },
        )

        CMSNavItem.objects.update_or_create(
            navigation=navigation,
            parent=None,
            title='Team Types: Club vs Varsity',
            defaults={
                'page': page,
                'external_url': '',
                'open_new_tab': False,
                'sort_order': 10,
                'is_published': True,
            },
        )

        widget, _ = CMSWidget.objects.update_or_create(
            slug='team-types-quick-guide',
            defaults={
                'name': 'Team Types Quick Guide',
                'title': 'Club vs Varsity: Quick Guide',
                'is_published': True,
                'body': [
                    {'type': 'paragraph', 'text': 'Club teams are usually student-led and organized through campus recreation. Varsity programs have formal school athletic support and official coaching.'},
                    {'type': 'list', 'style': 'unordered', 'items': [
                        'Club: high student leadership and flexible structure',
                        'Varsity: formal support and scholarship eligibility',
                        'Both: compete in collegiate cycling pathways',
                    ]},
                    {'type': 'link', 'text': 'Read full guide', 'href': '/content/collegiate-cycling-team-types-club-vs-varsity'},
                ],
            },
        )

        CMSWidgetPlacement.objects.update_or_create(
            widget=widget,
            page=None,
            route_path='/',
            slot=CMSWidgetPlacement.Slot.HOME,
            defaults={
                'sort_order': 10,
                'is_published': True,
            },
        )

        self.stdout.write(self.style.SUCCESS('Seeded CMS page, navigation item, and homepage widget.'))
