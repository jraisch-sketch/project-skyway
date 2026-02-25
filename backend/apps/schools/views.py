from django.db.models import Case, Count, FloatField, IntegerField, Q, Value, When
from django.db.models.functions import ACos, Cast, Cos, Radians, Sin
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Conference, FavoriteSchool, School
from .permissions import FavoritesPermission
from .serializers import (
    ConferenceSerializer,
    FavoriteSchoolSerializer,
    SchoolDetailSerializer,
    SchoolListSerializer,
)


DISCIPLINE_FIELD_MAP = {
    'road': 'road',
    'mtb_xc': 'mtb_xc',
    'mtb_st': 'mtb_st',
    'mtb_enduro': 'mtb_enduro',
    'mtb_downhill': 'mtb_downhill',
    'mtb_slalom': 'mtb_slalom',
    'cyclocross': 'cyclocross',
    'track': 'track',
}


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = School.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SchoolDetailSerializer
        return SchoolListSerializer

    def get_queryset(self):
        qs = School.objects.all()
        q = self.request.query_params.get('q', '').strip()
        team_type = self.request.query_params.get('team_type', '').strip()
        conference = self.request.query_params.get('conference', '').strip()
        state = self.request.query_params.get('state', '').strip()
        sort = self.request.query_params.get('sort', 'relevance').strip()
        disciplines = self.request.query_params.get('disciplines', '').strip()

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(city__icontains=q) |
                Q(state__icontains=q)
            ).annotate(
                relevance=Case(
                    When(name__iexact=q, then=Value(100)),
                    When(name__istartswith=q, then=Value(80)),
                    When(city__istartswith=q, then=Value(60)),
                    default=Value(40),
                    output_field=IntegerField(),
                )
            )
        else:
            qs = qs.annotate(relevance=Value(0, output_field=IntegerField()))

        if team_type:
            qs = qs.filter(team_type__iexact=team_type)
        if conference:
            qs = qs.filter(conference__name__iexact=conference)
        if state:
            qs = qs.filter(state__iexact=state)

        if disciplines:
            requested = [d.strip().lower() for d in disciplines.split(',') if d.strip()]
            for discipline in requested:
                field_name = DISCIPLINE_FIELD_MAP.get(discipline)
                if field_name:
                    qs = qs.filter(**{field_name: True})

        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = self.request.query_params.get('radius')

        if lat and lng:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
                qs = qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True).annotate(
                    distance=Value(3959, output_field=FloatField())
                    * ACos(
                        Cos(Radians(Value(lat_f)))
                        * Cos(Radians(Cast('latitude', FloatField())))
                        * Cos(Radians(Cast('longitude', FloatField())) - Radians(Value(lng_f)))
                        + Sin(Radians(Value(lat_f))) * Sin(Radians(Cast('latitude', FloatField())))
                    )
                )
                if radius:
                    try:
                        radius_f = float(radius)
                        if radius_f > 0:
                            qs = qs.filter(distance__lte=radius_f)
                    except ValueError:
                        pass
            except ValueError:
                qs = qs.annotate(distance=Value(None, output_field=FloatField()))
        else:
            qs = qs.annotate(distance=Value(None, output_field=FloatField()))

        if sort == 'distance':
            qs = qs.order_by('distance', '-relevance', 'name')
        elif sort == 'alphabetical':
            qs = qs.order_by('name')
        else:
            qs = qs.order_by('-relevance', 'name')

        return qs


class FavoriteSchoolViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSchoolSerializer
    permission_classes = [FavoritesPermission]

    def get_queryset(self):
        if self.action == 'list' and self.request.query_params.get('public') == 'true':
            return FavoriteSchool.objects.filter(visibility=FavoriteSchool.Visibility.PUBLIC).select_related('school', 'user')
        return FavoriteSchool.objects.filter(user=self.request.user).select_related('school')

    def perform_create(self, serializer):
        serializer.save()


@api_view(['GET'])
def filter_options(request):
    conferences = (
        School.objects.exclude(conference__isnull=True)
        .values_list('conference__name', flat=True)
        .distinct()
        .order_by('conference__name')
    )
    states = School.objects.exclude(state='').values_list('state', flat=True).distinct().order_by('state')
    return Response(
        {
            'team_types': [choice[0] for choice in School.TeamType.choices],
            'conferences': list(conferences),
            'states': list(states),
            'disciplines': list(DISCIPLINE_FIELD_MAP.keys()),
            'sort_options': ['relevance', 'distance', 'alphabetical'],
        }
    )


@api_view(['GET'])
def conferences_list(request):
    conferences = Conference.objects.annotate(team_count=Count('schools')).order_by('name')
    serializer = ConferenceSerializer(conferences, many=True)
    return Response(serializer.data)
