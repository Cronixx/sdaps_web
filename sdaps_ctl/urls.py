from django.urls import path, re_path
from django.contrib.auth.decorators import permission_required

from sdaps_ctl.views import *

urlpatterns = [
        # generalprepost_matters: General views and Pre-/Postprocessing
        path(route='', view=SurveyList.as_view(), name='surveys'),
        path(route='create/', view=permission_required('sdaps_ctl.add_survey')(SurveyCreateView.as_view()), name='survey_create'),
        path(route='<slug:slug>/', view=SurveyDetail.as_view(), name='survey_overview'),
        path(route='<slug:slug>/delete/', view=delete, name='survey_delete'),

        # designinit_matter: Designing the questionnaire and initializing
        path(route='<slug:slug>/edit/', view=SurveyUpdateView.as_view(), name='questionnaire_edit'),
        path(route='<slug:slug>/edit/questionnaire/', view=questionnaire, name='questionnaire_post'),
        path(route='<slug:slug>/questionnaire.pdf', view=questionnaire_download, name='questionnaire_download'),
        path(route='<slug:slug>/questionnaire.tex', view=questionnaire_tex_download, name='questionnaire_tex_download'),
        path(route='<slug:slug>/build/', view=survey_build, name='survey_build'),

        # upload_matter: Uploading scans for review
        path(route='<slug:slug>/add_images/', view=survey_add_images, name='survey_add_images'),
        path(route='<slug:slug>/upload/', view=survey_upload, name='survey_upload'),
        path(route='<slug:slug>/upload/post/', view=SurveyUploadPost.as_view(), name='survey_upload_post'),
        re_path(route=r'^(?P<slug>\w+)/upload/post/(?P<filename>.+)$', view=SurveyUploadFile.as_view(), name='survey_upload_file'),

        # review_matter: Review the scans
        path(route='<slug:slug>/review/', view=survey_review, name='survey_review'),
        path(route='<slug:slug>/review/<int:sheet>/', view=survey_review_sheet, name='survey_review_sheet'),
        path(route='<slug:slug>/images/<int:filenum>/<int:page>/', view=survey_image, name='survey_image'),

        # results_matters: Generate results and reports
        path(route='<slug:slug>/report/',  view=survey_report, name='survey_report'),
        path(route='<slug:slug>/report.pdf', view=report_download, name='report_download'),
        path(route='<slug:slug>/data.csv', view=csv_download, name='csv_download'),
    ]
