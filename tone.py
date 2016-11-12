import json
import time
from watson_developer_cloud import ToneAnalyzerV3
from multiprocessing import Pool, Queue, Process


tone_analyzer = ToneAnalyzerV3(
   username="03caa1c4-b0aa-4cd9-a040-2449c087fa0a",
   password="mfLRLZmBc6Jb",
   version="2016-05-19")

def get_emotions(lyrics):
    """Returns the emotions contained in the lyrics.

    Args:
        lyrics (tuple): the lyrics to be analyzed

    Returns:
        data (dict): Valid keys are 'anger', 'joy', 'fear', 'sadness', 'disgust'
            The values are the scores for each emotion.

    """
    result = tone_analyzer.tone(text=lyrics, tones="emotion", sentences="false")
    tones = result['document_tone']['tone_categories'][0]["tones"]

    data = {}
    for tone_data in tones:
        data[str(tone_data['tone_id'])] = tone_data['score']
        
    return data

def get_all_emotions(songs_arr):
    """Computes the emotions for the given array of songs in parallel.

    Args:
        songs_arr (arr): Array of songs in the form (id, lyrics)

    Returns:
        data (arr): Array of song data in the form (id, emotions) where
            emotions is the dict defined in get_emotions.
    """
    def analyze_lyrics(queue, song):
        queue.put((song[0], get_emotions(song[1])))
    queue = Queue()
    processes = []
    for song in songs_arr:
        p = Process(target=analyze_lyrics, args=(queue, song))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    data = []

    while not queue.empty():
        data.append(queue.get())

    return data

