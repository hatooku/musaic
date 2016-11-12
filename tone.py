import json
from watson_developer_cloud import ToneAnalyzerV3


tone_analyzer = ToneAnalyzerV3(
   username="03caa1c4-b0aa-4cd9-a040-2449c087fa0a",
   password="mfLRLZmBc6Jb",
   version="2016-05-19")

def get_emotions(lyrics):
    """Returns the emotions contained in the lyrics.

    Args:
        lyrics (str): lyrics to be analyzed

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