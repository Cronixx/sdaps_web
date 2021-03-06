#!/usr/bin/env python3
# sdaps_web - Webinterface for SDAPS
# Copyright(C) 2019, Benjamin Berg <benjamin@sipsolutions.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import os
import os.path
import datetime

import re

from .admin import SurveyAdmin

from django.urls import reverse

from django.views import generic
from django.views.decorators import csrf
from django.views.decorators.http import last_modified
from django.utils.decorators import method_decorator

from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.files.base import ContentFile
from wsgiref.util import FileWrapper

from django.shortcuts import render, get_object_or_404

from django.template import Context, loader

from . import models
from . import tasks
from . import forms
import io

import simplejson as json

from sdaps.model.survey import Survey as SDAPSSurvey
from sdaps import image
from sdaps import matrix
from sdaps import csvdata
from . import buddies
import cairo

def get_survey_or_404(request, slug, change=False, delete=False, review=False, upload=False):
    obj = get_object_or_404(models.Survey, slug=slug)

    if change:
        if not request.user.has_perm('sdaps_ctl.change_survey'):
            raise Http404
    if delete:
        if not request.user.has_perm('sdaps_ctl.delete_survey'):
            raise Http404
    if review:
        if not request.user.has_perm('sdaps_ctl.review_survey'):
            raise Http404
    if upload:
        if not request.user.has_perm('sdaps_ctl.change_uploadedfile'):
            raise Http404
    if not SurveyAdmin.has_permissions(request, obj):
        raise Http404

    return obj

class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class SurveyList(LoginRequiredMixin, generic.ListView):
    template_name = 'list.html'
    context_object_name = 'survey_list'

    def get_queryset(self):
        return SurveyAdmin.filter(self.request, models.Survey.objects).order_by('name')

@login_required
def survey_add_images(request, slug):
    if request.method == "POST":
        survey = get_survey_or_404(request, slug, change=True)

        # Queue file addition
        survey_id = str(survey.id)
        if tasks.add_images.apply_async(args=(survey_id, )):
            tasks.recognize_scan.apply_async(args=(survey_id, ))

        return HttpResponseRedirect(reverse('survey_overview', args=(survey.slug,)))

    # XXX: Everything else is not allowed
    raise Http404

@login_required
def survey_build(request, slug):
    if request.method == "POST":
        survey = get_survey_or_404(request, slug, change=True)

        if survey.initialized:
            raise Http404

        # Queue project creation
        tasks.build_survey.apply_async(args=(survey.id, ))

        return HttpResponseRedirect(reverse('survey_overview', args=(survey.slug,)))

    # XXX: Everything else is not allowed
    raise Http404

@login_required
def survey_report(request, slug):
    if request.method == "POST":
        survey = get_survey_or_404(request, slug, change=True)

        if not survey.initialized:
            raise Http404

        # Queue project creation
        tasks.generate_report.apply_async(args=(survey.id, ))

        return HttpResponseRedirect(reverse('survey_overview', args=(survey.slug,)))

    # XXX: Everything else is not allowed
    raise Http404

class SurveyCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = models.Survey
    form_class = forms.SurveyModelForm
    template_name = 'survey_create.html'
    success_url = '/surveys'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        self.model = form.save()
        self.model.save()
        survey_id = str(self.model.id)
        # Rendering the empty document
        if tasks.write_questionnaire.apply_async(args=(survey_id, )):
            tasks.render_questionnaire.apply_async(args=(survey_id, ))
        response = super().form_valid(form)
        return response



class SurveyDetail(LoginRequiredMixin, generic.DetailView):
    model = models.Survey
    template_name = 'overview.html'

    def get_object(self, *args, **kwargs):
        obj = generic.DetailView.get_object(self, *args, **kwargs)

        if obj and not SurveyAdmin.has_permissions(self.request, obj):
            raise Http404

        return obj

    def get_context_data(self, **kwargs):
        context = super(SurveyDetail, self).get_context_data(**kwargs)
        context['may_upload'] = self.request.user.has_perm('sdaps_ctl.change_uploadedfile')
        context['may_review'] = self.request.user.has_perm('sdaps_ctl.review_survey')
        context['may_change'] = self.request.user.has_perm('sdaps_ctl.change_survey')
        context['may_edit'] = self.request.user.has_perm('sdaps_ctl.change_survey')
        context['may_delete'] = self.request.user.has_perm('sdaps_ctl.delete_survey')
        return context

# File download last modified test
def survey_file_last_modification(request, slug, filename):
    survey = get_survey_or_404(request, slug)

    filename = os.path.join(survey.path, filename)
    if not os.path.isfile(filename):
        raise Http404

    return datetime.datetime.utcfromtimestamp((os.stat(filename).st_ctime))


## Questionnaire download
@last_modified(lambda *args, **kwargs: survey_file_last_modification(*args, filename='questionnaire.pdf', **kwargs))
@login_required
def questionnaire_download(request, slug):
    survey = get_survey_or_404(request, slug)

    filename = os.path.join(survey.path, 'questionnaire.pdf')
    if not os.path.isfile(filename):
        raise Http404

    wrapper = FileWrapper(open(filename, 'rb'))
    response = HttpResponse(wrapper, content_type='application/x-pdf')
    response['Content-Length'] = os.path.getsize(filename)
    response['Cache-Control'] = 'max-age=0, must-revalidate'

    return response

@last_modified(lambda *args, **kwargs: survey_file_last_modification(*args, filename='report.pdf', **kwargs))
@login_required
def report_download(request, slug):
    survey = get_survey_or_404(request, slug)

    filename = os.path.join(survey.path, 'report.pdf')
    if not os.path.isfile(filename):
        raise Http404

    wrapper = FileWrapper(open(filename, 'rb'))
    response = HttpResponse(wrapper, content_type='application/x-pdf')
    response['Content-Length'] = os.path.getsize(filename)

    return response

@last_modified(lambda *args, **kwargs: survey_file_last_modification(*args, filename='questionnaire.tex', **kwargs))
@login_required
def questionnaire_tex_download(request, slug):
    survey = get_survey_or_404(request, slug)

    filename = os.path.join(survey.path, 'questionnaire.tex')
    if not os.path.isfile(filename):
        raise Http404

    wrapper = FileWrapper(open(filename, 'rb'))
    response = HttpResponse(wrapper, content_type='text/x-tex')
    response['Content-Length'] = os.path.getsize(filename)

    return response

class SurveyUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    model = models.Survey
    form_class = forms.SurveyModelForm
    template_name = 'edit_questionnaire.html'
    success_url = '/surveys'

    def get_object(self, queryset=None):
        self.object = get_object_or_404(models.Survey, slug=self.kwargs['slug'])
        if self.object.initialized:
            raise Http404
        return self.object

    def form_valid(self, form):
        # Rendering the empty document does not really hurt ...
        form.save()
        survey_id = str(self.object.id)
        if tasks.write_questionnaire.apply_async(args=(survey_id, )):
            tasks.render_questionnaire.apply_async(args=(survey_id, ))
        response = super().form_valid(form)
        return response

@login_required
def delete(request, slug):
    survey = get_survey_or_404(request, slug, delete=True)

    yes_missing = False
    if request.method == "POST":
        if 'delete' in request.POST and request.POST['delete'] == "YES":
            survey.delete()
            return HttpResponseRedirect(reverse('surveys'))
        else:
            yes_missing = True

    return render(request, 'delete.html', { 'survey' : survey, 'yes_missing' : yes_missing })

@login_required
def questionnaire(request, slug):
    '''GET always gives you the questionnaire as json file. POST is accepted
    when the survey is not initialized for sending in the questionnaire draft
    via the editor. The json gets written as latex and then rendered for the
    editor preview.'''
    survey = get_survey_or_404(request, slug, change=True)

    # Get CSRF token, so that cookie will be included
    csrf.get_token(request)

    if request.method == 'POST':
        if survey.initialized:
            raise Http404
        else:
            survey.questionnaire = request.read()
            survey.save()

            survey_id = str(survey.id)
            if tasks.write_questionnaire.apply_async(args=(survey_id, )):
                tasks.render_questionnaire.apply_async(args=(survey_id, ))
            return HttpResponse(status=202)

    elif request.method == 'GET':
        return HttpResponse(survey.questionnaire, content_type="application/json")

@login_required
def survey_image(request, slug, filenum, page):
    # This function does not open the real SDAPS survey, as unpickling the data
    # is way to inefficient.
    survey = get_survey_or_404(request, slug, review=True)

    image_file = os.path.join(survey.path, "%s.tif" % (filenum,))

    if not os.path.exists(os.path.join(survey.path)):
        raise Http404

    surface = image.get_rgb24_from_tiff(image_file, int(page), False)
    if surface is None:
        raise Http404

    # Create PNG stream and return it
    response = HttpResponse(content_type='image/png')
    response['Cache-Control'] = 'private, max-age=3600'
    surface.write_to_png(response)

    return response

@login_required
def survey_review(request, slug):
    djsurvey = get_survey_or_404(request, slug, review=True)

    if not djsurvey.initialized:
        raise Http404

    #with models.LockedSurvey(djsurvey.id, 5):

    survey = SDAPSSurvey.load(djsurvey.path)

    context_dict = {
        'survey' : djsurvey,
        'sheet_count' : survey.sheet_count
    }

    return render(request, 'survey_review.html', context_dict)

@login_required
def survey_review_sheet(request, slug, sheet):
    djsurvey = get_survey_or_404(request, slug, review=True)

    # Get CSRF token, so that cookie will be included
    csrf.get_token(request)

    sheet = int(sheet)

    # XXX: Throw sane error in this case!
    #if djsurvey.active_task:
    #    raise Http404

    if not djsurvey.initialized:
        raise Http404

    # Now this is getting hairy, we need to unpickle the data :-(
    #with models.LockedSurvey(djsurvey.id, 5):

    survey = SDAPSSurvey.load(djsurvey.path)

    try:
        survey.goto_nth_sheet(sheet)
    except:
        raise Http404

    if request.method == 'POST':
        post_data = json.loads(request.read())
        data = post_data['data']

        survey.questionnaire.sdaps_ctl.set_data(data)

        survey.save()

    # Assume image is NUMBER.tif
    res = {
        'images' : [
            {
                'image' : int(image.filename[:-4]),
                'image_page' : image.tiff_page,
                'page' : image.page_number if image.survey_id == survey.survey_id else -1,
                'rotated' : image.rotated,
                'pxtomm' : tuple(image.matrix.px_to_mm()),
                'mmtopx' : tuple(image.matrix.mm_to_px()),
            } for image in survey.sheet.images if not image.ignored
        ],
        'data' : survey.questionnaire.sdaps_ctl.get_data()
    }

    return HttpResponse(json.dumps(res), content_type="application/json")


@login_required
def csv_download(request, slug):
    '''GET gives you the csv-file from an initialized survey.'''
    djsurvey = get_survey_or_404(request, slug, change=True)

    if not djsurvey.initialized:
        raise Http404

    survey = SDAPSSurvey.load(djsurvey.path)

    outdata = io.StringIO()
    csvdata.csvdata_export(survey, outdata, None)

    return HttpResponse(outdata.getvalue(), content_type="text/csv; charset=utf-8")



@login_required
def survey_upload(request, slug):
    survey = get_survey_or_404(request, slug, upload=True)

    csrf.get_token(request)

    if not survey.initialized:
        raise Http404

    context_dict = {
        'survey' : survey,
    }

    return render(request, 'survey_upload.html', context_dict)



class SurveyUploadPost(LoginRequiredMixin, generic.View):

    content_range_pattern = re.compile(r'^bytes (?P<start>\d+)-(?P<end>\d+)/(?P<size>\d+)')

    def ensure_valid_upload(self, upload):
        if upload.status != models.UPLOADING:
            return False
        return True

    def post(self, request, slug):
        survey = get_survey_or_404(self.request, slug, upload=True)

        #upload_id = request.POST.get('upload_id')

        single_file = len(request.FILES.getlist('files[]')) == 1
        result = list()
        range_header = None
        for chunk in request.FILES.getlist('files[]'):
            # Get the details about the chunk/upload
            content_range = request.META.get('HTTP_CONTENT_RANGE', '')
            if content_range:
                match = self.content_range_pattern.match(content_range)
                if not match:
                    result.append({ 'name' : chunk.name, 'error' : 'Broken or wrong content range.' })
                    continue

                start = int(match.group('start'))
                end = int(match.group('end'))
                length = int(match.group('size'))

                size = end - start + 1
            else:
                start = 0
                size = None

                length = chunk.size

            # TODO: Figure out a way that name collisions work!
            upload = models.UploadedFile.objects.filter(survey=survey, filename=chunk.name).first()

            if upload is not None:
                if not self.ensure_valid_upload(upload):
                    result.append({ 'name' : chunk.name, 'error' : 'File already uploaded or in an error state.' })
                    continue

            else:
                # Create a new upload
                upload = models.UploadedFile(survey=survey, filename=chunk.name, filesize=length)
                # Ensure PK is created
                upload.save()
                upload.file.save(name='', content=ContentFile(''), save=True)

            upload.append_chunk(chunk, offset=start, length=size)

            upload.save()

            result.append(upload.get_description())

            if single_file:
                # Send back the range that is already uploaded
                range_header = 'bytes %i-%i' % (0, upload.file.size-1)

        # only include the uploaded files in response
        result = {
            'files' : result,
        }

        response = HttpResponse(json.dumps(result), content_type="application/json")
        if range_header is not None:
            response['Range'] = range_header

        return response

    def generate_response(self, survey):
        files = list(survey.uploads.all())
        result = []
        for f in files:
            result.append(f.get_description())

        result = {
            'files' : result,
        }

        return HttpResponse(json.dumps(result), content_type="application/json")


    def get(self, request, slug):
        survey = get_survey_or_404(self.request, slug, upload=True)

        return self.generate_response(survey)


class SurveyUploadFile(LoginRequiredMixin, generic.View):

    def delete(self, request, slug, filename):
        survey = get_survey_or_404(self.request, slug, upload=True)

        upload = models.UploadedFile.objects.filter(survey=survey, filename=filename).first()
        upload.delete()

        return HttpResponse(json.dumps({ 'files' : [ { filename : True }] }), content_type="application/json")


    def get(self, request, slug, filename):
        survey = get_survey_or_404(self.request, slug, upload=True)

        upload = models.UploadedFile.objects.filter(survey=survey, filename=filename).first()

        if upload is None:
            raise Http404

        # XXX: Store mimetype and return correct one here!
        return HttpResponse(upload.file, content_type="application/binary")