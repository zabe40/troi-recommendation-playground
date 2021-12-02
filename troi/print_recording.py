from troi import Recording, Playlist, PipelineError

class PrintRecordingList():
    """
        Print a list of recordings in a sane matter intended to fit on a reasonably sized screen.
        It prints recording name and artist name always, and year, bpm, listen_count or moods
        if they are found in the first recording.
    """

    def __init__(self):
        super().__init__()
        self.print_year = None
        self.print_bpm = None
        self.print_list_count = None
        self.print_moods = None
        self.print_genre = None

    def _examine_recording_for_headers(self, recording):
        # Look at the first item and decide which columns to show
        if recording.year is not None:
            self.print_year = True
        else:
            self.print_year = False

        if "listen_count" in recording.listenbrainz:
            self.print_listen_count = True
        else:
            self.print_listen_count = False

        if "bpm" in recording.acousticbrainz:
            self.print_bpm = True
        else:
            self.print_bpm = False

        if "moods" in recording.acousticbrainz:
            self.print_moods = True
        else:
            self.print_moods = False

        if "genres" in recording.musicbrainz or "tags" in recording.musicbrainz:
            self.print_genre = True
        else:
            self.print_genre = False

    def print(self, entity):
        """ Print out a list(Recording) or list(Playlist). """

        if type(entity) == Recording:
            self.print_recording(entity)
            return

        if type(entity) == list and type(entity[0]) == Recording:
            for rec in entity:
                self.print_recording(rec)

        if type(entity) == Playlist:
            for rec in entity.recordings:
                self.print_recording(rec)

        raise PipelineError("You must pass a Recording or list of Recordings or a Playlist to print.")


    def print_recording(self, recording, year=False, listen_count=False, bpm=False, moods=False, genre=False):
        """ Print out a recording, formatting it nicely to fit in a reasonably sized window.
            The year, listen_count, bpm, mood and genre arguments here can override the settings
            gleaned from the first recording submitted to this class"""

        if self.print_year is None:
            self._examine_recording_for_headers(recording)

        if recording.artist is None:
            artist = "[missing]"
        elif recording.artist.name is None:
            if recording.artist.mbids is not None:
                artist = "[[ artist_mbids:%s ]]" % ",".join(recording.artist.mbids)
            elif recording.artist.artist_credit_id is not None:
                artist = "[[ artist_credit_id:%d ]]" % (recording.artist.artist_credit_id)
            else:
                artist = "[[ unknown ]]"
        else:
            artist = recording.artist.name
        if recording.name is None:
            rec_name = "[[ mbid:%s ]]" % recording.mbid
        else:
            rec_name = recording.name
        print("%-60s %-50s" % (rec_name[:59], artist[:49]), end='')

        if self.print_year or year:
            print(" %d" % recording.year, end='')
        if self.print_listen_count or listen_count:
            print(" %4d" % recording.listenbrainz['listen_count'], end='')
        if self.print_bpm or bpm:
            print(" %3d" % recording.acousticbrainz['bpm'], end='')
        if self.print_moods or moods:
            # TODO: make this print more than agg, but given the current state of moods/coverage...
            print(" mood agg %3d" % int(100 * recording.acousticbrainz['moods']["mood_aggressive"]), end='')
        if self.print_genre or genre:
            print(" %s" % ",".join(recording.musicbrainz['genres']), end='')
            print(" %s" % ",".join(recording.musicbrainz['tags']), end='')

        print()