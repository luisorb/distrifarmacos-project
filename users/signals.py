from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


BASE_GROUPS = ("digitador", "gestor_calidad", "admin_proyecto")


@receiver(post_migrate)
def create_base_groups(sender, **kwargs):
    if getattr(sender, "name", None) != "users":
        return

    for group_name in BASE_GROUPS:
        Group.objects.get_or_create(name=group_name)