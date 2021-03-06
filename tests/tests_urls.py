from django.test import SimpleTestCase
from django.urls import reverse, resolve
from sdaps_ctl.views import *

class TestUrls(SimpleTestCase):
    def test_surveylist_url_resolves(self):
        url = reverse('surveys')
        self.assertEquals(resolve(url).func.view_class, SurveyList)

    def test_surveycreate_url_resolves(self):
        url = reverse('survey_create')
        self.assertEquals(resolve(url).func.view_class, SurveyCreateView)

    def test_surveyoverview_url_resolves(self):
        url = reverse('survey_overview', args=['some-slug'])
        self.assertEquals(resolve(url).func.view_class, SurveyDetail)

    def test_surveycsvdownload_url_resolves(self):
        url = reverse('csv_download', args=['some-slug'])
        self.assertEquals(resolve(url).func, csv_download)

    def test_surveyquestionnairedownload_url_resolves(self):
        url = reverse('questionnaire_download', args=['some-slug'])
        self.assertEquals(resolve(url).func, questionnaire_download)

    def test_surveyquestionnairetexdownload_url_resolves(self):
        url = reverse('questionnaire_tex_download', args=['some-slug'])
        self.assertEquals(resolve(url).func, questionnaire_tex_download)

    def test_surveyreportdownload_url_resolves(self):
        url = reverse('report_download', args=['some-slug'])
        self.assertEquals(resolve(url).func, report_download)

    def test_surveyquestionnaireedit_url_resolves(self):
        url = reverse('questionnaire_edit', args=['some-slug'])
        self.assertEquals(resolve(url).func.view_class, SurveyUpdateView)

    def test_surveydelete_url_resolves(self):
        url = reverse('survey_delete', args=['some-slug'])
        self.assertEquals(resolve(url).func, delete)

    def test_surveyquestionnairepost_url_resolves(self):
        url = reverse('questionnaire_post', args=['some-slug'])
        self.assertEquals(resolve(url).func, questionnaire)

    def test_surveyreview_url_resolves(self):
        url = reverse('survey_review', args=['some-slug'])
        self.assertEquals(resolve(url).func, survey_review)

    def test_surveyreviewsheet_url_resolves(self):
        url = reverse('survey_review_sheet', kwargs={'slug':'some-slug', 'sheet': 1})
        self.assertEquals(resolve(url).func, survey_review_sheet)

    def test_surveyimage_url_resolves(self):
        url = reverse('survey_image', kwargs={'slug':'some-slug', 'filenum': 1, 'page': 1})
        self.assertEquals(resolve(url).func, survey_image)

    def test_surveybuild_url_resolves(self):
        url = reverse('survey_build', args=['some-slug'])
        self.assertEquals(resolve(url).func, survey_build)

    def test_surveyreport_url_resolves(self):
        url = reverse('survey_report', args=['some-slug'])
        self.assertEquals(resolve(url).func, survey_report)

    def test_surveyaddimages_url_resolves(self):
        url = reverse('survey_add_images', args=['some-slug'])
        self.assertEquals(resolve(url).func, survey_add_images)

    def test_surveyupload_url_resolves(self):
        url = reverse('survey_upload', args=['some-slug'])
        self.assertEquals(resolve(url).func, survey_upload)

    def test_surveyuploadpost_url_resolves(self):
        url = reverse('survey_upload_post', args=['some-slug'])
        self.assertEquals(resolve(url).func.view_class, SurveyUploadPost)

    def test_surveyuploadfile_url_resolves(self):
        url = reverse('survey_upload_file', args={'slug':'some-slug', 'filename': 1})
        self.assertEquals(resolve(url).func.view_class, SurveyUploadFile)

    def test_redirecttosurveylist_url_resolves(self):
        url = reverse('survey_upload_file', args={'slug':'some-slug', 'filename': 1})
        self.assertEquals(resolve(url).func.view_class, SurveyUploadFile) 