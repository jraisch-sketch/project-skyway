from rest_framework import serializers

from .models import Conference, FavoriteSchool, School


class ConferenceSerializer(serializers.ModelSerializer):
    team_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conference
        fields = ('id', 'name', 'long_name', 'acronym', 'description', 'team_count')


class SchoolListSerializer(serializers.ModelSerializer):
    conference = serializers.CharField(source='conference.name', read_only=True, default='')

    class Meta:
        model = School
        fields = (
            'id',
            'name',
            'team_type',
            'conference',
            'city',
            'state',
            'latitude',
            'longitude',
            'road',
            'mtb',
            'cyclocross',
            'track',
            'cycling_program_status',
            'school_website',
            'athletic_dept_website',
            'cycling_website',
            'logo',
        )


class SchoolDetailSerializer(serializers.ModelSerializer):
    conference = serializers.CharField(source='conference.name', read_only=True, default='')

    class Meta:
        model = School
        fields = (
            'id',
            'name',
            'proto_data',
            'conference',
            'team_type',
            'roster_male',
            'roster_female',
            'contact_email',
            'date_joined',
            'last_current',
            'mascot',
            'school_website',
            'athletic_dept_website',
            'cycling_website',
            'street_address',
            'city',
            'state',
            'zip_code',
            'address_complete',
            'geocode_raw',
            'latitude',
            'longitude',
            'geocode_status',
            'geocode_confidence',
            'geocode_query',
            'geocode_source',
            'geocode_source_url',
            'geocode_needs_review',
            'geocode_notes',
            'geocode_updated_at',
            'nces_unitid',
            'nces_name',
            'nces_schoolyear',
            'institution_control',
            'institution_level',
            'locale',
            'logo',
            'road',
            'mtb',
            'cyclocross',
            'track',
            'cycling_program_status',
            'head_coach',
            'instagram',
            'facebook',
            'twitter',
            'program_strengths',
            'avg_cost',
            'enrollment',
            'acceptance_rate',
            'graduation_rate',
            'created_at',
            'updated_at',
        )


class FavoriteSchoolSerializer(serializers.ModelSerializer):
    school = SchoolListSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), source='school', write_only=True)

    class Meta:
        model = FavoriteSchool
        fields = ('id', 'school', 'school_id', 'visibility', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        favorite, _ = FavoriteSchool.objects.update_or_create(
            user=user,
            school=validated_data['school'],
            defaults={'visibility': validated_data.get('visibility', FavoriteSchool.Visibility.PRIVATE)},
        )
        return favorite
