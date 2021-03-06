# voter_guide/models.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.db import models
from django.db.models import Q
from election.models import ElectionManager, TIME_SPAN_LIST
from exception.models import handle_exception, handle_record_not_found_exception, \
    handle_record_found_more_than_one_exception
import operator
from organization.models import Organization, OrganizationManager
import wevote_functions.admin
from wevote_functions.functions import convert_to_int, convert_to_str, positive_value_exists
from wevote_settings.models import fetch_site_unique_id_prefix, fetch_next_we_vote_id_last_voter_guide_integer

logger = wevote_functions.admin.get_logger(__name__)

ORGANIZATION = 'O'
PUBLIC_FIGURE = 'P'
VOTER = 'V'
UNKNOWN_VOTER_GUIDE = 'U'
VOTER_GUIDE_TYPE_CHOICES = (
    (ORGANIZATION, 'Organization'),
    (PUBLIC_FIGURE, 'Public Figure or Politician'),
    (VOTER, 'Voter'),
)


class VoterGuideManager(models.Manager):
    """
    A class for working with the VoterGuide model
    """
    def update_or_create_organization_voter_guide_by_election_id(self, organization_we_vote_id,
                                                                 google_civic_election_id):
        """
        This creates voter_guides, and also refreshes voter guides with updated organization data
        """
        google_civic_election_id = convert_to_int(google_civic_election_id)
        voter_guide_owner_type = ORGANIZATION
        exception_multiple_object_returned = False
        organization = Organization()
        organization_found = False
        new_voter_guide_created = False
        if not google_civic_election_id or not organization_we_vote_id:
            status = 'ERROR_VARIABLES_MISSING_FOR_ORGANIZATION_VOTER_GUIDE'
            success = False
            new_voter_guide_created = False
        else:
            # Retrieve the organization object so we can bring over values
            # NOTE: If we don't have this organization in the local database, we won't create a voter guide
            organization_manager = OrganizationManager()
            results = organization_manager.retrieve_organization(0, organization_we_vote_id)
            if results['organization_found']:
                organization_found = True
                organization = results['organization']

            # Now update voter_guide
            try:
                if organization_found:
                    updated_values = {
                        # Values we search against below
                        'google_civic_election_id': google_civic_election_id,
                        'organization_we_vote_id':  organization_we_vote_id,
                        # The rest of the values
                        'voter_guide_owner_type':   voter_guide_owner_type,
                        'image_url':                organization.organization_photo_url(),
                        'twitter_handle':           organization.organization_twitter_handle,
                        'twitter_description':      organization.twitter_description,
                        'twitter_followers_count':  organization.twitter_followers_count,
                        'display_name':             organization.organization_name,
                    }
                    voter_guide_on_stage, new_voter_guide_created = VoterGuide.objects.update_or_create(
                        google_civic_election_id__exact=google_civic_election_id,
                        organization_we_vote_id__iexact=organization_we_vote_id,
                        defaults=updated_values)
                    success = True
                    if new_voter_guide_created:
                        status = 'VOTER_GUIDE_CREATED_FOR_ORGANIZATION'
                    else:
                        status = 'VOTER_GUIDE_UPDATED_FOR_ORGANIZATION'
                else:
                    success = False
                    status = 'VOTER_GUIDE_NOT_CREATED_BECAUSE_ORGANIZATION_NOT_FOUND_LOCALLY'
            except VoterGuide.MultipleObjectsReturned as e:
                handle_record_found_more_than_one_exception(e, logger=logger)
                success = False
                status = 'MULTIPLE_MATCHING_VOTER_GUIDES_FOUND_FOR_ORGANIZATION'
                exception_multiple_object_returned = True
                new_voter_guide_created = False

        results = {
            'success':                  success,
            'status':                   status,
            'MultipleObjectsReturned':  exception_multiple_object_returned,
            'voter_guide_saved':        success,
            'new_voter_guide_created':  new_voter_guide_created,
        }
        return results

    def update_or_create_organization_voter_guide_by_time_span(self, organization_we_vote_id, vote_smart_time_span):
        organization_found = False
        voter_guide_owner_type = ORGANIZATION
        exception_multiple_object_returned = False
        if not vote_smart_time_span or not organization_we_vote_id:
            status = 'ERROR_VARIABLES_MISSING_FOR_ORGANIZATION_VOTER_GUIDE_BY_TIME_SPAN'
            success = False
            new_voter_guide_created = False
        else:
            # Retrieve the organization object so we can bring over values
            organization_manager = OrganizationManager()
            results = organization_manager.retrieve_organization(0, organization_we_vote_id)
            if results['organization_found']:
                organization_found = True
                organization = results['organization']

            # Now update voter_guide
            try:
                if organization_found:
                    if organization.twitter_followers_count is None:
                        twitter_followers_count = 0
                    else:
                        twitter_followers_count = convert_to_int(organization.twitter_followers_count)
                    updated_values = {
                        # Values we search against below
                        'vote_smart_time_span':     vote_smart_time_span,
                        'organization_we_vote_id':  organization_we_vote_id,
                        # The rest of the values
                        'voter_guide_owner_type':   voter_guide_owner_type,
                        'twitter_handle':           organization.organization_twitter_handle,
                        'display_name':             organization.organization_name,
                        'image_url':                organization.organization_photo_url(),
                        'twitter_description':      organization.twitter_description,
                        'twitter_followers_count':  twitter_followers_count,
                    }
                    voter_guide_on_stage, new_voter_guide_created = VoterGuide.objects.update_or_create(
                        vote_smart_time_span__exact=vote_smart_time_span,
                        organization_we_vote_id__iexact=organization_we_vote_id,
                        defaults=updated_values)
                    success = True
                    if new_voter_guide_created:
                        status = 'VOTER_GUIDE_CREATED_FOR_ORGANIZATION_BY_TIME_SPAN'
                    else:
                        status = 'VOTER_GUIDE_UPDATED_FOR_ORGANIZATION_BY_TIME_SPAN'
                else:
                    success = False
                    status = 'VOTER_GUIDE_NOT_CREATED_BECAUSE_ORGANIZATION_NOT_FOUND_LOCALLY'
            except VoterGuide.MultipleObjectsReturned as e:
                handle_record_found_more_than_one_exception(e, logger=logger)
                success = False
                status = 'MULTIPLE_MATCHING_VOTER_GUIDES_FOUND_FOR_ORGANIZATION_BY_TIME_SPAN'
                exception_multiple_object_returned = True
                new_voter_guide_created = False

        results = {
            'success':                  success,
            'status':                   status,
            'MultipleObjectsReturned':  exception_multiple_object_returned,
            'voter_guide_saved':        success,
            'new_voter_guide_created':  new_voter_guide_created,
        }
        return results

    def update_or_create_public_figure_voter_guide(self, google_civic_election_id, public_figure_we_vote_id):
        new_voter_guide = VoterGuide()
        voter_guide_owner_type = new_voter_guide.PUBLIC_FIGURE
        exception_multiple_object_returned = False
        if not google_civic_election_id or not public_figure_we_vote_id:
            status = 'ERROR_VARIABLES_MISSING_FOR_PUBLIC_FIGURE_VOTER_GUIDE'
            new_voter_guide_created = False
            success = False
        else:
            try:
                updated_values = {
                    # Values we search against below
                    'google_civic_election_id': google_civic_election_id,
                    'voter_guide_owner_type': voter_guide_owner_type,
                    'public_figure_we_vote_id': public_figure_we_vote_id,
                    # The rest of the values
                }
                voter_guide_on_stage, new_voter_guide_created = VoterGuide.objects.update_or_create(
                    google_civic_election_id__exact=google_civic_election_id,
                    voter_guide_owner_type__iexact=voter_guide_owner_type,
                    public_figure_we_vote_id__iexact=public_figure_we_vote_id,
                    defaults=updated_values)
                success = True
                if new_voter_guide_created:
                    status = 'VOTER_GUIDE_CREATED_FOR_PUBLIC_FIGURE'
                else:
                    status = 'VOTER_GUIDE_UPDATED_FOR_PUBLIC_FIGURE'
            except VoterGuide.MultipleObjectsReturned as e:
                handle_record_found_more_than_one_exception(e, logger=logger)
                success = False
                status = 'MULTIPLE_MATCHING_VOTER_GUIDES_FOUND_FOR_PUBLIC_FIGURE'
                exception_multiple_object_returned = True
                new_voter_guide_created = False

        results = {
            'success':                  success,
            'status':                   status,
            'MultipleObjectsReturned':  exception_multiple_object_returned,
            'voter_guide_saved':        success,
            'new_voter_guide_created':  new_voter_guide_created,
        }
        return results

    def update_or_create_voter_voter_guide(self, google_civic_election_id, owner_voter_id):
        new_voter_guide = VoterGuide()
        voter_guide_owner_type = new_voter_guide.VOTER
        owner_voter_id = convert_to_int(owner_voter_id)
        exception_multiple_object_returned = False
        if not google_civic_election_id or not owner_voter_id:
            status = 'ERROR_VARIABLES_MISSING_FOR_VOTER_VOTER_GUIDE'
            new_voter_guide_created = False
            success = False
        else:
            try:
                updated_values = {
                    # Values we search against below
                    'google_civic_election_id': google_civic_election_id,
                    'voter_guide_owner_type': voter_guide_owner_type,
                    'owner_voter_id': owner_voter_id,
                    # The rest of the values
                }
                voter_guide_on_stage, new_voter_guide_created = VoterGuide.objects.update_or_create(
                    google_civic_election_id__exact=google_civic_election_id,
                    voter_guide_owner_type__iexact=voter_guide_owner_type,
                    owner_voter_id__exact=owner_voter_id,
                    defaults=updated_values)
                success = True
                if new_voter_guide_created:
                    status = 'VOTER_GUIDE_CREATED_FOR_VOTER'
                else:
                    status = 'VOTER_GUIDE_UPDATED_FOR_VOTER'
            except VoterGuide.MultipleObjectsReturned as e:
                handle_record_found_more_than_one_exception(e, logger=logger)
                success = False
                status = 'MULTIPLE_MATCHING_VOTER_GUIDES_FOUND_FOR_VOTER'
                exception_multiple_object_returned = True
                new_voter_guide_created = False

        results = {
            'success':                  success,
            'status':                   status,
            'MultipleObjectsReturned':  exception_multiple_object_returned,
            'voter_guide_saved':        success,
            'new_voter_guide_created':  new_voter_guide_created,
        }
        return results

    def voter_guide_exists(self, organization_we_vote_id, google_civic_election_id):
        voter_guide_found = False
        try:
            if positive_value_exists(organization_we_vote_id) and positive_value_exists(google_civic_election_id):
                voter_guide_on_stage = VoterGuide.objects.filter(google_civic_election_id=google_civic_election_id,
                                                                 organization_we_vote_id=organization_we_vote_id)
                voter_guide_found = True if voter_guide_on_stage.count() > 0 else False
        except VoterGuide.MultipleObjectsReturned as e:
            voter_guide_found = True
        except VoterGuide.DoesNotExist:
            voter_guide_found = False
        return voter_guide_found

    def retrieve_voter_guide(self, voter_guide_id=0, google_civic_election_id=0, vote_smart_time_span=None,
                             organization_we_vote_id=None, public_figure_we_vote_id=None, owner_we_vote_id=None):
        voter_guide_id = convert_to_int(voter_guide_id)
        google_civic_election_id = convert_to_int(google_civic_election_id)
        organization_we_vote_id = convert_to_str(organization_we_vote_id)
        public_figure_we_vote_id = convert_to_str(public_figure_we_vote_id)
        owner_we_vote_id = convert_to_str(owner_we_vote_id)

        error_result = False
        exception_does_not_exist = False
        exception_multiple_object_returned = False
        voter_guide_on_stage = VoterGuide()
        voter_guide_on_stage_id = 0
        status = "ERROR_ENTERING_RETRIEVE_VOTER_GUIDE"
        try:
            if positive_value_exists(voter_guide_id):
                status = "ERROR_RETRIEVING_VOTER_GUIDE_WITH_ID"  # Set this in case the get fails
                voter_guide_on_stage = VoterGuide.objects.get(id=voter_guide_id)
                voter_guide_on_stage_id = voter_guide_on_stage.id
                status = "VOTER_GUIDE_FOUND_WITH_ID"
            elif positive_value_exists(organization_we_vote_id) and positive_value_exists(google_civic_election_id):
                status = "ERROR_RETRIEVING_VOTER_GUIDE_WITH_ORGANIZATION_WE_VOTE_ID"  # Set this in case the get fails
                voter_guide_on_stage = VoterGuide.objects.get(google_civic_election_id=google_civic_election_id,
                                                              organization_we_vote_id=organization_we_vote_id)
                voter_guide_on_stage_id = voter_guide_on_stage.id
                status = "VOTER_GUIDE_FOUND_WITH_ORGANIZATION_WE_VOTE_ID"
            elif positive_value_exists(organization_we_vote_id) and positive_value_exists(vote_smart_time_span):
                status = "ERROR_RETRIEVING_VOTER_GUIDE_WITH_ORGANIZATION_WE_VOTE_ID_AND_TIME_SPAN"
                voter_guide_on_stage = VoterGuide.objects.get(vote_smart_time_span=vote_smart_time_span,
                                                              organization_we_vote_id=organization_we_vote_id)
                voter_guide_on_stage_id = voter_guide_on_stage.id
                status = "VOTER_GUIDE_FOUND_WITH_ORGANIZATION_WE_VOTE_ID_AND_TIME_SPAN"
            elif positive_value_exists(public_figure_we_vote_id) and positive_value_exists(google_civic_election_id):
                status = "ERROR_RETRIEVING_VOTER_GUIDE_WITH_PUBLIC_FIGURE_WE_VOTE_ID"  # Set this in case the get fails
                voter_guide_on_stage = VoterGuide.objects.get(google_civic_election_id=google_civic_election_id,
                                                              public_figure_we_vote_id=public_figure_we_vote_id)
                voter_guide_on_stage_id = voter_guide_on_stage.id
                status = "VOTER_GUIDE_FOUND_WITH_PUBLIC_FIGURE_WE_VOTE_ID"
            elif positive_value_exists(owner_we_vote_id) and positive_value_exists(google_civic_election_id):
                status = "ERROR_RETRIEVING_VOTER_GUIDE_WITH_VOTER_WE_VOTE_ID"  # Set this in case the get fails
                voter_guide_on_stage = VoterGuide.objects.get(google_civic_election_id=google_civic_election_id,
                                                              owner_we_vote_id=owner_we_vote_id)
                voter_guide_on_stage_id = voter_guide_on_stage.id
                status = "VOTER_GUIDE_FOUND_WITH_VOTER_WE_VOTE_ID"
            else:
                status = "Insufficient variables included to retrieve one voter guide."
        except VoterGuide.MultipleObjectsReturned as e:
            handle_record_found_more_than_one_exception(e, logger)
            error_result = True
            exception_multiple_object_returned = True
            status += ", ERROR_MORE_THAN_ONE_VOTER_GUIDE_FOUND"
        except VoterGuide.DoesNotExist:
            error_result = True
            exception_does_not_exist = True
            status += ", VOTER_GUIDE_NOT_FOUND"

        voter_guide_on_stage_found = True if voter_guide_on_stage_id > 0 else False
        results = {
            'success':                      True if voter_guide_on_stage_found else False,
            'status':                       status,
            'voter_guide_found':            voter_guide_on_stage_found,
            'voter_guide_id':               voter_guide_on_stage_id,
            'organization_we_vote_id':      voter_guide_on_stage.organization_we_vote_id,
            'public_figure_we_vote_id':     voter_guide_on_stage.public_figure_we_vote_id,
            'owner_we_vote_id':             voter_guide_on_stage.owner_we_vote_id,
            'voter_guide':                  voter_guide_on_stage,
            'error_result':                 error_result,
            'DoesNotExist':                 exception_does_not_exist,
            'MultipleObjectsReturned':      exception_multiple_object_returned,
        }
        return results

    def retrieve_most_recent_voter_guide_for_org(self, organization_we_vote_id):
        status = 'ENTERING_RETRIEVE_MOST_RECENT_VOTER_GUIDE_FOR_ORG'
        voter_guide_found = False
        voter_guide = VoterGuide()
        voter_guide_manager = VoterGuideManager()
        for time_span in TIME_SPAN_LIST:
            voter_guide_by_time_span_results = voter_guide_manager.retrieve_voter_guide(
                vote_smart_time_span=time_span,
                organization_we_vote_id=organization_we_vote_id)
            if voter_guide_by_time_span_results['voter_guide_found']:
                voter_guide_found = True
                voter_guide = voter_guide_by_time_span_results['voter_guide']
                status = 'MOST_RECENT_VOTER_GUIDE_FOUND_FOR_ORG_BY_TIME_SPAN'
                results = {
                    'success':              voter_guide_found,
                    'status':               status,
                    'voter_guide_found':    voter_guide_found,
                    'voter_guide':          voter_guide,
                }
                return results

        election_manager = ElectionManager()
        results = election_manager.retrieve_elections_by_date()
        if results['success']:
            election_list = results['election_list']
            for one_election in election_list:
                voter_guide_results = voter_guide_manager.retrieve_voter_guide(
                    google_civic_election_id=one_election.google_civic_election_id,
                    organization_we_vote_id=organization_we_vote_id)
                if voter_guide_results['voter_guide_found']:
                    voter_guide_found = True
                    voter_guide = voter_guide_results['voter_guide']
                    status = 'MOST_RECENT_VOTER_GUIDE_FOUND_FOR_ORG_BY_ELECTION_ID'
                    results = {
                        'success':              voter_guide_found,
                        'status':               status,
                        'voter_guide_found':    voter_guide_found,
                        'voter_guide':          voter_guide,
                    }
                    return results

        results = {
            'success':              False,
            'status':               status,
            'voter_guide_found':    voter_guide_found,
            'voter_guide':          voter_guide,
        }
        return results

    def update_voter_guide_social_media_statistics(self, organization):
        """
        Update voter_guide entry with details retrieved from Twitter, Facebook, or ???
        """
        success = False
        status = "ENTERING_UPDATE_VOTER_GUIDE_SOCIAL_MEDIA_STATISTICS"
        values_changed = False
        voter_guide = VoterGuide()

        if organization:
            if positive_value_exists(organization.twitter_followers_count):
                results = self.retrieve_most_recent_voter_guide_for_org(organization_we_vote_id=organization.we_vote_id)

                if results['voter_guide_found']:
                    voter_guide = results['voter_guide']
                    if positive_value_exists(voter_guide.id):
                        if voter_guide.twitter_followers_count != organization.twitter_followers_count:
                            voter_guide.twitter_followers_count = organization.twitter_followers_count
                            values_changed = True

            if positive_value_exists(values_changed):
                voter_guide.save()
                success = True
                status = "SAVED_ORG_TWITTER_DETAILS"
            else:
                success = True
                status = "NO_CHANGES_SAVED_TO_ORG_TWITTER_DETAILS"

        results = {
            'success':                  success,
            'status':                   status,
            'organization':             organization,
            'voter_guide':              voter_guide,
        }
        return results

    def delete_voter_guide(self, voter_guide_id):
        voter_guide_id = convert_to_int(voter_guide_id)
        voter_guide_deleted = False

        try:
            if voter_guide_id:
                results = self.retrieve_voter_guide(voter_guide_id)
                if results['voter_guide_found']:
                    voter_guide = results['voter_guide']
                    voter_guide_id = voter_guide.id
                    voter_guide.delete()
                    voter_guide_deleted = True
        except Exception as e:
            handle_exception(e, logger=logger)

        results = {
            'success':              voter_guide_deleted,
            'voter_guide_deleted': voter_guide_deleted,
            'voter_guide_id':      voter_guide_id,
        }
        return results

    def refresh_cached_voter_guide_info(self, voter_guide):
        """
        Make sure that the voter guide information has been updated with the latest information in the organization
        table. NOTE: Dale started building this routine, and then discovered
        that update_or_create_organization_voter_guide_by_election_id does this "refresh" function
        """
        voter_guide_change = False

        # Start with "speaker" information (Organization, Voter, or Public Figure)
        if positive_value_exists(voter_guide.organization_we_vote_id):
            if not positive_value_exists(voter_guide.display_name) \
                    or not positive_value_exists(voter_guide.image_url) \
                    or not positive_value_exists(voter_guide.twitter_handle) \
                    or not positive_value_exists(voter_guide.twitter_description):
                try:
                    # We need to look in the organization table for display_name & image_url
                    organization_manager = OrganizationManager()
                    organization_id = 0
                    results = organization_manager.retrieve_organization(organization_id,
                                                                         voter_guide.organization_we_vote_id)
                    if results['organization_found']:
                        organization = results['organization']
                        if not positive_value_exists(voter_guide.display_name):
                            # speaker_display_name is missing so look it up from source
                            voter_guide.display_name = organization.organization_name
                            voter_guide_change = True
                        if not positive_value_exists(voter_guide.image_url):
                            # image_url is missing so look it up from source
                            voter_guide.image_url = organization.organization_photo_url()
                            voter_guide_change = True
                        if not positive_value_exists(voter_guide.twitter_handle):
                            # twitter_url is missing so look it up from source
                            voter_guide.twitter_handle = organization.organization_twitter_handle
                            voter_guide_change = True
                        if not positive_value_exists(voter_guide.twitter_description):
                            # twitter_description is missing so look it up from source
                            voter_guide.twitter_description = organization.twitter_description
                            voter_guide_change = True
                except Exception as e:
                    pass
        elif positive_value_exists(voter_guide.voter_id):
            pass  # The following to be updated
            # if not positive_value_exists(voter_guide.speaker_display_name) or \
            #         not positive_value_exists(voter_guide.voter_we_vote_id) or \
            #         not positive_value_exists(voter_guide.speaker_image_url_https):
            #     try:
            #         # We need to look in the voter table for speaker_display_name
            #         voter_manager = VoterManager()
            #         results = voter_manager.retrieve_voter_by_id(voter_guide.voter_id)
            #         if results['voter_found']:
            #             voter = results['voter']
            #             if not positive_value_exists(voter_guide.speaker_display_name):
            #                 # speaker_display_name is missing so look it up from source
            #                 voter_guide.speaker_display_name = voter.get_full_name()
            #                 voter_guide_change = True
            #             if not positive_value_exists(voter_guide.voter_we_vote_id):
            #                 # speaker_we_vote_id is missing so look it up from source
            #                 voter_guide.voter_we_vote_id = voter.we_vote_id
            #                 voter_guide_change = True
            #             if not positive_value_exists(voter_guide.speaker_image_url_https):
            #                 # speaker_image_url_https is missing so look it up from source
            #                 voter_guide.speaker_image_url_https = voter.voter_photo_url()
            #                 voter_guide_change = True
            #     except Exception as e:
            #         pass

        elif positive_value_exists(voter_guide.public_figure_we_vote_id):
            pass

        if voter_guide_change:
            voter_guide.save()

        return voter_guide


class VoterGuide(models.Model):
    # We are relying on built-in Python id field

    # The we_vote_id identifier is unique across all We Vote sites, and allows us to share our voter_guide
    # info with other organizations running their own We Vote servers
    # It starts with "wv" then we add on a database specific identifier like "3v" (WeVoteSetting.site_unique_id_prefix)
    # then the string "vg" (for voter guide), and then a sequential integer like "123".
    # We generate this id on initial save keep the last value in WeVoteSetting.we_vote_id_last_voter_guide_integer
    we_vote_id = models.CharField(
        verbose_name="we vote permanent id", max_length=255, null=True, blank=True, unique=True)

    # NOTE: We are using we_vote_id's instead of internal ids
    # The unique id of the organization. May be null if voter_guide owned by a public figure or voter instead of org.
    organization_we_vote_id = models.CharField(
        verbose_name="organization we vote id", max_length=255, null=True, blank=True, unique=False)

    # The unique id of the public figure. May be null if voter_guide owned by org or voter instead of public figure.
    public_figure_we_vote_id = models.CharField(
        verbose_name="public figure we vote id", max_length=255, null=True, blank=True, unique=False)

    # The unique id of the public figure. May be null if voter_guide owned by org or public figure instead of voter.
    owner_we_vote_id = models.CharField(
        verbose_name="individual voter's we vote id", max_length=255, null=True, blank=True, unique=False)

    # The unique id of the voter that owns this guide. May be null if voter_guide owned by an org
    # or public figure instead of by a voter.
    # DEPRECATE THIS - 2015-11-11 We should use
    owner_voter_id = models.PositiveIntegerField(
        verbose_name="the unique voter id of the voter who this guide is about", default=0, null=True, blank=False)

    # The unique ID of this election. (Provided by Google Civic)
    google_civic_election_id = models.PositiveIntegerField(
        verbose_name="google civic election id", null=True)

    # Usually in one of these two formats 2015, 2014-2015
    vote_smart_time_span = models.CharField(
        verbose_name="the period in which the organization stated this position", max_length=255, null=True,
        blank=True, unique=False)

    # This might be the organization name, or the
    display_name = models.CharField(
        verbose_name="display title for this voter guide", max_length=255, null=True, blank=True, unique=False)

    image_url = models.URLField(verbose_name='image url of logo/photo associated with voter guide',
                                blank=True, null=True)

    voter_guide_owner_type = models.CharField(
        verbose_name="is owner org, public figure, or voter?", max_length=1, choices=VOTER_GUIDE_TYPE_CHOICES,
        default=ORGANIZATION)

    twitter_handle = models.CharField(verbose_name='twitter screen_name', max_length=255, null=True, unique=False)
    twitter_description = models.CharField(verbose_name="Text description of this organization from twitter.",
                                           max_length=255, null=True, blank=True)
    twitter_followers_count = models.IntegerField(verbose_name="number of twitter followers",
                                                  null=True, blank=True, default=0)

    # We usually cache the voter guide name, but in case we haven't, we force the lookup
    def voter_guide_display_name(self):
        if self.display_name:
            return self.display_name
        elif self.voter_guide_owner_type == ORGANIZATION:
            return self.retrieve_organization_display_name()
        return ''

    def retrieve_organization_display_name(self):
        organization_manager = OrganizationManager()
        organization_id = 0
        organization_we_vote_id = self.organization_we_vote_id
        results = organization_manager.retrieve_organization(organization_id, organization_we_vote_id)
        if results['organization_found']:
            organization = results['organization']
            organization_name = organization.organization_name
            return organization_name

    # We try to cache the image_url, but in case we haven't, we force the lookup
    def voter_guide_image_url(self):
        if self.image_url:
            return self.image_url
        elif self.voter_guide_owner_type == ORGANIZATION:
            organization_manager = OrganizationManager()
            organization_id = 0
            organization_we_vote_id = self.organization_we_vote_id
            results = organization_manager.retrieve_organization(organization_id, organization_we_vote_id)
            if results['organization_found']:
                organization = results['organization']
                organization_photo_url = organization.organization_photo_url()
                return organization_photo_url
        return ''

    # The date of the last change to this voter_guide
    last_updated = models.DateTimeField(verbose_name='date last changed', null=True, auto_now=True)  # TODO convert to date_last_changed

    # We want to map these here so they are available in the templates
    ORGANIZATION = ORGANIZATION
    PUBLIC_FIGURE = PUBLIC_FIGURE
    VOTER = VOTER
    UNKNOWN_VOTER_GUIDE = UNKNOWN_VOTER_GUIDE

    def __unicode__(self):
        return self.last_updated

    class Meta:
        ordering = ('last_updated',)

    objects = VoterGuideManager()

    def organization(self):
        try:
            organization = Organization.objects.get(we_vote_id=self.organization_we_vote_id)
        except Organization.MultipleObjectsReturned as e:
            handle_record_found_more_than_one_exception(e, logger=logger)
            logger.error("voter_guide.organization Found multiple")
            return
        except Organization.DoesNotExist:
            logger.error("voter_guide.organization did not find")
            return
        return organization

    # We override the save function so we can auto-generate we_vote_id
    def save(self, *args, **kwargs):
        # Even if this voter_guide came from another source we still need a unique we_vote_id
        if self.we_vote_id:
            self.we_vote_id = self.we_vote_id.strip().lower()
        if self.we_vote_id == "" or self.we_vote_id is None:  # If there isn't a value...
            # ...generate a new id
            site_unique_id_prefix = fetch_site_unique_id_prefix()
            next_local_integer = fetch_next_we_vote_id_last_voter_guide_integer()
            # "wv" = We Vote
            # site_unique_id_prefix = a generated (or assigned) unique id for one server running We Vote
            # "vg" = tells us this is a unique id for a voter guide
            # next_integer = a unique, sequential integer for this server - not necessarily tied to database id
            self.we_vote_id = "wv{site_unique_id_prefix}vg{next_integer}".format(
                site_unique_id_prefix=site_unique_id_prefix,
                next_integer=next_local_integer,
            )
            # TODO we need to deal with the situation where we_vote_id is NOT unique on save
        super(VoterGuide, self).save(*args, **kwargs)


# This is the class that we use to rapidly show lists of voter guides, regardless of whether they are from an
# organization, public figure, or voter
class VoterGuideListManager(models.Model):
    """
    A set of methods to retrieve a list of voter_guides
    """

    # NOTE: This is extremely simple way to retrieve voter guides, used by admin tools. Being replaced by:
    #  retrieve_voter_guides_by_ballot_item(ballot_item_we_vote_id) AND
    #  retrieve_voter_guides_by_election(google_civic_election_id)
    def retrieve_voter_guides_for_election(self, google_civic_election_id):
        voter_guide_list = []
        voter_guide_list_found = False

        try:
            # voter_guide_queryset = VoterGuide.objects.order_by('-twitter_followers_count')
            voter_guide_queryset = VoterGuide.objects.order_by('display_name')
            voter_guide_list = voter_guide_queryset.filter(
                google_civic_election_id=google_civic_election_id)

            if len(voter_guide_list):
                voter_guide_list_found = True
                status = 'VOTER_GUIDE_FOUND'
            else:
                status = 'NO_VOTER_GUIDES_FOUND'
            success = True
        except Exception as e:
            handle_record_not_found_exception(e, logger=logger)
            status = 'voterGuidesToFollowRetrieve: Unable to retrieve voter guides from db. ' \
                     '{error} [type: {error_type}]'.format(error=e, error_type=type(e))
            success = False

        results = {
            'success':                      success,
            'status':                       status,
            'voter_guide_list_found':       voter_guide_list_found,
            'voter_guide_list':             voter_guide_list,
        }
        return results

    def retrieve_voter_guides_by_organization_list(self, organization_we_vote_ids_followed_by_voter):
        voter_guide_list = []
        voter_guide_list_found = False

        if not type(organization_we_vote_ids_followed_by_voter) is list:
            status = 'NO_VOTER_GUIDES_FOUND_MISSING_ORGANIZATION_LIST'
            success = False
            results = {
                'success':                      success,
                'status':                       status,
                'voter_guide_list_found':       voter_guide_list_found,
                'voter_guide_list':             voter_guide_list,
            }
            return results

        if not len(organization_we_vote_ids_followed_by_voter):
            status = 'NO_VOTER_GUIDES_FOUND_NO_ORGANIZATIONS_IN_LIST'
            success = False
            results = {
                'success':                      success,
                'status':                       status,
                'voter_guide_list_found':       voter_guide_list_found,
                'voter_guide_list':             voter_guide_list,
            }
            return results

        try:
            voter_guide_queryset = VoterGuide.objects.all()
            voter_guide_queryset = voter_guide_queryset.filter(
                organization_we_vote_id__in=organization_we_vote_ids_followed_by_voter)
            voter_guide_queryset = voter_guide_queryset.order_by('-twitter_followers_count')
            voter_guide_list = voter_guide_queryset

            if len(voter_guide_list):
                voter_guide_list_found = True
                status = 'VOTER_GUIDES_FOUND_BY_ORGANIZATION_LIST'
            else:
                status = 'NO_VOTER_GUIDES_FOUND_BY_ORGANIZATION_LIST'
            success = True
        except Exception as e:
            handle_record_not_found_exception(e, logger=logger)
            status = 'voterGuidesToFollowRetrieve: Unable to retrieve voter guides from db. ' \
                     '{error} [type: {error_type}]'.format(error=e.message, error_type=type(e))
            success = False

        # If we have multiple voter guides for one org, we only want to show the most recent
        if voter_guide_list_found:
            voter_guide_list_filtered = self.remove_older_voter_guides_for_each_org(voter_guide_list)
        else:
            voter_guide_list_filtered = []

        results = {
            'success':                      success,
            'status':                       status,
            'voter_guide_list_found':       voter_guide_list_found,
            'voter_guide_list':             voter_guide_list_filtered,
        }
        return results

    def retrieve_voter_guides_to_follow_by_election(self, google_civic_election_id, organization_we_vote_id_list,
                                                    search_string,
                                                    maximum_number_to_retrieve=0, sort_by='', sort_order=''):
        voter_guide_list = []
        voter_guide_list_found = False
        if not positive_value_exists(maximum_number_to_retrieve):
            maximum_number_to_retrieve = 30

        try:
            voter_guide_queryset = VoterGuide.objects.all()
            if search_string:
                voter_guide_queryset = voter_guide_queryset.filter(Q(display_name__icontains=search_string) |
                                                                   Q(twitter_handle__icontains=search_string))

            voter_guide_queryset = voter_guide_queryset.filter(
                Q(google_civic_election_id=google_civic_election_id) &
                Q(organization_we_vote_id__in=organization_we_vote_id_list)
            )

            if sort_order == 'desc':
                voter_guide_queryset = voter_guide_queryset.order_by('-' + sort_by)[:maximum_number_to_retrieve]
            else:
                voter_guide_queryset = voter_guide_queryset.order_by(sort_by)[:maximum_number_to_retrieve]

            voter_guide_list = voter_guide_queryset

            if len(voter_guide_list):
                voter_guide_list_found = True
                status = 'VOTER_GUIDE_FOUND'
            else:
                status = 'NO_VOTER_GUIDES_FOUND'
            success = True
        except Exception as e:
            handle_record_not_found_exception(e, logger=logger)
            status = 'voterGuidesToFollowRetrieve: Unable to retrieve voter guides from db. ' \
                     '{error} [type: {error_type}]'.format(error=e, error_type=type(e))
            success = False

        results = {
            'success':                      success,
            'status':                       status,
            'voter_guide_list_found':       voter_guide_list_found,
            'voter_guide_list':             voter_guide_list,
        }
        return results

    def retrieve_voter_guides_to_follow_by_time_span(self, orgs_we_need_found_by_position_and_time_span_list_of_dicts,
                                                     search_string,
                                                     maximum_number_to_retrieve=0, sort_by='', sort_order=''):
        """
        Get the voter guides for orgs that we found by looking at the positions for an org found based on time span
        """
        voter_guide_list = []
        voter_guide_list_found = False
        if not positive_value_exists(maximum_number_to_retrieve):
            maximum_number_to_retrieve = 30

        if not len(orgs_we_need_found_by_position_and_time_span_list_of_dicts):
            status = "NO_VOTER_GUIDES_FOUND_BY_TIME_SPAN"
            results = {
                'success': True,
                'status': status,
                'voter_guide_list_found': voter_guide_list_found,
                'voter_guide_list': voter_guide_list,
            }
            return results

        try:
            voter_guide_queryset = VoterGuide.objects.all()

            # Retrieve all pairs that match vote_smart_time_span / organization_we_vote_id
            filter_list = Q()
            for item in orgs_we_need_found_by_position_and_time_span_list_of_dicts:
                filter_list |= Q(vote_smart_time_span=item['vote_smart_time_span'],
                                 organization_we_vote_id=item['organization_we_vote_id'])
            voter_guide_queryset = voter_guide_queryset.filter(filter_list)

            if search_string:
                voter_guide_queryset = voter_guide_queryset.filter(Q(display_name__icontains=search_string) |
                                                                   Q(twitter_handle__icontains=search_string))

            if sort_order == 'desc':
                voter_guide_queryset = voter_guide_queryset.order_by('-' + sort_by)[:maximum_number_to_retrieve]
            else:
                voter_guide_queryset = voter_guide_queryset.order_by(sort_by)[:maximum_number_to_retrieve]

            voter_guide_list = voter_guide_queryset
            if len(voter_guide_list):
                voter_guide_list_found = True
                status = 'VOTER_GUIDE_FOUND'
            else:
                status = 'NO_VOTER_GUIDES_FOUND'
            success = True
        except Exception as e:
            handle_record_not_found_exception(e, logger=logger)
            status = 'voterGuidesToFollowRetrieve: Unable to retrieve voter guides from db. ' \
                     '{error} [type: {error_type}]'.format(error=e, error_type=type(e))
            success = False

        results = {
            'success':                      success,
            'status':                       status,
            'voter_guide_list_found':       voter_guide_list_found,
            'voter_guide_list':             voter_guide_list,
        }
        return results

    def retrieve_voter_guides_to_follow_generic(self, organization_we_vote_ids_followed_or_ignored_by_voter,
                                                search_string,
                                                maximum_number_to_retrieve=0, sort_by='', sort_order=''):
        """
        Get the voter guides for orgs that we found by looking at the positions for an org found based on time span
        """
        voter_guide_list = []
        voter_guide_list_found = False
        if not positive_value_exists(maximum_number_to_retrieve):
            maximum_number_to_retrieve = 30

        try:
            voter_guide_queryset = VoterGuide.objects.all()

            if len(organization_we_vote_ids_followed_or_ignored_by_voter):
                voter_guide_queryset = voter_guide_queryset.exclude(
                    organization_we_vote_id__in=organization_we_vote_ids_followed_or_ignored_by_voter)

            if search_string:
                voter_guide_queryset = voter_guide_queryset.filter(Q(display_name__icontains=search_string) |
                                                                   Q(twitter_handle__icontains=search_string))

            if sort_order == 'desc':
                voter_guide_queryset = voter_guide_queryset.order_by('-' + sort_by)[:maximum_number_to_retrieve]
            else:
                voter_guide_queryset = voter_guide_queryset.order_by(sort_by)[:maximum_number_to_retrieve]

            voter_guide_list = voter_guide_queryset
            if len(voter_guide_list):
                voter_guide_list_found = True
                status = 'VOTER_GUIDE_FOUND_GENERIC_VOTER_GUIDES_TO_FOLLOW'
            else:
                status = 'NO_VOTER_GUIDES_FOUND_GENERIC_VOTER_GUIDES_TO_FOLLOW'
            success = True
        except Exception as e:
            handle_record_not_found_exception(e, logger=logger)
            status = 'voterGuidesToFollowRetrieve: Unable to retrieve voter guides from db. ' \
                     '{error} [type: {error_type}]'.format(error=e, error_type=type(e))
            success = False

        # If we have multiple voter guides for one org, we only want to show the most recent
        if voter_guide_list_found:
            voter_guide_list_filtered = self.remove_older_voter_guides_for_each_org(voter_guide_list)
        else:
            voter_guide_list_filtered = []

        results = {
            'success':                      success,
            'status':                       status,
            'voter_guide_list_found':       voter_guide_list_found,
            'voter_guide_list':             voter_guide_list_filtered,
        }
        return results

    def remove_older_voter_guides_for_each_org(self, voter_guide_list):
        # If we have multiple voter guides for one org, we only want to show the most recent
        organization_already_reviewed = []
        organization_with_multiple_voter_guides = []
        newest_voter_guide_for_org = {}  # Figure out the newest voter guide per org that we should show
        for one_voter_guide in voter_guide_list:
            if one_voter_guide.organization_we_vote_id:
                if one_voter_guide.organization_we_vote_id not in organization_already_reviewed:
                    organization_already_reviewed.append(one_voter_guide.organization_we_vote_id)
                # Are we dealing with a time span (instead of google_civic_election_id)?
                if positive_value_exists(one_voter_guide.vote_smart_time_span):
                    # Take the first four digits of one_voter_guide.vote_smart_time_span
                    first_four_digits = convert_to_int(one_voter_guide.vote_smart_time_span[:4])
                    # And figure out the newest voter guide for each org
                    if one_voter_guide.organization_we_vote_id in newest_voter_guide_for_org:
                        # If we are here, it means we have seen this organization once already
                        if one_voter_guide.organization_we_vote_id not in organization_with_multiple_voter_guides:
                            organization_with_multiple_voter_guides.append(one_voter_guide.organization_we_vote_id)
                        # If this voter guide is newer than the one already looked at, update newest_voter_guide_for_org
                        if first_four_digits > newest_voter_guide_for_org[one_voter_guide.organization_we_vote_id]:
                            newest_voter_guide_for_org[one_voter_guide.organization_we_vote_id] = first_four_digits
                    else:
                        newest_voter_guide_for_org[one_voter_guide.organization_we_vote_id] = first_four_digits

        voter_guide_list_filtered = []
        for one_voter_guide in voter_guide_list:
            if one_voter_guide.organization_we_vote_id in organization_with_multiple_voter_guides:
                if positive_value_exists(one_voter_guide.vote_smart_time_span):
                    first_four_digits = convert_to_int(one_voter_guide.vote_smart_time_span[:4])
                    if newest_voter_guide_for_org[one_voter_guide.organization_we_vote_id] == first_four_digits:
                        # If this voter guide is the newest from among the org's voter guides, include in results
                        voter_guide_list_filtered.append(one_voter_guide)
            else:
                voter_guide_list_filtered.append(one_voter_guide)

        return voter_guide_list_filtered

    def retrieve_all_voter_guides(self, order_by=''):
        voter_guide_list = []
        voter_guide_list_found = False
        try:
            voter_guide_queryset = VoterGuide.objects.all()
            if order_by == 'google_civic_election_id':
                voter_guide_queryset = voter_guide_queryset.order_by(
                    '-vote_smart_time_span', '-google_civic_election_id')
            else:
                voter_guide_queryset = voter_guide_queryset.order_by('-twitter_followers_count')
            voter_guide_list = voter_guide_queryset

            if len(voter_guide_list):
                voter_guide_list_found = True
                status = 'VOTER_GUIDE_FOUND'
            else:
                status = 'NO_VOTER_GUIDES_FOUND'
            success = True
        except Exception as e:
            handle_record_not_found_exception(e, logger=logger)
            status = 'voterGuidesToFollowRetrieve: Unable to retrieve voter guides from db. ' \
                     '{error} [type: {error_type}]'.format(error=e, error_type=type(e))
            success = False

        results = {
            'success':                      success,
            'status':                       status,
            'voter_guide_list_found':       voter_guide_list_found,
            'voter_guide_list':             voter_guide_list,
        }
        return results

    def reorder_voter_guide_list(self, voter_guide_list, field_to_order_by, asc_or_desc='desc'):
        def get_key_to_sort_by():
            if field_to_order_by == 'twitter_followers_count':
                return 'twitter_followers_count'
            else:
                return 'twitter_followers_count'

        if not len(voter_guide_list):
            return []

        # If we set this to 'desc', then Reverse the sort below. Otherwise sort 'asc' (ascending)
        is_desc = True if asc_or_desc == 'desc' else False

        voter_guide_list_sorted = sorted(voter_guide_list, key=operator.attrgetter(get_key_to_sort_by()),
                                         reverse=is_desc)

        return voter_guide_list_sorted

    def retrieve_possible_duplicate_voter_guides(self, google_civic_election_id, vote_smart_time_span,
                                                 organization_we_vote_id, public_figure_we_vote_id,
                                                 twitter_handle,
                                                 we_vote_id_from_master=''):
        voter_guide_list_objects = []
        filters = []
        voter_guide_list_found = False

        try:
            voter_guide_queryset = VoterGuide.objects.all()
            if positive_value_exists(google_civic_election_id):
                voter_guide_queryset = voter_guide_queryset.filter(google_civic_election_id=google_civic_election_id)
            elif positive_value_exists(vote_smart_time_span):
                voter_guide_queryset = voter_guide_queryset.filter(vote_smart_time_span__iexact=vote_smart_time_span)

            # Ignore entries with we_vote_id coming in from master server
            if positive_value_exists(we_vote_id_from_master):
                voter_guide_queryset = voter_guide_queryset.filter(~Q(we_vote_id__iexact=we_vote_id_from_master))

            # We want to find candidates with *any* of these values
            if positive_value_exists(organization_we_vote_id):
                new_filter = Q(organization_we_vote_id__iexact=organization_we_vote_id)
                filters.append(new_filter)

            if positive_value_exists(public_figure_we_vote_id):
                new_filter = Q(public_figure_we_vote_id__iexact=public_figure_we_vote_id)
                filters.append(new_filter)

            if positive_value_exists(twitter_handle):
                new_filter = Q(twitter_handle__iexact=twitter_handle)
                filters.append(new_filter)

            # Add the first query
            if len(filters):
                final_filters = filters.pop()

                # ...and "OR" the remaining items in the list
                for item in filters:
                    final_filters |= item

                voter_guide_queryset = voter_guide_queryset.filter(final_filters)

            voter_guide_list_objects = voter_guide_queryset

            if len(voter_guide_list_objects):
                voter_guide_list_found = True
                status = 'DUPLICATE_VOTER_GUIDES_RETRIEVED'
                success = True
            else:
                status = 'NO_DUPLICATE_VOTER_GUIDES_RETRIEVED'
                success = True
        except VoterGuide.DoesNotExist:
            # No candidates found. Not a problem.
            status = 'NO_DUPLICATE_VOTER_GUIDES_FOUND_DoesNotExist'
            voter_guide_list_objects = []
            success = True
        except Exception as e:
            handle_exception(e, logger=logger)
            status = 'FAILED retrieve_possible_duplicate_voter_guides ' \
                     '{error} [type: {error_type}]'.format(error=e, error_type=type(e))
            success = False

        results = {
            'success':                  success,
            'status':                   status,
            'google_civic_election_id': google_civic_election_id,
            'voter_guide_list_found':   voter_guide_list_found,
            'voter_guide_list':         voter_guide_list_objects,
        }
        return results


class VoterGuidePossibilityManager(models.Manager):
    """
    A class for working with the VoterGuidePossibility model
    """
    def update_or_create_voter_guide_possibility(self, voter_guide_possibility_url, google_civic_election_id=0):
        google_civic_election_id = convert_to_int(google_civic_election_id)
        # TODO Implement the following to have a chance of normalizing URL's pasted in by volunteers
        #   http://nullege.com/codes/search/scrapy.utils.url.canonicalize_url
        # voter_guide_possibility_url =
        exception_multiple_object_returned = False
        if voter_guide_possibility_url and google_civic_election_id:
            try:
                updated_values = {
                    # Values we search against below
                    'google_civic_election_id': google_civic_election_id,
                    'voter_guide_possibility_url': voter_guide_possibility_url,
                    # The rest of the values
                }
                voter_guide_possibility_on_stage, new_voter_guide_possibility_created = \
                    VoterGuidePossibility.objects.update_or_create(
                        google_civic_election_id__exact=google_civic_election_id,
                        voter_guide_possibility_url__iexact=voter_guide_possibility_url,
                        defaults=updated_values)
                success = True
                if new_voter_guide_possibility_created:
                    status = 'VOTER_GUIDE_POSSIBILITY_CREATED_WITH_ELECTION'
                else:
                    status = 'VOTER_GUIDE_POSSIBILITY_UPDATED_WITH_ELECTION'
            except VoterGuidePossibility.MultipleObjectsReturned as e:
                handle_record_found_more_than_one_exception(e, logger=logger)
                success = False
                status = 'MULTIPLE_MATCHING_VOTER_GUIDE_POSSIBILITIES_FOUND_BY_URL_AND_ELECTION'
                exception_multiple_object_returned = True
                new_voter_guide_possibility_created = False
        elif voter_guide_possibility_url:  # No google_civic_election_id provided
            try:
                updated_values = {
                    # Values we search against below
                    'voter_guide_possibility_url': voter_guide_possibility_url,
                    # The rest of the values
                }
                voter_guide_possibility_on_stage, new_voter_guide_possibility_created = \
                    VoterGuidePossibility.objects.update_or_create(
                        voter_guide_possibility_url__exact=voter_guide_possibility_url,
                        defaults=updated_values)
                success = True
                if new_voter_guide_possibility_created:
                    status = 'VOTER_GUIDE_POSSIBILITY_CREATED_WITHOUT_ELECTION'
                else:
                    status = 'VOTER_GUIDE_POSSIBILITY_UPDATED_WITHOUT_ELECTION'
            except VoterGuidePossibility.MultipleObjectsReturned as e:
                handle_record_found_more_than_one_exception(e, logger=logger)
                success = False
                status = 'MULTIPLE_MATCHING_VOTER_GUIDE_POSSIBILITIES_FOUND_BY_URL'
                exception_multiple_object_returned = True
                new_voter_guide_possibility_created = False
        else:
            status = 'ERROR_VARIABLES_MISSING_FOR_VOTER_GUIDE_POSSIBILITY'
            success = False
            new_voter_guide_possibility_created = False

        results = {
            'success':                              success,
            'status':                               status,
            'MultipleObjectsReturned':              exception_multiple_object_returned,
            'voter_guide_possibility_saved':        success,
            'new_voter_guide_possibility_created':  new_voter_guide_possibility_created,
        }
        return results

    def retrieve_voter_guide_possibility_from_url(self, voter_guide_possibility_url):
        voter_guide_possibility_id = 0
        google_civic_election_id = 0
        return self.retrieve_voter_guide_possibility(voter_guide_possibility_id, google_civic_election_id,
                                                     voter_guide_possibility_url)

    def retrieve_voter_guide_possibility(self, voter_guide_possibility_id=0, google_civic_election_id=0,
                                         voter_guide_possibility_url='',
                                         organization_we_vote_id=None,
                                         public_figure_we_vote_id=None,
                                         owner_we_vote_id=None):
        voter_guide_possibility_id = convert_to_int(voter_guide_possibility_id)
        google_civic_election_id = convert_to_int(google_civic_election_id)
        organization_we_vote_id = convert_to_str(organization_we_vote_id)
        public_figure_we_vote_id = convert_to_str(public_figure_we_vote_id)
        owner_we_vote_id = convert_to_str(owner_we_vote_id)

        error_result = False
        exception_does_not_exist = False
        exception_multiple_object_returned = False
        voter_guide_possibility_on_stage = VoterGuidePossibility()
        voter_guide_possibility_on_stage_id = 0
        try:
            if positive_value_exists(voter_guide_possibility_id):
                status = "ERROR_RETRIEVING_VOTER_GUIDE_POSSIBILITY_WITH_ID"  # Set this in case the get fails
                voter_guide_possibility_on_stage = VoterGuidePossibility.objects.get(id=voter_guide_possibility_id)
                voter_guide_possibility_on_stage_id = voter_guide_possibility_on_stage.id
                status = "VOTER_GUIDE_POSSIBILITY_FOUND_WITH_ID"
                success = True
            elif positive_value_exists(voter_guide_possibility_url):
                status = "ERROR_RETRIEVING_VOTER_GUIDE_POSSIBILITY_WITH_URL"  # Set this in case the get fails
                voter_guide_possibility_on_stage = VoterGuidePossibility.objects.get(
                    voter_guide_possibility_url=voter_guide_possibility_url)
                voter_guide_possibility_on_stage_id = voter_guide_possibility_on_stage.id
                status = "VOTER_GUIDE_POSSIBILITY_FOUND_WITH_URL"
                success = True
            elif positive_value_exists(organization_we_vote_id) and positive_value_exists(google_civic_election_id):
                # Set this status in case the 'get' fails
                status = "ERROR_RETRIEVING_VOTER_GUIDE_POSSIBILITY_WITH_ORGANIZATION_WE_VOTE_ID"
                voter_guide_possibility_on_stage = VoterGuidePossibility.objects.get(
                    google_civic_election_id=google_civic_election_id,
                    organization_we_vote_id=organization_we_vote_id)
                voter_guide_possibility_on_stage_id = voter_guide_possibility_on_stage.id
                status = "VOTER_GUIDE_POSSIBILITY_FOUND_WITH_ORGANIZATION_WE_VOTE_ID"
                success = True
            elif positive_value_exists(public_figure_we_vote_id) and positive_value_exists(google_civic_election_id):
                # Set this status in case the 'get' fails
                status = "ERROR_RETRIEVING_VOTER_GUIDE_POSSIBILITY_WITH_PUBLIC_FIGURE_WE_VOTE_ID"
                voter_guide_possibility_on_stage = VoterGuidePossibility.objects.get(
                    google_civic_election_id=google_civic_election_id,
                    public_figure_we_vote_id=public_figure_we_vote_id)
                voter_guide_possibility_on_stage_id = voter_guide_possibility_on_stage.id
                status = "VOTER_GUIDE_POSSIBILITY_FOUND_WITH_PUBLIC_FIGURE_WE_VOTE_ID"
                success = True
            elif positive_value_exists(owner_we_vote_id) and positive_value_exists(google_civic_election_id):
                # Set this status in case the 'get' fails
                status = "ERROR_RETRIEVING_VOTER_GUIDE_POSSIBILITY_WITH_VOTER_WE_VOTE_ID"
                voter_guide_possibility_on_stage = VoterGuidePossibility.objects.get(
                    google_civic_election_id=google_civic_election_id,
                    owner_we_vote_id=owner_we_vote_id)
                voter_guide_possibility_on_stage_id = voter_guide_possibility_on_stage.id
                status = "VOTER_GUIDE_POSSIBILITY_FOUND_WITH_VOTER_WE_VOTE_ID"
                success = True
            else:
                status = "VOTER_GUIDE_POSSIBILITY_NOT_FOUND_INSUFFICIENT_VARIABLES"
                success = False
        except VoterGuidePossibility.MultipleObjectsReturned as e:
            handle_record_found_more_than_one_exception(e, logger)
            error_result = True
            exception_multiple_object_returned = True
            status += ", ERROR_MORE_THAN_ONE_VOTER_GUIDE_POSSIBILITY_FOUND"
            success = False
        except VoterGuidePossibility.DoesNotExist:
            error_result = True
            exception_does_not_exist = True
            status = "VOTER_GUIDE_POSSIBILITY_NOT_FOUND"
            success = True

        voter_guide_possibility_on_stage_found = True if voter_guide_possibility_on_stage_id > 0 else False
        results = {
            'success':                          success,
            'status':                           status,
            'voter_guide_possibility_found':    voter_guide_possibility_on_stage_found,
            'voter_guide_possibility_id':       voter_guide_possibility_on_stage_id,
            'voter_guide_possibility_url':      voter_guide_possibility_on_stage.voter_guide_possibility_url,
            'organization_we_vote_id':          voter_guide_possibility_on_stage.organization_we_vote_id,
            'public_figure_we_vote_id':         voter_guide_possibility_on_stage.public_figure_we_vote_id,
            'owner_we_vote_id':                 voter_guide_possibility_on_stage.owner_we_vote_id,
            'voter_guide':                      voter_guide_possibility_on_stage,
            'error_result':                     error_result,
            'DoesNotExist':                     exception_does_not_exist,
            'MultipleObjectsReturned':          exception_multiple_object_returned,
        }
        return results

    def delete_voter_guide_possibility(self, voter_guide_possibility_id):
        voter_guide_possibility_id = convert_to_int(voter_guide_possibility_id)
        voter_guide_deleted = False

        try:
            if voter_guide_possibility_id:
                results = self.retrieve_voter_guide_possibility(voter_guide_possibility_id)
                if results['voter_guide_found']:
                    voter_guide = results['voter_guide']
                    voter_guide_possibility_id = voter_guide.id
                    voter_guide.delete()
                    voter_guide_deleted = True
        except Exception as e:
            handle_exception(e, logger=logger)

        results = {
            'success':              voter_guide_deleted,
            'voter_guide_deleted': voter_guide_deleted,
            'voter_guide_possibility_id':      voter_guide_possibility_id,
        }
        return results


class VoterGuidePossibility(models.Model):
    """
    We ask volunteers to enter a list of urls that might have voter guides. This table stores the URLs and partial
    information, prior to a full-fledged voter guide being saved in the VoterGuide table.
    """
    # We are relying on built-in Python id field

    # Where a volunteer thinks there is a voter guide
    voter_guide_possibility_url = models.URLField(verbose_name='url of possible voter guide', blank=True, null=True)

    # The unique id of the organization, if/when we know it
    organization_we_vote_id = models.CharField(
        verbose_name="organization we vote id", max_length=255, null=True, blank=True, unique=False)

    # The unique id of the public figure, if/when we know it
    public_figure_we_vote_id = models.CharField(
        verbose_name="public figure we vote id", max_length=255, null=True, blank=True, unique=False)

    # The unique id of the public figure, if/when we know it
    owner_we_vote_id = models.CharField(
        verbose_name="individual voter's we vote id", max_length=255, null=True, blank=True, unique=False)

    # The unique ID of this election. (Provided by Google Civic)
    google_civic_election_id = models.PositiveIntegerField(verbose_name="google civic election id", null=True)

    voter_guide_owner_type = models.CharField(
        verbose_name="is owner org, public figure, or voter?", max_length=1, choices=VOTER_GUIDE_TYPE_CHOICES,
        default=ORGANIZATION)

    # The date of the last change to this voter_guide_possibility
    last_updated = models.DateTimeField(verbose_name='date last changed', null=True, auto_now=True)  # TODO Convert to date_last_changed

    def __unicode__(self):
        return self.last_updated

    class Meta:
        ordering = ('last_updated',)

    objects = VoterGuideManager()

    def organization(self):
        try:
            organization = Organization.objects.get(we_vote_id=self.organization_we_vote_id)
        except Organization.MultipleObjectsReturned as e:
            handle_record_found_more_than_one_exception(e, logger=logger)
            logger.error("voter_guide.organization Found multiple")
            return
        except Organization.DoesNotExist:
            logger.error("voter_guide.organization did not find")
            return
        return organization
