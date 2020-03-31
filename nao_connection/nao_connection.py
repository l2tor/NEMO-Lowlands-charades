import qi

import stk.runner
import stk.events
import stk.services
import stk.logging

from gesture_production.joint_position_to_nao import JointPositionToNAO

class ALNaoConnection(object):
    "NAOqi service for the gesture guessing experiment."
    APP_ID = "com.aldebaran.ALNaoConnection"
    def __init__(self):
        #atexit.register(self.cleanup)

        # generic activity boilerplate
        #self.qiapp = qiapp FIXME
        qiapp = stk.runner.init()
        self.events = stk.events.EventHelper(qiapp.session)
        self.s = stk.services.ServiceCache(qiapp.session)
        self.logger = stk.logging.get_logger(qiapp.session, self.APP_ID)
        self.is_logging = False
        self.happy_eyes = False

        # Set audio volume (does not work on virtual robot)
        try:
            self.s.ALAudioDevice.setOutputVolume(90)
        except:
            pass

        # Set eye blinking behavior (does not work on virtual robot, or if the behavior is not installed)
        try:
            self.s.ALBehaviorManager.startBehavior("custom/blinking")
        except:
            pass

    # Initialize the robot, e.g. move it to a starting position
    def start_experiment(self):
        self.s.ALRobotPosture.goToPosture("Stand", 0.5)
        self.s.ALMotion.setBreathEnabled("Body", True)
        self.s.ALAnimatedSpeech.setBodyLanguageMode(0)

    def end_experiment(self):
        self.s.ALMotion.setBreathEnabled("Body", False)
        self.s.ALRobotPosture.goToPosture("Crouch", 0.5)
        self.s.ALMotion.setStiffnesses("Body", 0.0)

    def set_language(self, lang):
        if lang == 'nl':
            self.s.ALTextToSpeech.setLanguage("Dutch")
            self.s.ALTextToSpeech.setVolume(0.65)
            self.s.ALTextToSpeech.setParameter("speed", 80)
        else:
            self.s.ALTextToSpeech.setLanguage("English")
            self.s.ALTextToSpeech.setVolume(0.8)
            self.s.ALTextToSpeech.setParameter("speed", 75)

    def say(self, text):
        self.s.ALAnimatedSpeech.say(text)
        print "TTS: " + text

    # 'Play back' an existing recording from a different participant
    def perform_gesture(self, gesture):
        for i in range(0, len(gesture.timestamps)):
            # We delay the gesture a bit so that it is less likely for the robot to tip over (and less loss in detail)
            gesture.timestamps[i] += 0.5 + 0.025 * (i+1)

        positioncalc = JointPositionToNAO()

        # # Version without sampling
        # nao_joints = positioncalc.get_nao_joints(gesture)
        # nao_joints[1] = zip(*nao_joints[1])
        # stamps = list()
        # for i in range(0, len(nao_joints[0])):
        #     stamps.append(gesture.timestamps)
        # self.s.ALMotion.angleInterpolation(nao_joints[0], nao_joints[1], stamps, True)

        # Sampling so that we don't get "body max velocity not respected" errors from NAO (moving too fast)
        sample = 0.3
        current_time = gesture.timestamps[0] + sample
        to_play = list()
        to_play_stamps = list()
        to_play.append(0)
        to_play_stamps.append(gesture.timestamps[0])

        for i in range(15, min(170, len(gesture.timestamps)-45)): # We remove the last one and a half second and shorten if needed
            if abs(gesture.timestamps[i] - current_time) > abs(gesture.timestamps[i-1] - current_time):
                to_play.append(i-1)
                to_play_stamps.append(gesture.timestamps[i-1])
                current_time = gesture.timestamps[i-1] + sample

        angle_names = list()
        to_play_nao = list()

        # Reformat the structure so that it fits the parameters of the ALMotion.angleInterpolation call
        for i in range(0, len(to_play)):
            nao_joints = positioncalc.get_nao_joints_for_timestamp(gesture, to_play[i])

            if i == 0:
                angle_names = nao_joints[0]

            if i == len(to_play)-1:
                nao_joints[1][-2] = 0.0
                nao_joints[1][-1] = 0.0

            to_play_nao.append(nao_joints[1])

        to_play_nao = zip(*to_play_nao)

        stamps = list()
        for i in range(0, len(angle_names)):
            stamps.append(to_play_stamps)

        self.s.ALMotion.angleInterpolation(angle_names, to_play_nao, stamps, True)

    # Marker to set happy eyes
    def happy_feedback(self):
        self.s.ALLeds.rasta(2)
