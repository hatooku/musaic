import json
import time
from musixmatch import track as TRACK
from multiprocessing import Pool, Queue, Process
import random as rand

def get_lyrics(track, artist):
    '''
    Gets the lyrics of a song given the track and artist

    Uses musicmaxtch to retrive the first result of a song searching by
    artist and title. If there are no results or the result is not in
    english, an empty string is returned. Otherwise, the lyrics are returned
    as a string.
    '''
    song_results = TRACK.search(q_track=track, q_artist=artist,
                                f_has_lyrics=True)
    if len(song_results) > 0:
        lyrics_dict = song_results[0].lyrics()
        if lyrics_dict['lyrics_language'] != 'en':
            # print 'Song is not in English:  '+ track + " by " + artist
            return ''
        # -58 to remove the characters they add at the end about copyright
        lyrics = lyrics_dict['lyrics_body'][0: len(lyrics_dict['lyrics_body']) - 58]
        # print "got lyrics for: " + track + " by " + artist
        return lyrics

    else:
        # print 'no results for: '+ track + " by " + artist
        return ''


def get_all_lyrics(input_tracks):
    '''
    Gets all lyrics for all songs in input track list in parallel.
    '''
    def queue_song(queue, song):
        queue.put((song[2], get_lyrics(song[0], song[1])))
    queue = Queue()
    processes = []
    for song in input_tracks:
        p = Process(target=queue_song, args=(queue, song))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    output_lyric_list = []
    while not queue.empty():
        out_lyrics = queue.get()
        if out_lyrics[1] != '':
            output_lyric_list.append(out_lyrics)

    return output_lyric_list


if __name__ == '__main__':
    '''Examples using the songs in our spotify library used to ensure that
        our demo only bothered using songs that we coudl get lyrics for.
        They're vaguely sorted by their tone anaysis.

        '''
    a = ('Joy To The World', 'Three Dog Night')
    l = ('Martha My Dear - Remastered', 'The Beatles')
    m = ('I feel fine - Remastered', 'The Beatles')
    g = ("Happy", "Pharrell Williams")

    c = ('Last Resort', 'Papa Roach')
    d = ("You're a mean one, Mr. Grinch", 'Thurl Ravenscroft')
    j = ('Welcome to the black parade', 'My Chemical Romance')
    k = ('Teenagers', 'My Chemical Romance')

    e = ("Afraid", "The Neighbourhood")
    f = ("Fear of the Dark", "Iron Maiden")

    h = ('I hate everything about you', 'Three Days Grace')
    i = ('Someone like you', 'Adele')
    b = ('Hello', 'Adele')
    n = ("Careless Whisper", 'George Michael')
    o = ("I'll Cry Instead - Remastered", "The Beatles")
    test_cases = [a, b, c, d, e, f, g, h, i, j, k, l, m, n, o]
    # make sure non english songs dont' get lyrics
    test_cases.append(('If You', 'Big Bang'))
    for letter in test_cases:
        print get_lyrics(letter[0], letter[1])
