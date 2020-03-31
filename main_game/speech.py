import random

class Speech:
	content = {
		'nl': {
			'intro': 'Hallo, leuk om jou te zien. Laten we samen een spelletje hints spelen. Ik ga zo iets laten zien met mijn handen en dan moet jij raden wat het is. Daarna moet jij iets uitbeelden en dan ga ik raden. Laten we het een keertje oefenen.',
			'practice_robot_intro': 'Ik begin, hier komt \'ie.',
			'practice_robot_instruction': 'Nu mag jij raden wat dit was, door op de \prn=t E: b l @ t \\ het juiste ding aan te raken.',
			'practice_robot_positive_feedback': 'Goed zo, het was inderdaad een bril!',
			'practice_robot_negative_feedback': 'Helaas, ik probeerde een bril uit te beelden.',
			'practice_participant_instruction': 'Nu ben jij aan de beurt. Er verschijnt zo iets op de \prn=t E: b l @ t \\, en dat ga ik dan raden.',
			'practice_participant_instruction_2': 'Druk op de knop als je er klaar voor bent, dan telt de \prn=t E: b l @ t \\ af van 3, 2, 1 en mag je het laten zien.',
			'practice_participant_feedback': 'Dat is vast een bal! Ja, ik heb het goed!',
			'practice_participant_explanation_classification_1': 'Ik zal je op de \prn=t E: b l @ t \\ steeds laten zien wat ik dacht dat het was, kijk maar.',
			'practice_participant_explanation_classification_2': 'Ik wist best zeker dat het een bal was, maar ik dacht dat het misschien ook een molen was.',
			'practice_participant_finished': 'Laten we nu beginnen met het echte spel. Ik zal weer eerst gaan.',
			'outro_1': 'Dat was het!',
			'outro_robot_wins': 'Je hebt het super goed gedaan.',
			'outro_participant_wins': 'Je deed het beter dan ik, gefeliciteerd!',
			'outro_2': 'Ik vond het leuk om met je te spelen. Tot de volgende keer!',			
			'robot_turn': [
				'Ik ben aan de beurt.',
				'Oke, mijn beurt.',
				'Nu zal ik weer iets uitbeelden.'
			],
			'robot_last_turn': 'Dit is de laatste ronde.',
			'robot_turn_start': [
				'Komt \'ie.',
				'Daar ga ik.'
			],
			'robot_turn_end': [
				'Nu mag jij raden wat dit was.',
				'Wat was dit?',
				'Weet je het?'
			],
			'robot_turn_end_second_attempt': [
				'Probeer het nog eens te raden.',
				'Weet je het nu?'
			],
			'robot_try_again': [
				'Ik probeer het nog een keer.',
				'Wacht, nog eens.',
				'Ik doe hem nog eens.'
			],
			'participant_turn': [
				'Nu jij.',
				'Jij bent aan de beurt.',
				'Ik ben benieuwd wat het volgende ding is.'
			],
			'participant_try_again': [
				'Kun je het nog eens uitbeelden?',
				'Laten we het nog een keer proberen.',
				'Poging 2, nog een keer!'
			],
			'positive_feedback': [
				'Goed zo! Het was [obj]',
				'Super! [obj]!'
			],
			'negative_feedback': [
				'Helaas, het is geen [obj]',
				'Nee, dat was geen [obj]',
				'[obj] is niet goed!'
			],
			'correct_answer': [
				'Dat was [obj]',
				'Het was [obj]',
				'Ik probeerde [obj] uit te beelden.'
			],
			'robot_guess': [
				'Ik denk dat het [obj] is.',
				'Volgens mij is het [obj].',
				'Dat is... [obj].',
				'Aha... Misschien [obj]?'
			],
			'positive_feedback_self': [
				'Ik had hem goed, het was [obj]!',
				'Jippie! [obj]!'
			],
			'negative_feedback_self': [
				'Ik had hem fout, jammer!',
				'O nee, dat is niet goed.'
			]
		},
		'en': {
			'intro': 'Hello, it\'s great to see you. Let\'s play a game of charades together. I will show you something with my hands and you will have to guess what it is. After that, you will show me something and I will guess. Let\'s do a practice round.',
			'practice_robot_intro': 'I\'ll go first, watch me.',
			'practice_robot_instruction': 'Now you can guess what this was, by touching the object on the tablet.',
			'practice_robot_positive_feedback': 'Well done, it was indeed glasses!',
			'practice_robot_negative_feedback': 'Too bad, I tried to show you glasses.',
			'practice_participant_instruction': 'Now it\'s your turn. Something will appear on the tablet soon, and I will try to guess what it is.',
			'practice_participant_instruction_2': 'Press the button when you\'re ready, and then the tablet will count down from 3, 2, 1, and then you can start to show me.',
			'practice_participant_feedback': 'That must be a ball! Yes, I got it right!',
			'practice_participant_explanation_classification_1': 'I will use the tablet to show you what I thought the object was, look.',
			'practice_participant_explanation_classification_2': 'I was pretty sure that it was a ball, but I thought it might have been a mill, as well.',
			'practice_participant_finished': 'Now let\'s start playing for real. I\'ll go first.',
			'outro_1': 'That was all!',
			'outro_robot_wins': 'You did very well.',
			'outro_participant_wins': 'You did better than I did, congratulations!',
			'outro_2': 'I enjoyed playing with you. See you next time!',			

			'robot_turn': [
				'Now it\'s my turn.',
				'Okay, my turn.',
				'Now I will show you something again.'
			],
			'robot_last_turn': 'This is the last round.',			
			'robot_turn_start': [
				'Starting now.',
				'Here I go.'
			],
			'robot_turn_end': [
				'Now you can guess what this was.',
				'What was this?',
				'Do you know what this was?'
			],
			'robot_turn_end_second_attempt': [
				'Try guessing it again.',
				'Do you know now?'
			],
			'robot_try_again': [
				'I\'ll try again.',
				'Wait, once more.',
				'I\'m going to do it again.'
			],
			'participant_turn': [
				'Now you\'re up.',
				'It\'s your turn.',
				'I wonder what the next one will be.'
			],
			'participant_try_again': [
				'Can you show me again?',
				'Let\'s try it again.',
				'Once more!'
			],
			'positive_feedback': [
				'Well done! It was [obj]',
				'Super! [obj]!'
			],
			'negative_feedback': [
				'Sorry, it\'s not [obj]',
				'No, that was not [obj]',
				'[obj] is not it!'
			],
			'correct_answer': [
				'That was [obj]',
				'It was [obj]',
				'I tried to show you [obj].'
			],
			'robot_guess': [
				'I think it\'s [obj].',
				'I believe that is [obj].',
				'That is... [obj].',
				'Maybe [obj]?'
			],
			'positive_feedback_self': [
				'I was right, it was [obj]!',
				'Yay! [obj]!'
			],
			'negative_feedback_self': [
				'That was wrong, too bad!',
				'Oh no, that\'s not right.'
			]
		}
	}

	@staticmethod
	def get(lang, key):
		random.seed()

		if type(Speech.content[lang][key]) is list:
			return Speech.content[lang][key][random.randint(0, len(Speech.content[lang][key])-1)]
		else:
			return Speech.content[lang][key]