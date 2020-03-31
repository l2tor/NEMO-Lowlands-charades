__version__ = "0.0.3"

__copyright__ = "Copyright 2015, Aldebaran Robotics"
__author__ = 'Jan de Wit'
__email__ = 'jan@neryana.com'


import json
import random
import os
import time #temp
# import atexit

import threading

from websocket_connection import WebsocketConnection
from socket_connection import SocketConnection
from dataset_management.our_import import OurImport
from dataset_management.gesture_classes import Pose
from gesture_classification.gesture_classifier import GestureClassifier
from dataset_management.datamanager import DataManager
from feature_extraction.gesture_feature_extractor import GestureFeatureExtractor
from gesture_production.gesture_clusters import GestureClusters
from nao_connection.nao_connection import ALNaoConnection

from speech import Speech
from concepts import Concepts


class MainGame():
    def __init__(self):
        random.seed()

        # set this to store/retrieve data elsewhere
        self.data_dir = 'data'
        self.lang = 'nl'

        # Load dataset with gist of previous gestures and link it to the classifier
        self.gist_dataset = self._load_or_generate_dataset()
        self.classifier = GestureClassifier(self.gist_dataset)

        # Load previous clusters and weights
        self.clusters = self._load_or_generate_clusters()
        self.current_sample = None
        self.current_cluster_id = -1
        self.current_sample_id = -1
        self.num_answer_attempts = 0
        self.previous_guess = None
        self.previous_recording = None

        # Set up the concepts to be used in a session
        self._fill_available_concepts()
        self.concepts_robot = list()
        self.concepts_participant = list()
        self.concepts_used = list()

        # Settings that come from the control panel
        self.participant_id = ""
        self.is_young_participant = False

        # Change the number of rounds to play here (it will be done 2x, so N robot rounds + N participant rounds)
        self.num_concepts = 5

        # Set this to true to only record gestures without the robot performing/guessing
        self.record_only = False

        # Keeping score to use different texts at the end of the experience
        self.num_correct_participant = 0
        self.num_correct_robot = 0

        # We keep track of totals for the fun of it :-)
        self.total_rounds_robot = 0
        self.total_rounds_participant = 0
        self.total_wins_robot = 0
        self.total_wins_participant = 0

        if os.path.isfile('data/totals.csv'):
            totals_file = open('data/totals.csv', 'r')
            totals_collection = totals_file.read().split(';')
            self.total_rounds_robot = int(totals_collection[0])
            self.total_wins_robot = int(totals_collection[1])
            self.total_rounds_participant = int(totals_collection[2])
            self.total_wins_participant = int(totals_collection[3])

        # Connection with web client
        self.websocket_server = WebsocketConnection(1335, self.message_received)
        self.websocket_server.start()

        # Connection with control panel, Kinect module and camera recording module
        self.socket_server = SocketConnection("maingame", "", 1336, self.message_received)
        self.socket_server.start()

        # Set the connection to the robot here
        self.robot_connection = ALNaoConnection()

        # Create the directory to store the practice gestures, in case it doesn't exist
        if not os.path.exists(self.data_dir + '/practice/ball'):
            os.makedirs(self.data_dir + '/practice/ball')

    # Load the existing dataset of (gists of) previous recordings
    # This will be used to perform gesture recognition
    def _load_or_generate_dataset(self):
        if os.path.isfile("data/gists.csv"):
            return DataManager("data/gists.csv")
        else:
            # Generate gists based on all the recordings found in data folder
            importer = OurImport()
            loaded_data = importer.load(self.data_dir + "/recordings")
            output_mgr = DataManager()

            if loaded_data != None:
                fe = GestureFeatureExtractor()

                # print loaded_data[0][0]
                if isinstance(loaded_data, (list,)):
                    for l in loaded_data:
                        output_mgr.append(fe.get_gesture_features_as_string(l))
                else:
                    output_mgr.append(fe.get_gesture_features_as_string(loaded_data))

                output_mgr.save("data/gists.csv")

            return output_mgr


    # This part ensures that the concepts are balanced across sessions, so that there are approximately
    # the same amount of recordings for each of the included concepts.
    def _fill_available_concepts(self):
        self.available_concepts_robot = list(Concepts.items)
        self.available_concepts_participant = list(Concepts.items)
        max_count = 0
        counts = dict()

        for concept, val in self.clusters.iteritems():
            counts[concept] = 0

            for cluster in val:
                counts[concept] += len(cluster["samples"])

            if counts[concept] > max_count:
                max_count = counts[concept]

        self.tmp_counts = counts

        for concept, val in counts.iteritems():
            for i in range(0, (max_count-val)):
                self.available_concepts_participant.append(Concepts.find(concept))


    # Start the main game -- this is triggered by pressing the start button
    # on the control panel
    def start_game(self, participant_id, is_young_participant):
        print "Starting the game by sending message to web client"
        self.participant_id = participant_id
        self.is_young_participant = is_young_participant
        self.num_correct_participant = 0
        self.num_correct_robot = 0

        # Logging
        if not os.path.exists('data/logs'):
            os.makedirs('data/logs')

        self.logfile = 'data/logs/' + participant_id + '_' + time.strftime('%Y%m%d%H%M%S') + '.log'

        self._log('start_game(participant_id=' + participant_id + ',is_young_participant=' + str(is_young_participant) + ')')

        print "yo1"
        self.socket_server.send("kinectrecorder", "SetParticipantData(" + participant_id + "," + is_young_participant + ")")
        self.socket_server.send("stereorecorder", "SetParticipantData(" + participant_id + "," + is_young_participant + ")")
        print "yo2"

        # Prepare the robot
        self.robot_connection.start_experiment()

        # Show the language choice on the tablet -- selecting a language
        # will trigger the next step (practice round)
        self.websocket_server.send("show_language_choice")


    # Callback from the tablet game, set the language and start the introduction
    def set_language(self, lang):
        # Currently we support Dutch and English, but it should be easy to
        # add new language:
        # 1. Add a button for it to the tablet game
        # 2. Make sure the texts in this file (for practice round) are translated
        # 3. Translate the terms in the speech.py file
        self.lang = lang

        self._log("set_language(" + lang + ")")

        self.robot_connection.set_language(lang)

        # Now we can also start the introduction
        self._introduction()


    # The robot explains the game, and starts the first practice round
    def _introduction(self):
        self.concept_index = 0
        self._pick_concepts()
        self._log("concepts_robot(" + json.dumps(self.concepts_robot) + ")")
        self._log("concepts_participant(" + json.dumps(self.concepts_participant) + ")")

        # The record-only mode is implemented at some point to quickly make
        # a set of initial recordings. Has not been used since ;)
        if self.record_only:
            self._do_participant_turn()
        else:
            # The robot will introduce itself and the game
            self.robot_connection.say(Speech.get(self.lang, 'intro'))
            self.is_practice = True
            # Then the robot will start with a practice run, where it will
            # perform the gesture for the concept 'glasses'
            self._do_robot_practice_turn()


    # Pick the 5 concepts that the participant should portray, and 5 that
    # the robot will perform (random, but we try to balance the amount
    # of recordings across sessions).
    def _pick_concepts(self):
        # Make a subset of the concepts to train
        self.concepts_used = list()
        self.concepts_robot = list()
        self.concepts_participant = list()

        while len(self.concepts_participant) < self.num_concepts:
            if len(self.available_concepts_participant) == 0:
                self.available_concepts_participant = list(Concepts.items)

            index = random.randint(0, len(self.available_concepts_participant)-1)
            if self.available_concepts_participant[index] not in self.concepts_participant:
                self.concepts_participant.append(self.available_concepts_participant.pop(index))

        while len(self.concepts_robot) < self.num_concepts:
            if len(self.available_concepts_robot) == 0:
                self.available_concepts_robot = list(Concepts.items)

            overlap_total = 0

            for i in self.available_concepts_robot:
                if i in self.concepts_robot or i in self.concepts_participant:
                    overlap_total += 1

            if overlap_total == len(self.available_concepts_robot):
                self.available_concepts_robot.extend(list(Concepts.items))

            index = random.randint(0, len(self.available_concepts_robot)-1)
            if self.available_concepts_robot[index] not in self.concepts_robot and self.available_concepts_robot[index] not in self.concepts_participant:
                self.concepts_robot.append(self.available_concepts_robot.pop(index))


    # Practice round of the robot
    def _do_robot_practice_turn(self):
        self.robot_connection.say(Speech.get(self.lang, 'practice_robot_intro'))

        # This loads a recorded gesture (.csv format, from Kinect)
        # and plays it back. In the practice round, we always use the same one.
        importer = OurImport()
        gesture = importer.load(self.data_dir + "/practice/glasses/glasses_practice.csv")
        self.robot_connection.perform_gesture(gesture)

        # These are the answers included only for the practice round
        # If you want to add another language, don't forget to translate the
        # terms here. These are not part of the recorded set of 35 items.
        answer_data = dict()
        answer_data["correct_answer"] = "glasses"

        answer_data["answers"] = [
            {
                'id': 'windmill',
                'description': {
                    'nl': 'Molen',
                    'en': 'Mill'
                },
                'article': {
                    'nl': 'Een',
                    'en': 'A'
                },
                'category': 'static',
                'image_filename': 'windmill.png'
            },
            {
                'id': 'glasses',
                'description': {
                    'nl': 'Bril',
                    'en': 'Glasses'
                },
                'article': {
                    'nl': 'Een',
                    'en': 'A'
                },
                'category': 'tools',
                'image_filename': 'glasses.png'
            },
            {
                'id': 'elephant',
                'description': {
                    'nl': 'Olifant',
                    'en': 'Elephant'
                },
                'article': {
                    'nl': 'Een',
                    'en': 'An'
                },
                'category': 'animate',
                'image_filename': 'elephant.png'
            },
            {
                'id': 'teapot',
                'description': {
                    'nl': 'Theepot',
                    'en': 'Teapot'
                },
                'article': {
                    'nl': 'Een',
                    'en': 'A'
                },
                'category': 'tools',
                'image_filename': 'teapot.png'
            }
        ]

        # Present answers to the participant on the tablet
        self.websocket_server.send("show_answers(" + json.dumps(answer_data) + ")")
        self._log("robot_practice_turn()")
        self.robot_connection.say(Speech.get(self.lang, 'practice_robot_instruction'))


    # Normal (non-practice) round of the robot
    def _do_robot_turn(self):
        # Hide previous results screen from the participant's turn (if applicable)
        self.websocket_server.send("hide_classification()")
        self.num_answer_attempts = 0
        self.current_concept = self.concepts_robot[self.concept_index]
        self.concepts_used.append(self.current_concept)

        print "Showing: " + self.current_concept["id"]

        if self.concept_index < (self.num_concepts-1) and self.concept_index > 0:
            self.robot_connection.say(Speech.get(self.lang, 'robot_turn'))

        # The robot indicates that we're about to start the last round
        elif self.concept_index == (self.num_concepts - 1):
            self.robot_connection.say(Speech.get(self.lang, 'robot_last_turn'))

        self.robot_connection.say(Speech.get(self.lang, 'robot_turn_start'))

        self._pick_and_perform()

        # Randomly pick three distractor objects. At the moment they can be any of the available concepts.
        answers = list()
        answers.append(self.current_concept)

        for i in range(0, 3):
            answer = Concepts.items[random.randint(0, len(Concepts.items)-1)]

            while answer in answers or answer in self.concepts_used:
                answer = Concepts.items[random.randint(0, len(Concepts.items)-1)]

            answers.append(answer)

        # Shuffle answers
        random.shuffle(answers)

        answer_data = dict()
        answer_data["answers"] = answers
        answer_data["correct_answer"] = self.current_concept["id"]

        # Send them to the tablet
        self.websocket_server.send("show_answers(" + json.dumps(answer_data) + ")")
        self._log("robot_turn(concept=" + self.current_concept["id"] + ",answers_presented=" + json.dumps(answer_data) + ")")

        self.robot_connection.say(Speech.get(self.lang, 'robot_turn_end'))


    # Second turn of the robot. It will again pick a recording to perform,
    # so in many cases this will result in another recording for the same item.
    def _do_robot_second_turn(self):
        self._log("robot_second_turn()")
        self.robot_connection.say(Speech.get(self.lang, 'robot_turn_start'))

        self._pick_and_perform()

        self.websocket_server.send("enable_answers()")


    # Pick a recording from the existing set (either the ones initially added
    # by the researchers, or previously recorded from another participant)
    def _pick_and_perform(self):
        worked = False

        while not worked:
            try:
                sample = self._pick_sample(self.current_concept["id"])
                filename = self.data_dir + "/recordings/" + self.current_concept["id"] + "/" + sample["filename"] + ".csv"

                if os.path.isfile(filename):
                    # Now play it back
                    importer = OurImport()
                    gesture = importer.load(filename)
                    self.robot_connection.perform_gesture(gesture)
                    worked = True
            except:
                pass


    # This picks a previously recorded gesture for the robot to perform
    def _pick_sample(self, current_concept):
        # First pick a cluster, 60% exploitation 40% exploration
        # Find the maximum weight cluster (to either take it or ignore it)
        cluster = self.clusters[current_concept][0]
        cluster_index = 0

        log_str = "sample_selected(concept=" + current_concept + ",num_clusters=" + str(len(self.clusters[current_concept])) + ",cluster_strategy="

        if len(self.clusters[current_concept]) > 1:
            max_cluster_index = 0
            is_exploration = random.randint(1, 10) <= 4

            for c in range(1, len(self.clusters[current_concept])):
                if self.clusters[current_concept][c]["weight"] > cluster["weight"]:
                    cluster = self.clusters[current_concept][c]
                    max_cluster_index = c

            if is_exploration: # Take any cluster *but* the one with the highest weight assigned to it
                log_str += "exploration,cluster_choice="
                print "Exploring clusters... " + str(max_cluster_index) + " is max."
                rand = max_cluster_index

                while rand == max_cluster_index:
                    rand = random.randint(0, len(self.clusters[current_concept])-1)

                print "I picked: " + str(rand)

                cluster = self.clusters[current_concept][rand]
                cluster_index = rand
                log_str += str(rand) + ",cluster_weight=" + str(cluster["weight"]) + ","
            else: # 'exploit' the highest rated cluster
                cluster_index = max_cluster_index
                cluster = self.clusters[current_concept][max_cluster_index]
                log_str += "exploitation,cluster_choice=" + str(max_cluster_index) + ",cluster_weight=" + str(cluster["weight"]) + ","
        else:
            log_str += "only_one,cluster_choice=0,cluster_weight=" + str(cluster["weight"]) + ","

        # Then pick a sample, 60% exploitation 40% exploration
        # Find the maximum weight sample (to either take it or ignore it)
        sample = cluster["samples"][0]
        sample_index = 0

        log_str += "num_samples=" + str(len(cluster["samples"])) + ",sample_strategy="

        if len(cluster["samples"]) > 1:
            max_sample_index = 0
            is_exploration = random.randint(1, 10) <= 4

            for s in range(1, len(cluster["samples"])):
                if cluster["samples"][s]["weight"] > sample["weight"]:
                    sample = cluster["samples"][s]
                    max_sample_index = s

            if is_exploration: # Take any recording *but* the one with the highest weight assigned to it
                log_str += "exploration,"
                print "Exploring samples... " + str(max_sample_index) + " is max."
                rand = max_sample_index

                while rand == max_sample_index:
                    rand = random.randint(0, len(cluster["samples"])-1)

                print "I picked: " + str(rand)
                sample = cluster["samples"][rand]
                sample_index = rand
            else: # 'exploit' the highest rated recording
                log_str += "exploitation,"
                sample = cluster["samples"][max_sample_index]
                sample_index = max_sample_index
        else:
            log_str += "only_one,"

        log_str += "sample_choice=" + str(sample_index) + ",sample_filename=" + sample["filename"] + ",sample_weight=" + str(sample["weight"]) + ")"
        self._log(log_str)
        print log_str
        self.current_cluster_id = cluster_index
        self.current_sample_id = sample_index
        return sample

    # This callback is triggered once the participant guesses an item from the tablet,
    # after the robot has performed a gesture.
    def answer_given(self, answer):
        print "Answer received: " + answer

        # If this is a practice run, the correct answer is always 'glasses'
        if self.is_practice:
            self._log("practice_answer_given(correct=glasses,given=" + answer + ")")
            if answer == "glasses": # Correct answer
                self.robot_connection.happy_feedback()
                self.robot_connection.say(Speech.get(self.lang, 'practice_robot_positive_feedback'))
            else: # Incorrect answer
                self.robot_connection.say(Speech.get(self.lang, 'practice_robot_negative_feedback'))

            # In the practice run, regardless of whether the answer was correct,
            # we always move on to the next step (second part of practice run)
            self._do_participant_practice_turn()

        # Correct answer -- increase weights for the performed recording
        elif answer == self.current_concept['id']:
            self._log("answer_given(correct=" + self.current_concept['id'] + ",given=" + answer + ")")
            if self.num_answer_attempts == 0: # Got it right the first time
                self.clusters[self.current_concept['id']][self.current_cluster_id]["weight"] += 1
                self.clusters[self.current_concept['id']][self.current_cluster_id]["samples"][self.current_sample_id]["weight"] += 1
            else: # Got it right on the second attempt -- less of an increase to the weights because higher chance of guessing correctly
                self.clusters[self.current_concept['id']][self.current_cluster_id]["weight"] += 0.75
                self.clusters[self.current_concept['id']][self.current_cluster_id]["samples"][self.current_sample_id]["weight"] += 0.75

            fb = Speech.get(self.lang, 'positive_feedback')
            fb = fb.replace('[obj]', self.current_concept['article'][self.lang] + " " + self.current_concept['description'][self.lang])
            self.num_correct_participant += 1

            self.total_rounds_participant += 1 # it is a participant guessing
            self.total_wins_participant += 1
            self._save_totals() # Keep track of the scores

            self.robot_connection.happy_feedback()
            self.robot_connection.say(fb)
            self._do_participant_turn() # Robot turn over, on to the participant's turn

        # Incorrect answer -- decrease weights for the performed recording
        else:
            self._log("answer_given(correct=" + self.current_concept['id'] + ",given=" + answer + ")")
            self.num_answer_attempts += 1

            self.total_rounds_participant += 1 # it is a participant guessing
            self._save_totals()

            neg_feedback = Speech.get(self.lang, 'negative_feedback')
            neg_feedback = neg_feedback.replace('[obj]', Concepts.find(answer)["description"][self.lang])
            self.robot_connection.say(neg_feedback)

            if self.num_answer_attempts == 1:
                self.clusters[self.current_concept['id']][self.current_cluster_id]["weight"] -= 1
                self.clusters[self.current_concept['id']][self.current_cluster_id]["samples"][self.current_sample_id]["weight"] -= 1
                self.robot_connection.say(Speech.get(self.lang, 'robot_try_again'))
                self._do_robot_second_turn()
            else:
                self.clusters[self.current_concept['id']][self.current_cluster_id]["weight"] -= 0.75
                self.clusters[self.current_concept['id']][self.current_cluster_id]["samples"][self.current_sample_id]["weight"] -= 0.75
                correct_answer = Speech.get(self.lang, 'correct_answer')
                correct_answer = correct_answer.replace('[obj]', self.current_concept["article"][self.lang] + " " + self.current_concept["description"][self.lang])
                self.robot_connection.say(correct_answer)
                self._do_participant_turn()


    # Practice round of the participant (the participant has to perform a gesture for ball)
    def _do_participant_practice_turn(self):
        self.websocket_server.send("hide_answers()")

        # Some introduction by the robot
        self.robot_connection.say(Speech.get(self.lang, 'practice_participant_instruction'))
        self.robot_connection.say(Speech.get(self.lang, 'practice_participant_instruction_2'))

        # The concept to perform is always 'ball' in the practice round
        # When adding a new language, don't forget to translate this term.
        concept = {
            'id': 'ball',
            'description': {
                'nl': 'Bal',
                'en': 'Ball'
            },
            'article': {
                'nl': 'Een',
                'en': 'A'
            },
            'category': 'entertainment',
            'image_filename': 'ball.png'
        }

        self._log("participant_practice_turn()")

        # Show the ball on the tablet screen so the participant knows
        # what to perform a gesture for.
        self.websocket_server.send("show_item(" + json.dumps(concept) + ")")


    # Normal (non-practice) round of the participant
    def _do_participant_turn(self):
        self.previous_guess = None
        self.previous_recording = None

        # Hide the previous screen on the tablet (if needed)
        self.websocket_server.send("hide_answers()")
        self.num_answer_attempts = 0

        # Pick a concept that the participant should perform
        self.current_concept = self.concepts_participant[self.concept_index]
        self.concepts_used.append(self.current_concept)

        if not self.record_only:
            self.robot_connection.say(Speech.get(self.lang, 'participant_turn'))

        # Send concept to the web client
        self.websocket_server.send("show_item(" + json.dumps(self.current_concept) + ")")
        self._log("participant_turn(" + self.current_concept['id'] + ")")


    # The participant's second attempt is straight-forward: we just enable the
    # button to start recording again.
    def _do_participant_second_turn(self):
        self._log("participant_second_turn()")
        self.websocket_server.send("enable_item()")

    # This function is triggered when the 'stop recording' button on the
    # control panel is pressed, in case the Kinect does not manage to
    # automatically detect the end of a gesture.
    def gesture_finished(self):
        self.socket_server.send("kinectrecorder", "StopRecording")

    # Callback from the KinectRecorder, triggered when it has stopped
    # recording the gesture and has saved it to file.
    def recording_completed(self, concept, filename):
        print "Recording completed: " + filename
        self._log('recording_completed(concept=' + concept + ',filename=' + filename + ')')

        # Temporary path introduced to efficiently record gestures without
        # completing the entire game.
        if self.record_only:
            self.concept_index += 1

            if self.concept_index < len(self.concepts_participant):
                self._do_participant_turn()

        # "Normal" situation, but in a practice round
        elif self.is_practice:
            # The robot will always guess correctly in the practice round
            self.robot_connection.happy_feedback()
            self.robot_connection.say(Speech.get(self.lang, 'practice_participant_feedback'))

            # Also introduce the feedback on the classification that is shown on the tablet
            guesses = list()
            guesses.append({
                'item': {
                    'id': 'ball',
                    'description': {
                        'nl': 'Bal',
                        'en': 'Ball'
                    },
                    'article': {
                        'nl': 'Een',
                        'en': 'A'
                    },
                    'category': 'entertainment',
                    'image_filename': 'ball.png'
                },
                'percentage': 0.85
            })
            guesses.append({
                'item': {
                    'id': 'windmill',
                    'description': {
                        'nl': 'Molen',
                        'en': 'Mill'
                    },
                    'article': {
                        'nl': 'Een',
                        'en': 'A'
                    },
                    'category': 'static',
                    'image_filename': 'windmill.png'
                },
                'percentage': 0.15
            })
            self.robot_connection.say(Speech.get(self.lang, "practice_participant_explanation_classification_1"))

            # This shows the top 3 of candidates for the robot's guess
            self.websocket_server.send("show_classification(" + json.dumps(guesses) + ")")
            self.robot_connection.say(Speech.get(self.lang, "practice_participant_explanation_classification_2"))

            time.sleep(2)

            self.is_practice = False
            self.robot_connection.say(Speech.get(self.lang, "practice_participant_finished"))

            # Now start the actual game, the robot will go first.
            self._do_robot_turn()

        else:
            # First guess and then add it to the dataset, that's the fair way to go :-)

            # Load the newly recorded gesture
            importer = OurImport()
            loaded_data = importer.load(self.data_dir + "/recordings/" + concept + "/" + filename + ".csv")

            # Extract features from it (inflection points and peaks, mapped to relative locations of body joints)
            fe = GestureFeatureExtractor()
            gist = fe.get_gesture_features_as_string(loaded_data)
            gist_list = gist.split(';')

            # Perform the classification (k-NN)
            guess_obj = self.classifier.classify(gist_list, self.previous_guess)
            neighbors = guess_obj[1]
            guess_obj = guess_obj[0]

            print neighbors

            self._log('robot_guess(correct_answer=' + self.current_concept['id'] + ',given=' + guess_obj[0][0] + ',guesses=' + json.dumps(guess_obj) + ',neighbors=' + json.dumps(neighbors) + ')')

            # Retrieve proper descriptions of objects -- these are the top 5 (at most) guesses that will be displayed
            guesses = list()
            for go in guess_obj:
                guesses.append({
                    'item': Concepts.find(go[0]),
                    'percentage': go[1]
                })

            guess = Speech.get(self.lang, 'robot_guess')
            obj = guesses[0]['item']
            guess = guess.replace('[obj]', obj["article"][self.lang] + " " + obj["description"][self.lang])

            # Show the top 5 (at most) candidates, then have the robot announce its #1 guess
            self.websocket_server.send("show_classification(" + json.dumps(guesses) + ")")
            self.robot_connection.say(guess)

            # Pause for dramatic effect...
            time.sleep(2)

            # The robot guessed correctly!
            if guess_obj[0][0] == self.current_concept['id']:
                fb = Speech.get(self.lang, 'positive_feedback_self')
                fb = fb.replace('[obj]', self.current_concept["article"][self.lang] + " " + self.current_concept['description'][self.lang])
                self.num_correct_robot += 1

                self.total_rounds_robot += 1 # it is a robot guessing here
                self.total_wins_robot += 1
                self._save_totals()

                # Announce the robot's victory
                self.robot_connection.happy_feedback()
                self.robot_connection.say(fb)

                # Now we can add it to the existing dataset (for future classification and generation)
                if self.num_answer_attempts == 1:
                    self.gist_dataset.append(self.previous_recording)

                self.gist_dataset.append(gist)
                self.gist_dataset.save("data/gists.csv")
                self._regenerate_cluster(self.current_concept['id'])

                # Move on
                self.concept_index += 1
                self.websocket_server.send("hide_item()")

                print str(self.concept_index) + " " + str(len(self.concepts_participant)) + " " + str(len(self.concepts_robot))

                # Check whether we've covered all 5 items, then end the session
                if self.concept_index == len(self.concepts_participant):
                    self._log('experiment_end(robot_score=' + str(self.num_correct_robot) + ',participant_score=' + str(self.num_correct_participant) + ')')

                    # Announce the end of the session
                    self.robot_connection.say(Speech.get(self.lang, 'outro_1'))

                    # Depending on who guessed most gestures correctly (this is very likely the participant),
                    # we have a slightly different outro
                    if self.num_correct_robot > self.num_correct_participant:
                        self.robot_connection.say(Speech.get(self.lang, 'outro_robot_wins'))
                    else:
                        self.robot_connection.say(Speech.get(self.lang, 'outro_participant_wins'))

                    self.robot_connection.say(Speech.get(self.lang, 'outro_2'))

                    # Clean up
                    self.websocket_server.send("hide_classification()")
                    self.socket_server.send("controlpanel", "ExperimentFinished()")

                    # Robot can rest
                    self.robot_connection.end_experiment()

                else: # This was not the last round, so we proceed with the next turn for the robot to perform
                    self._do_robot_turn()

            # The robot guessed incorrectly!
            else:
                self.total_rounds_robot += 1 # it is a robot guessing
                self._save_totals()

                self.robot_connection.say(Speech.get(self.lang, 'negative_feedback_self'))
                self.num_answer_attempts += 1

                # If this is the first attempt, try again
                if self.num_answer_attempts == 1:
                    self.robot_connection.say(Speech.get(self.lang, 'participant_try_again'))
                    self.websocket_server.send("hide_classification()")
                    self.previous_guess = guess_obj[0][0]
                    self.previous_recording = gist
                    # The participant will be asked to perform another gesture for the same item
                    self._do_participant_second_turn()

                # Otherwise, call it quits and move on :-)
                else:
                    self.concept_index += 1
                    self.websocket_server.send("hide_item()")

                    # Now we can add it to the existing dataset (for future classification and generation)
                    self.gist_dataset.append(self.previous_recording)
                    self.gist_dataset.append(gist)
                    self.gist_dataset.save("data/gists.csv")
                    self._regenerate_cluster(self.current_concept['id'])

                    print str(self.concept_index) + " " + str(len(self.concepts_participant)) + " " + str(len(self.concepts_robot))

                    # Check whether we've covered all 5 items, then end the session
                    if self.concept_index == len(self.concepts_participant):
                        self.robot_connection.say(Speech.get(self.lang, 'outro_1'))

                        # Depending on who guessed most gestures correctly (this is very likely the participant),
                        # we have a slightly different outro
                        if self.num_correct_robot > self.num_correct_participant:
                            self.robot_connection.say(Speech.get(self.lang, 'outro_robot_wins'))
                        else:
                            self.robot_connection.say(Speech.get(self.lang, 'outro_participant_wins'))

                        self.robot_connection.say(Speech.get(self.lang, 'outro_2'))

                        # Clean up
                        self.websocket_server.send("hide_classification()")

                        # Robot can rest
                        self.robot_connection.end_experiment()

                    else: # This was not the last round, so we proceed with the next turn for the robot to perform
                        self._do_robot_turn()


    # We also attempt, using the same similarity score from gesture recognition,
    # to use hierarchical clustering to identify groups of similar gestures,
    # for example those using the same mode of representation.
    # This is not very reliable yet, since the similarity scores are also
    # not perfectly accurate.
    # We assign weights to these clusters, so that the system can use
    # exploration vs exploitation when it comes to selecting the gesture
    # to perform.
    def _load_or_generate_clusters(self):
        clusters = dict()

        if os.path.isfile("data/clusters.json"):
            with open("data/clusters.json", "r") as infile:
                clusters = json.load(infile)

        # Rebuild the clusters from scratch
        else:
            sets = dict()

            for d in self.gist_dataset.data:
                if not d[0] in sets:
                    sets[d[0]] = list()

                sets[d[0]].append(d)


            for item in sets:
                if len(sets[item]) == 1:
                    clusters[item] = list()
                    clusters[item].append({
                        "weight": 0,
                        "samples": list()
                        })
                    clusters[item][0]["samples"].append({
                        "weight": 0,
                        "filename": sets[item][0][1]
                        })
                elif len(sets[item]) > 1:
                    c = GestureClusters(sets[item])
                    item_clusters = c.generate_clusters()
                    clusters[item] = list()

                    for i in range(1, max(item_clusters)+1):
                        for j in range(0, len(item_clusters)):
                            if item_clusters[j] == i:
                                if len(clusters[item]) < i:
                                    clusters[item].append({
                                        "weight": 0,
                                        "samples": list()
                                    })

                                clusters[item][i-1]["samples"].append({
                                    "weight": 0,
                                    "filename": sets[item][j][1]
                                    })


            for i in clusters:
                print i + ": " + str(len(clusters[i]))

            if len(clusters) > 0:
                with open("data/clusters.json", "w") as outfile:
                    json.dump(clusters, outfile)

        return clusters


    # Regenerating the clusters after a new example has been recorded.
    def _regenerate_cluster(self, concept):
        print "regenerating cluster.."
        data_gists = list()

        for d in self.gist_dataset.data:
            if d[0] == concept:
                data_gists.append(d)

        c = GestureClusters(data_gists)
        item_clusters = c.generate_clusters()

        new_cluster = list()
        for i in range(1, max(item_clusters)+1):
            for j in range(0, len(item_clusters)):
                if item_clusters[j] == i:
                    if len(new_cluster) < i:
                        new_cluster.append({
                            "weight": 0,
                            "samples": list()
                        })

                    new_cluster[i-1]["samples"].append({
                        "weight": 0,
                        "filename": data_gists[j][1]
                        })

        for cl in self.clusters[concept]:
            # Transfer old weights if applicable
            max_overlap = -1
            max_overlap_id = -1

            for cl2 in range(0, len(new_cluster)):
                this_overlap = 0

                for s in cl["samples"]:
                    for s2 in new_cluster[cl2]["samples"]:
                        if s["filename"] == s2["filename"]:
                            this_overlap += 1

                if this_overlap > max_overlap:
                    max_overlap = this_overlap
                    max_overlap_id = cl2

            if max_overlap * 1.0 / len(cl["samples"]) >= .5:
                new_cluster[max_overlap_id]["weight"] = cl["weight"]

                # Also copy individual sample weights if overlap was found
                for s in cl["samples"]:
                    for s2 in new_cluster[max_overlap_id]["samples"]:
                        if s["filename"] == s2["filename"]:
                            s2["weight"] = s["weight"]

        # Save it just in case
        self._log('regenerated_clusters(concept=' + concept + ',num_clusters_old=' + str(len(self.clusters[concept])) + ',num_clusters_new=' + str(len(new_cluster)) + ')')

        self.clusters[concept] = new_cluster
        if len(self.clusters) > 0:
            with open("data/clusters.json", "w") as outfile:
                json.dump(self.clusters, outfile)


    # Logging is mostly used to see how the participant and robot performed,
    # and which recordings were used by the robot.
    def _log(self, text):
        with open(self.logfile, "a") as logger:
            now = time.time()
            localtime = time.localtime(now)
            milliseconds = '%03d' % int((now - int(now)) * 1000)

            logger.write(time.strftime('%d-%m-%Y %H:%M:%S') + '.' + str(milliseconds) + ': ' + text + '\n')


    # This keeps track of an overall total score (human vs robot),
    # over all sessions.
    def _save_totals(self):
        with open("data/totals.csv", "w") as outfile:
            outfile.write(str(self.total_rounds_robot) + ';' + str(self.total_wins_robot) + ';' + str(self.total_rounds_participant) + ';' + str(self.total_wins_participant))


    # Message received through the socket connection
    def message_received(self, origin, message):
        print "Message received from " + origin + ": " + message

        # Find out if there was a target of the message
        parts = message.split(':')

        if len(parts) > 1:
            target = parts[0]
            command = parts[1]
        else:
            target = "maingame"
            command = message

        # Check whether the message was for us. If so, handle it, otherwise forward it to correct module.
        if target == "maingame":
            self._handle_message(origin, command)
        else:
            if target == "webclient":
                self.websocket_server.send(command)
            else:
                print "Sending " + command + " to " + target
                self.socket_server.send(target, command, origin)

    # Handle a call to this module, by executing the matching function.
    def _handle_message(self, origin, message):
        print "Message for main game"
        params = list()
        func = message

        if message.find('(') != -1:
            params = message[message.find('(')+1:message.find(')')].split(',')
            func = message[0:message.find('(')]

            for i in range(0, len(params)):
                params[i] = params[i].strip()

        getattr(self, func)(*params)

    # Send an overview of connected clients to the others
    def get_connected_clients(self, return_address):
        connected_clients = list()

        for key, val in self.socket_server.connected_clients.iteritems():
            connected_clients.append(key)

        if self.websocket_server.is_client_connected():
            connected_clients.append("webclient")

        self.socket_server.send(return_address, "update_connected_clients(" + ';'.join(connected_clients) + ")")

    # Before ending the game, store the gists of the gestures, and the clusters
    def exit(self, dummy=None):
        print "Cleaning up...!"
        if len(self.clusters) > 0:
            with open("data/clusters.json", "w") as outfile:
                json.dump(self.clusters, outfile)
        self.gist_dataset.save("data/gists.csv")

        # Send exit message to all connected clients
        # for key, val in self.socket_server.connected_clients.iteritems():
        #     self.socket_server.send("exit()", key)
        self.socket_server.send("kinectrecorder", "exit()")
        self.socket_server.send("stereorecorder", "exit()")

        time.sleep(2)

        # Now exit ourselves ;-)
        self.socket_server.stop()
        self.websocket_server.stop()

    # def cleanup(self):
    #     print "Cleaning up...!"
    #     if len(self.clusters) > 0:
    #         with open("data/clusters.json", "w") as outfile:
    #             json.dump(self.clusters, outfile)
    #     self.gist_dataset.save("data/gists.csv")
    #
    # # Send an exit message to those clients that need a trigger to shut down
    # def exit(self, dummy=""):
    #     # Send exit message to all connected clients
    #     # for key, val in self.socket_server.connected_clients.iteritems():
    #     #     self.socket_server.send("exit()", key)
    #     self.socket_server.send("stereorecorder", "exit()")
    #
    #     time.sleep(2)
    #
    #     # Now exit ourselves ;-)
    #     self.stop()


#     @qi.bind(returnType=qi.Void, paramsType=[])
#     def stop(self):
#         self.logger.info("ALGestureGame stopped by user request.")
#         self.qiapp.stop()
#
#     @qi.nobind
#     def on_stop(self):
#         self.socket_server.stop()
#         self.websocket_server.stop()
#         self.logger.info("ALGestureGame finished.")
#
# ####################
# # Setup and Run
# ####################
#
if __name__ == "__main__":
    game = MainGame()
