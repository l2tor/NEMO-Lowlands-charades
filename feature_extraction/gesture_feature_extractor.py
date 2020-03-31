import math
import numpy

# import matplotlib.pyplot as plt

class GestureFeatureExtractor():
	def smooth(self, y, box_pts):
	    box = numpy.ones(box_pts)/box_pts
	    y_smooth = numpy.convolve(y, box, mode='same')
	    return y_smooth

	def get_derivative(self, timestamps, data):
	    deriv = list()

	    data = zip(*data)

	    for i in range(1, len(data)):
	        deriv.append(numpy.divide(numpy.subtract(data[i], data[i-1]), (timestamps[i] - timestamps[i-1])))

	    deriv.append([0,0,0])

	    return zip(*deriv)

	# Position of joint (main_joint) relative to other joint (reference joint)
	def get_quadrant(self, main_joint, reference_joint, timestamp_index):
	    if main_joint[0][timestamp_index] <= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] >= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] <= reference_joint[2][timestamp_index]:
	        return "1"
	    elif main_joint[0][timestamp_index] >= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] >= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] <= reference_joint[2][timestamp_index]:
	        return "2"
	    elif main_joint[0][timestamp_index] <= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] <= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] <= reference_joint[2][timestamp_index]:
	        return "3"
	    elif main_joint[0][timestamp_index] >= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] <= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] <= reference_joint[2][timestamp_index]:
	        return "4"
	    elif main_joint[0][timestamp_index] <= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] >= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] >= reference_joint[2][timestamp_index]:
	        return "5"
	    elif main_joint[0][timestamp_index] >= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] >= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] >= reference_joint[2][timestamp_index]:
	        return "6"
	    elif main_joint[0][timestamp_index] <= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] <= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] >= reference_joint[2][timestamp_index]:
	        return "7"
	    elif main_joint[0][timestamp_index] >= reference_joint[0][timestamp_index] and main_joint[1][timestamp_index] <= reference_joint[1][timestamp_index] and main_joint[2][timestamp_index] >= reference_joint[2][timestamp_index]:
	        return "8"
	    else:
	        return "*"

	def _get_features_for_joint(self, main_joint, reference_joint, timestamps):
		# plt.plot(timestamps, main_joint[0])

		# Smoothing
		for i in range(0, 3):
			main_joint[i] = self.smooth(main_joint[i], 10)

		# plt.plot(timestamps, main_joint[0])

		# First derivative
		deriv1 = self.get_derivative(timestamps, main_joint)
		# print str(len(deriv1[0])) + "hasdjh"

		# Also smooth the derivative
		for i in range(0, 3):
			deriv1[i] = self.smooth(deriv1[i], 10)

		# plt.plot(timestamps, deriv1[0])

		# Second derivative
		deriv2 = self.get_derivative(timestamps, deriv1)

		# plt.plot(timestamps, deriv2[0])

		# Also smooth the second derivative
		for i in range(0, 3):
			deriv2[i] = self.smooth(deriv2[i], 10)


		# Find the peaks of the gesture trajectory (in X, Y and Z directions)
		peaks = [list(), list(), list()]

		for i in range(0, 3):
			peaks[i] = list()

			for t in range(2, len(timestamps)-1):
				if ((deriv1[i][t-1] <= 0 and deriv1[i][t] >= 0) or (deriv1[i][t-1] >= 0 and deriv1[i][t] <= 0)):
					peaks[i].append(t)

		# Find the inflection points (where the second derivative crosses 0)
		# Then find the nearest peak as well as the sign of the second derivative (shape of the curve after the inflection point) and store it
		found_points = [list(), list(), list()]
		signs = [list(), list(), list()]
		thresholds = [list(), list(), list()]

		# Temporary only for visualisation
		inflection_points = [list(), list(), list()]

		for i in range(0, 3):
			thresholds[i] = max(0.01, math.fabs(max(main_joint[i][4:len(main_joint[i])-4]) - min(main_joint[i][4:len(main_joint[i])-4])) / 5)

			# There needs to be a minimal displacement over the course of the joint's trajectory (in the X/Y/Z direction) larger than 20cm for it to be considered
			if math.fabs(max(main_joint[i][4:len(main_joint[i])-4]) - min(main_joint[i][4:len(main_joint[i])-4])) > 0.2:

				for t in range(5, len(timestamps)-5):
					if ((deriv2[i][t-1] <= 0 and deriv2[i][t] >= 0) or (deriv2[i][t-1] >= 0 and deriv2[i][t] <= 0)):
						inflection_points[i].append(t)
						peak_found = None
						closest_dist_to_peak = float('inf')
						prev_t = -1

						for j in range(1, len(peaks[i])):
							if peaks[i][j-1] > t and math.fabs(peaks[i][j] - t) > math.fabs(peaks[i][j-1] - t):
								peak_found = peaks[i][j-1]
								break

						if peak_found == None:
							peak_found = peaks[i][len(peaks[i])-1]

						# Check the type of inflection point
						if math.fabs(main_joint[i][peak_found] - main_joint[i][t]) > thresholds[i]:
							sign = ''
							if math.fabs(deriv2[i][t]) < .001:
								sign = '0'
							elif deriv2[i][t] > 0:
								sign = '+'
							else:
								sign = '-'

							if peak_found in found_points[i]:
								if math.fabs(t - peak_found) < closest_dist_to_peak:
									signs[i][found_points[i].index(peak_found)] = sign
									closest_dist_to_peak = math.fabs(t - peak_found)
							else:
								found_points[i].append(peak_found)
								signs[i].append(sign)


		# plt.plot([timestamps[i] for i in inflection_points[0]], [main_joint[0][i] for i in inflection_points[0]], 'go')
		# plt.plot([timestamps[i] for i in found_points[0]], [main_joint[0][i] for i in found_points[0]], 'ro')
		# print found_points
		# plt.show()

		return [found_points, signs]

	def get_features_for_joint_as_string(self, main_joint, reference_joint, timestamps):
		res = ""
		features = self._get_features_for_joint(main_joint, reference_joint, timestamps)

		for i in range(0, len(features[0])):
			for j in range(0, len(features[0][i])):
				res += self.get_quadrant(main_joint, reference_joint, features[0][i][j]) + features[1][i][j]

			if i < len(features[0])-1:
				res += ";"

		return res

	def get_hand_open_percentage(self, left_states, right_states):
		return str(self._get_hand_open_percentage(left_states)) + ";" + str(self._get_hand_open_percentage(right_states))


	def _get_hand_open_percentage(self, states):
		num_open = 0.0
		num_closed = 0.0
		total = 0.0

		for s in states:
			if s.state == 0:
				num_closed += 1
				total += 1
			elif s.state == 1:
				num_open += 1
				total += 1

		if total == 0:
			return 0

		return int(num_open / total * 100.0)


	def get_gesture_features_as_string(self, gesture):
		timestamps = gesture.timestamps
		lh_joint = zip(*gesture.joints.hand_left)
		rh_joint = zip(*gesture.joints.hand_right)
		ls_joint = zip(*gesture.joints.shoulder_left)
		rs_joint = zip(*gesture.joints.shoulder_right)
		le_joint = zip(*gesture.joints.elbow_left)
		re_joint = zip(*gesture.joints.elbow_right)
		ch_joint = zip(*gesture.joints.hip_center)
		cs_joint = zip(*gesture.joints.shoulder_center)

		# return gesture.id + ';' + gesture.filename + ';' + self.get_features_for_joint_as_string(lh_joint, le_joint, timestamps) + ';' + self.get_features_for_joint_as_string(rh_joint, re_joint, timestamps) \
		# + ';' + self.get_features_for_joint_as_string(le_joint, ls_joint, timestamps) + ';' + self.get_features_for_joint_as_string(re_joint, rs_joint, timestamps) \
		# + ';' + self.get_features_for_joint_as_string(cs_joint, ch_joint, timestamps) + ';' + self.get_hand_open_percentage(gesture.joints.hand_state_left, gesture.joints.hand_state_right)

		return gesture.id + ';' + gesture.filename + ';' + self.get_features_for_joint_as_string(lh_joint, ls_joint, timestamps) + ';' + self.get_features_for_joint_as_string(rh_joint, rs_joint, timestamps) \
		+ ';' + self.get_features_for_joint_as_string(lh_joint, rh_joint, timestamps) \
		+ ';' + self.get_features_for_joint_as_string(cs_joint, ch_joint, timestamps) + ';' + self.get_hand_open_percentage(gesture.joints.hand_state_left, gesture.joints.hand_state_right)
