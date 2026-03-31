from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SuperUser, Staff
class SuperUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = SuperUser
        fields = ['id', 'name', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = SuperUser(**validated_data)
        user.set_password(password)  # hashing
        user.save()
        return user
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
class StaffSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    user = UserSerializer(read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id',
            'staff_id',
            'full_name',
            'email',
            'password',
            'phone',
            'dob',
            'position',
            'department',
            'hotel',
            'salary',
            'address',
            'photo_url',
            'emergency_contact',
            'joining_date',
            'status',
            'user'
        ]

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        # Create Django User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # Create Staff
        staff = Staff.objects.create(user=user, **validated_data)

        return staff