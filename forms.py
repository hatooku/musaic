from flask_wtf import Form
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

class MoodButtons(Form):
    anger = SubmitField('Angry')
    joy = SubmitField('Happy')
    sadness = SubmitField('Sad')

class MoodText(Form):
    text = TextAreaField('Mood')
    startButton = SubmitField("Submit")

class PlaylistButton(Form):
	make = SubmitField("That sounds dank. I'll order 1 playlist of that please")
