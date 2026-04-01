from django.db import migrations


def set_admin_roles(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(is_staff=True).update(role='admin')
    User.objects.filter(is_superuser=True).update(role='admin')


def revert_admin_roles(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(role='admin', is_staff=False, is_superuser=False).update(role='client')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_admin_roles, revert_admin_roles),
    ]
