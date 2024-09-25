from django.db import migrations
from django.contrib.postgres.search import SearchVector

def populate_search_vector(apps, schema_editor):
    User = apps.get_model('social_network', 'User')
    User.objects.update(search_vector=SearchVector('name', 'email'))

class Migration(migrations.Migration):

    dependencies = [
        ('social_network', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_search_vector),
    ]