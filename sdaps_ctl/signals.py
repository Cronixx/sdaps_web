from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Survey

@receiver(post_save, sender=Survey)
def create_survey_dir(sender, instance, created, **kwargs):
    if not created:
        return

    tasks.create_survey(instance)

@receiver(post_delete, sender=Survey)
def delete_moves_survey_dir(sender, instance, using, **kwargs):
    """This signal handler moves the project directory into the "deleted"
    directory whenever a survey is removed from the database."""

    path = instance.path

    if path and os.path.isdir(path):
        delpath = os.path.join(settings.SDAPS_PROJECT_ROOT, 'deleted')

        # Make sure the "deleted" directory exists
        if not os.path.isdir(delpath):
            os.mkdir(delpath)

        # And rename/move the old directory
        os.rename(path, os.path.join(delpath, datetime.datetime.now().strftime('%Y%m%d-%H%M') + '-' + str(instance.id)))

@receiver(post_delete, sender=Survey):
def delete_uploaded_file(sender, instance, using, **kwargs):
    instance.file.delete(save=False)