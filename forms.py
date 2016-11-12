from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class MoodButtons(Form):
	anger = SubmitField('Angry')
	joy = SubmitField('Hapy')
	sadness = SubmitField('Sad')
class MoodText(Form):
	test = StringField('Username')
	startButton = SubmitField("That's how I'm feeling baby")
class GoButton(Form):
	go = SubmitField("Let met log into spotify")