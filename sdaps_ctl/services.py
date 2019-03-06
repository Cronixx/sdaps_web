from typing import Dict, BinaryIO
from models import Survey
from django.contrib.auth.models import User, Group

def create_survey(*,
                  name: str,
                  slug: str,
                  title: str="",
                  author: str="",
                  questionnaire: BinaryIO,
                  initialized: bool=False,
                  owner: User,
                  ) -> Survey:

    if Survey.objects.filter(slug=self.slug).exists():
        raise ValidationError('url slug is already in use')

    if not slug:
        slug = get_random_string(6,'ABCDEFGHIJKLMNOPQVWXYZ0123456789')

    survey = Survey.objects.create(
        name=name,
        slug=slug,
        title=title,
        author=author,
        questionnaire=questionnaire,
        initialized=initialized,
        owner=owner
    )

    return survey

