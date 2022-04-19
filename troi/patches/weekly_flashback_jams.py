from collections import defaultdict
import random

import click

from troi import Element, Recording, Playlist, PipelineError
import troi.listenbrainz.recs
import troi.playlist
import troi.filters
import troi.sorts
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.mbid_mapping


@click.group()
def cli():
    pass

class DecadePlaylistSplitterElement(Element):
    '''
        Take a list of recordings that have their year attribute filled out
        and output N playlists broken down by decade of the Recordings. Recordings
        with no year set will be ignored and playlists will only be generated
        for decades that have at least minimum_count recordings.
    '''

    def __init__(self, minimum_count=20):
        Element.__init__(self)
        self.minimum_count = minimum_count

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):
        """
            Sort the recordings into decades and return playlists for decades that have the minimum number of tracks.
        """
        recordings = inputs[0]
        if not recordings or len(recordings) == 0:
            return inputs[0]

        decades = defaultdict(list)
        for r in recordings:
            if not r.year:
                continue

            decade = (r.year // 10) * 10
            decades[decade].append(r)

        playlists = []
        for decade in decades:
            if len(decades[decade]) < self.minimum_count:
                continue

            random.shuffle(decades[decade])
            playlists.append(Playlist("%ss flashback jams" % str(decade), filename="%ss_flashback_jams.jspf" % str(decade),
                             recordings=decades[decade]))

        return playlists


class WeeklyFlashbackJams(troi.patch.Patch):
    """
        See below for description
    """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('type')
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        Generate weekly flashback playlists from the ListenBrainz recommended recordings.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        TYPE: is The type of daily jam. Must be 'top' or 'similar'.
        TOKEN: is the user token from the LB user into whose account you wish to post this playlist
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "user_name", "desc": "ListenBrainz user name", "optional": False },
                { "type": str, "name": "type", "desc": "The type of daily jam. Must be 'top' or 'similar'.", "optional": False }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "weekly-flashback-jams"

    @staticmethod
    def description():
        return "Generate weekly flashback playlists from the ListenBrainz recommended recordings."

    def create(self, inputs, patch_args):
        user_name = inputs['user_name']
        type = inputs['type']

        if type not in ("top", "similar"):
            raise PipelineError("type must be either 'top' or 'similar'")

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                          artist_type=type,
                                                                          count=-1)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement(skip_not_found=True)
        r_lookup.set_sources(recs)

        y_lookup = troi.musicbrainz.mbid_mapping.MBIDMappingLookupElement()
        y_lookup.set_sources(r_lookup)

        # Filter out tracks that do not fit into the given year range
        year_sort = troi.sorts.YearSortElement()
        year_sort.set_sources(y_lookup)

        decade_splitter = DecadePlaylistSplitterElement()
        decade_splitter.set_sources(year_sort)

        shaper = troi.playlist.PlaylistRedundancyReducerElement(max_artist_occurrence=3)
        shaper.set_sources(decade_splitter)

        shuffle = troi.playlist.PlaylistShuffleElement()
        shuffle.set_sources(shaper)

        return shuffle
