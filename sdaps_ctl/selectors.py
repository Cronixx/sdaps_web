from sdaps_ctl.models import Survey
from django.shortcuts import get_object_or_404
from .admin import SurveyAdmin

def get_survey(request, slug, change=False, delete=False, review=False, upload=False):
    obj = get_object_or_404(Survey, slug=slug)

    if change:
        if not request.user.has_perm('sdaps_ctl.change_survey'):
            return False
    if delete:
        if not request.user.has_perm('sdaps_ctl.delete_survey'):
            return False
    if review:
        if not request.user.has_perm('sdaps_ctl.review_survey'):
            return False
    if upload:
        if not request.user.has_perm('sdaps_ctl.change_uploadedfile'):
            return False
    if not SurveyAdmin.has_permissions(request, obj):
        return False

    return obj

def get_initialized_survey(request, slug, change=False, delete=False, review=False, upload=False):
    obj = get_survey(request, slug, change=False, delete=False, review=False, upload=False)

    if not obj.initialized:
        return False
    return obj

def get_non_initialized_survey(request, slug, change=False, delete=False, review=False, upload=False):
    obj = get_survey(request, slug, change=False, delete=False, review=False, upload=False)

    if not obj.initialized:
        return obj
    return False

def get_survey_list(request):
    return SurveyAdmin.filter(request, Survey.objects).order_by('name')