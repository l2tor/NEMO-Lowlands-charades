import os
from stat import *
import csv

from dataset_management.gesture_classes import Gesture, HandState, FaceOrientation

class OurImport():
	def load(self, file_or_directory):
		all_gestures = list()

		# Check whether we're supposed to load a single file or a bunch of files
		mode = os.stat(file_or_directory)[ST_MODE]
		if S_ISREG(mode):
			all_gestures = self.load_file(file_or_directory)

		else:
			for filename in os.listdir(file_or_directory):
				# We assume that in this case we are dealing with a directory of directories (one per item)
				mode = os.stat(file_or_directory + '/' + filename)[ST_MODE]
				if not S_ISREG(mode):
					for filename2 in os.listdir(file_or_directory + '/' + filename):

						if filename2.endswith('.csv'):
							print filename + '/' + filename2

							gesture = self.load_file(file_or_directory + '/' + filename + '/' + filename2)

							if gesture != None:
								all_gestures.append(gesture)

		return all_gestures


	def load_file(self, filename):
		with open(filename, 'rb') as f:
			reader = csv.reader(f, delimiter=',')
			readlines = list(reader)
			data = readlines[1:]

			for rl in data:
		 		for i in range(0, 70):
		 			# print i
					rl[i] = float(rl[i])

				rl[70] = int(rl[70])
				rl[71] = int(rl[71])

				for i in range(74, len(rl)-3):
					rl[i] = float(rl[i])

				rl[-3] = int(rl[-3])
				rl[-2] = int(rl[-2])
				rl[-1] = int(rl[-1])

			# Sometimes the first line has a very high timestamp for some reason, we should probably ignore it just to be sure.
			while data[0][0] > 1000.0:
				del data[0]

			fname_parts = filename.split('/')

			# print readlines[0][84]

			gesture = Gesture()
			gesture.id = fname_parts[len(fname_parts)-2]
			gesture.filename = fname_parts[len(fname_parts)-1][:-4]
			gesture.timestamps = [row[0] for row in data]

			gesture.joints.hip_center = [row[64:67] for row in data]
			gesture.joints.spine = [row[61:64] for row in data]
			gesture.joints.shoulder_center = [row[67:70] for row in data]
			gesture.joints.head = [row[1:4] for row in data]
			gesture.joints.face_orientation = [FaceOrientation(row[-3], row[-2], row[-1]) for row in data]
			gesture.joints.neck = [row[4:7] for row in data]
			gesture.joints.shoulder_left = [row[16:19] for row in data]
			gesture.joints.elbow_left = [row[19:22] for row in data]
			gesture.joints.wrist_left = [row[22:25] for row in data]
			gesture.joints.hand_left = [row[52:55] for row in data]
			gesture.joints.hand_state_left = [HandState(row[71], row[73]) for row in data]
			gesture.joints.hand_tip_left = [row[58:61] for row in data]
			gesture.joints.thumb_left = [row[77:80] for row in data]
			gesture.joints.shoulder_right = [row[7:10] for row in data]
			gesture.joints.elbow_right = [row[10:13] for row in data]
			gesture.joints.wrist_right = [row[13:16] for row in data]
			gesture.joints.hand_right = [row[49:52] for row in data]
			gesture.joints.hand_state_right = [HandState(row[70], row[72]) for row in data]
			gesture.joints.hand_tip_right = [row[55:58] for row in data]
			gesture.joints.thumb_right = [row[74:77] for row in data]
			gesture.joints.hip_left = [row[34:37] for row in data]
			gesture.joints.knee_left = [row[37:40] for row in data]
			gesture.joints.ankle_left = [row[40:43] for row in data]
			gesture.joints.foot_left = [row[46:49] for row in data]
			gesture.joints.hip_right = [row[25:28] for row in data]
			gesture.joints.knee_right = [row[28:31] for row in data]
			gesture.joints.ankle_right = [row[31:34] for row in data]
			gesture.joints.foot_right = [row[43:46] for row in data]
			# print gesture.joints.hip_center

			return gesture