from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class MoodButtons(Form):
    name = StringField('name', validators=[DataRequired()])

# class MoodButtons(Form):
#     anger = SubmitField('Angry')
#     joy = SubmitField('Hapy')
#     sadness = SubmitField('Sad')

# class MoodText(Form):
#     test = StringField('Username')
#     startButton = SubmitField("That's how I'm feeling baby")

#class PlaylistButton(Form):
#	make = SubmitField("That sounds dank. I'll order 1 playlist of that please")