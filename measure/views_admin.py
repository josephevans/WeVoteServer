# measure/views_admin.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-


from .controllers import measures_import_from_master_server
from .models import ContestMeasure
from .serializers import ContestMeasureSerializer
from admin_tools.views import redirect_to_sign_in_page
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.shortcuts import render
from election.models import Election
from exception.models import handle_record_found_more_than_one_exception,\
    handle_record_not_found_exception, handle_record_not_saved_exception
from rest_framework.views import APIView
from rest_framework.response import Response
from voter.models import voter_has_authority
import wevote_functions.admin
from wevote_functions.functions import convert_to_int, positive_value_exists

logger = wevote_functions.admin.get_logger(__name__)


# This page does not need to be protected.
class MeasuresSyncOutView(APIView):
    def get(self, request, format=None):
        google_civic_election_id = convert_to_int(request.GET.get('google_civic_election_id', 0))

        contest_measure_list = ContestMeasure.objects.all()
        if positive_value_exists(google_civic_election_id):
            contest_measure_list = contest_measure_list.filter(google_civic_election_id=google_civic_election_id)

        serializer = ContestMeasureSerializer(contest_measure_list, many=True)
        return Response(serializer.data)


@login_required
def measures_import_from_master_server_view(request):
    google_civic_election_id = convert_to_int(request.GET.get('google_civic_election_id', 0))
    state_code = request.GET.get('state_code', '')

    results = measures_import_from_master_server(request, google_civic_election_id)

    if not results['success']:
        messages.add_message(request, messages.ERROR, results['status'])
    else:
        messages.add_message(request, messages.INFO, 'Measures import completed. '
                                                     'Saved: {saved}, Updated: {updated}, '
                                                     'Master data not imported (local duplicates found): '
                                                     '{duplicates_removed}, '
                                                     'Not processed: {not_processed}'
                                                     ''.format(saved=results['saved'],
                                                               updated=results['updated'],
                                                               duplicates_removed=results['duplicates_removed'],
                                                               not_processed=results['not_processed']))
    return HttpResponseRedirect(reverse('admin_tools:sync_dashboard', args=()) + "?google_civic_election_id=" +
                                str(google_civic_election_id) + "&state_code=" + str(state_code))


@login_required
def measure_list_view(request):
    authority_required = {'verified_volunteer'}  # admin, verified_volunteer
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    messages_on_stage = get_messages(request)
    google_civic_election_id = convert_to_int(request.GET.get('google_civic_election_id', 0))

    try:
        measure_list = ContestMeasure.objects.order_by('measure_title')
        if positive_value_exists(google_civic_election_id):
            measure_list = measure_list.filter(google_civic_election_id=google_civic_election_id)
    except ContestMeasure.DoesNotExist:
        # This is fine
        measure_list = ContestMeasure()
        pass

    election_list = Election.objects.order_by('-election_day_text')

    template_values = {
        'messages_on_stage': messages_on_stage,
        'measure_list': measure_list,
        'election_list': election_list,
        'google_civic_election_id': google_civic_election_id,
    }
    return render(request, 'measure/measure_list.html', template_values)


@login_required
def measure_new_view(request):
    authority_required = {'verified_volunteer'}  # admin, verified_volunteer
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    google_civic_election_id = request.GET.get('google_civic_election_id', 0)

    try:
        measure_list = ContestMeasure.objects.order_by('measure_title')
        if positive_value_exists(google_civic_election_id):
            measure_list = measure_list.filter(google_civic_election_id=google_civic_election_id)
    except ContestMeasure.DoesNotExist:
        # This is fine
        measure_list = ContestMeasure()
        pass

    messages_on_stage = get_messages(request)
    template_values = {
        'messages_on_stage':        messages_on_stage,
        'google_civic_election_id': google_civic_election_id,
        'measure_list':             measure_list,
    }
    return render(request, 'measure/measure_edit.html', template_values)


@login_required
def measure_edit_view(request, measure_id):
    authority_required = {'verified_volunteer'}  # admin, verified_volunteer
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    messages_on_stage = get_messages(request)
    measure_id = convert_to_int(measure_id)
    measure_on_stage_found = False
    try:
        measure_on_stage = ContestMeasure.objects.get(id=measure_id)
        measure_on_stage_found = True
    except ContestMeasure.MultipleObjectsReturned as e:
        handle_record_found_more_than_one_exception(e, logger=logger)
        measure_on_stage = ContestMeasure()
    except ContestMeasure.DoesNotExist:
        # This is fine, create new
        measure_on_stage = ContestMeasure()
        pass

    if measure_on_stage_found:
        template_values = {
            'messages_on_stage':    messages_on_stage,
            'measure':              measure_on_stage,
        }
    else:
        template_values = {
            'messages_on_stage':    messages_on_stage,
        }
    return render(request, 'measure/measure_edit.html', template_values)


@login_required
def measure_edit_process_view(request):
    """
    Process the new or edit measure forms
    :param request:
    :return:
    """
    authority_required = {'verified_volunteer'}  # admin, verified_volunteer
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    measure_id = convert_to_int(request.POST['measure_id'])
    measure_title = request.POST.get('measure_title', False)
    google_civic_measure_title = request.POST.get('google_civic_measure_title', False)
    measure_subtitle = request.POST.get('measure_subtitle', False)
    measure_text = request.POST.get('measure_text', False)
    measure_url = request.POST.get('measure_url', False)
    google_civic_election_id = request.POST.get('google_civic_election_id', 0)
    maplight_id = request.POST.get('maplight_id', False)
    vote_smart_id = request.POST.get('vote_smart_id', False)
    state_code = request.POST.get('state_code', False)

    # Check to see if this measure exists
    measure_on_stage_found = False
    measure_on_stage = ContestMeasure()
    error = False
    try:
        if positive_value_exists(measure_id):
            measure_query = ContestMeasure.objects.filter(id=measure_id)
            if len(measure_query):
                measure_on_stage = measure_query[0]
                measure_on_stage_found = True
    except Exception as e:
        messages.add_message(request, messages.ERROR, 'There was an error trying to find this measure.')
        error = True

    if not error:
        try:
            if measure_on_stage_found:
                # Update
                if measure_title is not False:
                    measure_on_stage.measure_title = measure_title
                if google_civic_measure_title is not False:
                    measure_on_stage.google_civic_measure_title = google_civic_measure_title
                if measure_subtitle is not False:
                    measure_on_stage.measure_subtitle = measure_subtitle
                if measure_text is not False:
                    measure_on_stage.measure_text = measure_text
                if measure_url is not False:
                    measure_on_stage.measure_url = measure_url
                if google_civic_election_id is not False:
                    measure_on_stage.google_civic_election_id = google_civic_election_id
                if maplight_id is not False:
                    measure_on_stage.maplight_id = maplight_id
                if vote_smart_id is not False:
                    measure_on_stage.vote_smart_id = vote_smart_id
                if state_code is not False:
                    measure_on_stage.state_code = state_code

                measure_on_stage.save()
                messages.add_message(request, messages.INFO, 'ContestMeasure updated.')
            else:
                # Create new
                measure_on_stage = ContestMeasure(
                    measure_title=measure_title,
                    google_civic_measure_title=google_civic_measure_title,
                    measure_subtitle=measure_subtitle,
                    measure_text=measure_text,
                    measure_url=measure_url,
                    google_civic_election_id=google_civic_election_id,
                    state_code=state_code,
                    maplight_id=maplight_id,
                    vote_smart_id=vote_smart_id,
                )
                measure_on_stage.save()
                messages.add_message(request, messages.INFO, 'New measure saved.')
        except Exception as e:
            messages.add_message(request, messages.ERROR, 'Could not save measure.')

    return HttpResponseRedirect(reverse('measure:measure_list', args=()) +
                                "?google_civic_election_id=" + str(google_civic_election_id))


@login_required
def measure_summary_view(request, measure_id):
    authority_required = {'verified_volunteer'}  # admin, verified_volunteer
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    messages_on_stage = get_messages(request)
    measure_id = convert_to_int(measure_id)
    measure_on_stage_found = False
    measure_on_stage = ContestMeasure()
    google_civic_election_id = convert_to_int(request.GET.get('google_civic_election_id', 0))
    try:
        measure_on_stage = ContestMeasure.objects.get(id=measure_id)
        measure_on_stage_found = True
    except ContestMeasure.MultipleObjectsReturned as e:
        handle_record_found_more_than_one_exception(e, logger=logger)
    except ContestMeasure.DoesNotExist:
        # This is fine, create new
        pass

    election_list = Election.objects.order_by('-election_day_text')

    if measure_on_stage_found:
        template_values = {
            'messages_on_stage': messages_on_stage,
            'measure': measure_on_stage,
            'election_list': election_list,
            'google_civic_election_id': google_civic_election_id,
        }
    else:
        template_values = {
            'messages_on_stage': messages_on_stage,
        }
    return render(request, 'measure/measure_summary.html', template_values)
