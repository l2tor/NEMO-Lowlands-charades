import math
from dataset_management.gesture_classes import Pose

# Code based on:
# Suay, H. B., & Chernova, S. (2011, March). Humanoid robot control using depth camera. In Proceedings of the 6th international conference on Human-robot interaction (pp. 401-402). ACM.

class JointPositionToNAO():
	def __init__(self):
		self.prev_hand_l = 0.0
		self.prev_hand_r = 0.0

	def get_nao_joints(self, gesture):
		robot_joint_ids = list()
		robot_joint_pos = list()

		# print len(gesture.timestamps)
		# prev_hand_l_open = 0
		# prev_hand_r_open = 0

		for i in range(0, len(gesture.timestamps)):
			p = Pose.from_gesture(gesture, i)
			r = self.get_nao_joints_for_pose(gesture, i)

			if i == 0:
				robot_joint_ids = r[0]

			robot_joint_pos.append(r[1])

		return [robot_joint_ids, robot_joint_pos]


	def get_nao_joints_for_timestamp(self, gesture, index):
		pose = Pose.from_gesture(gesture, index)

		pose_ids = []
		pose_values = []

		if abs(pose.joints.elbow_right[2] - pose.joints.hip_right[2]) < .1 and abs(pose.joints.hand_right[0] - pose.joints.hip_right[0]) < .1:
			pose.joints.elbow_right[2] += 0.25
			pose.joints.hand_right[2] += 0.25

		if abs(pose.joints.elbow_left[2] - pose.joints.hip_left[2]) < .1 and abs(pose.joints.hand_left[0] - pose.joints.hip_left[0]) < .1:
			pose.joints.elbow_left[2] += 0.25
			pose.joints.hand_left[2] += 0.25


    	# Left shoulder pitch: XN_SKEL_LEFT_HIP, XN_SKEL_LEFT_SHOULDER, XN_SKEL_LEFT_ELBOW
		lsap = self.get_limb_angle(pose.joints.hip_left, pose.joints.shoulder_left, pose.joints.elbow_left) * math.pi / 180
		lsap = lsap - 1.5708
		pose_ids.append('LShoulderPitch')
		if lsap < -2.0857:
			lsap = -2.0857
		elif lsap > 2.0857:
			lsap = 2.0857

		pose_values.append(lsap)

		# Left shoulder roll: XN_SKEL_LEFT_HIP, XN_SKEL_RIGHT_HIP, XN_SKEL_LEFT_SHOULDER, XN_SKEL_LEFT_ELBOW
		lsar = self.get_angle_between_limbs(pose.joints.hip_left, pose.joints.hip_right, pose.joints.shoulder_left, pose.joints.elbow_left) * math.pi / 180
		lsar = lsar - 1.5708 #1.57 # 1.63?
		pose_ids.append('LShoulderRoll')
		if lsar < -.3142:
			lsar = .3142
		elif lsar > 1.3265:
			lsar = 1.3265

		pose_values.append(lsar)

    	# Left elbow roll: XN_SKEL_LEFT_SHOULDER, XN_SKEL_LEFT_ELBOW, XN_SKEL_LEFT_HAND
		lear = self.get_limb_angle(pose.joints.shoulder_left, pose.joints.elbow_left, pose.joints.hand_left) * math.pi / 180
		lear = -1 * lear
		pose_ids.append('LElbowRoll')
		if lear < -1.5446:
			lear = -1.5446
		elif lear > -.0349:
			lear = -.0349

		pose_values.append(lear)

    	# Left elbow yaw: XN_SKEL_LEFT_SHOULDER, XN_SKEL_LEFT_HIP, XN_SKEL_LEFT_ELBOW, XN_SKEL_LEFT_HAND
		leay = self.get_angle_between_limbs(pose.joints.shoulder_left, pose.joints.hip_left, pose.joints.elbow_left, pose.joints.hand_left) * math.pi / 180
		# leay = leay - 1.5708 #1.57 - leay
		if abs(leay) < 0.4:
			leay = 0
		else:
			leay = 1.5708 - leay

		pose_ids.append('LElbowYaw')
		if leay < -2.0857:
			leay = -2.0857
		elif leay > 2.0857:
			leay = 2.0857
		pose_values.append(leay)

		# Left wrist yaw (experimental): XN_LEFT_ELBOW, XN_SKEL_LEFT_HIP, XN_SKEL_LEFT_HAND, XN_SKEL_LEFT_HANDTIP
		# lwy = self.get_limb_angle(pose.joints.hand_left, pose.joints.hand_tip_left, pose.joints.thumb_left) * math.pi / 180
		lwy = self.get_angle_between_limbs(pose.joints.hip_left, pose.joints.hip_right, pose.joints.wrist_left, pose.joints.thumb_left) * math.pi / 180
		# lwy = self.get_angle_between_limbs(pose.joints.elbow_left, pose.joints.hip_left, pose.joints.hand_left, pose.joints.thumb_left) * math.pi / 180
		# lwy = 1.57 - lwy
		lwy = lwy - 1.5708
		# lwy = 1.5708 - lwy #- 1.57
		# lwy = -1 * lwy
		# print lwy
		if lwy < -1.8238:
			lwy = -1.8238
		elif lwy > 1.8238:
			lwy = 1.8238
		pose_ids.append('LWristYaw')
		pose_values.append(lwy)

		# Right shoulder pitch: XN_SKEL_RIGHT_HIP, XN_SKEL_RIGHT_SHOULDER, XN_SKEL_RIGHT_ELBOW
		rsap = self.get_limb_angle(pose.joints.hip_right, pose.joints.shoulder_right, pose.joints.elbow_right) * math.pi / 180
		rsap = rsap - 1.5708
		pose_ids.append('RShoulderPitch')
		if rsap < -2.0857:
			rsap = -2.0857
		elif rsap > 2.0857:
			rsap = 2.0857

		# print rsap

		# rsap -= 0.5
		pose_values.append(rsap)

		# Right shoulder roll: XN_SKEL_RIGHT_HIP, XN_SKEL_LEFT_HIP, XN_SKEL_RIGHT_SHOULDER, XN_SKEL_RIGHT_ELBOW
		rsar = self.get_angle_between_limbs(pose.joints.hip_right, pose.joints.hip_left, pose.joints.shoulder_right, pose.joints.elbow_right) * math.pi / 180
		rsar = 1.5708 - rsar
		pose_ids.append('RShoulderRoll')
		if rsar < -1.3265:
			rsar = -1.3265
		elif rsar > 0.3142:
			rsar = 0.3142
		pose_values.append(rsar)


		# Right elbow roll: XN_SKEL_RIGHT_SHOULDER, XN_SKEL_RIGHT_ELBOW, XN_SKEL_RIGHT_HAND
		rear = self.get_limb_angle(pose.joints.shoulder_right, pose.joints.elbow_right, pose.joints.hand_right) * math.pi / 180
		pose_ids.append('RElbowRoll')
		if rear < .0349:
			rear = .0349
		elif rear > 1.5446:
			rear = 1.5446
		pose_values.append(rear)

		# Right elbow yaw: XN_SKEL_RIGHT_SHOULDER, XN_SKEL_RIGHT_HIP, XN_SKEL_RIGHT_ELBOW, XN_SKEL_RIGHT_HAND
		reay = self.get_angle_between_limbs(pose.joints.shoulder_right, pose.joints.hip_right, pose.joints.elbow_right, pose.joints.hand_right) * math.pi / 180
		if abs(reay) < 0.4:
			reay = 0
		else:
			reay = reay - 1.5708
		# reay = 1.5708 - reay
		# print reay
		pose_ids.append('RElbowYaw')
		if reay < -2.0857:
			reay = -2.0857
		elif reay > 2.0857:
			reay = 2.0857
		pose_values.append(reay)

		# Left wrist yaw (experimental): XN_LEFT_ELBOW, XN_SKEL_LEFT_HIP, XN_SKEL_LEFT_HAND, XN_SKEL_LEFT_HANDTIP
		# rwy = self.get_angle_between_limbs(pose.joints.elbow_right, pose.joints.hip_right, pose.joints.hand_right, pose.joints.thumb_right) * math.pi / 180
		rwy = self.get_angle_between_limbs(pose.joints.hip_left, pose.joints.hip_right, pose.joints.wrist_right, pose.joints.thumb_right) * math.pi / 180

		# rwy = self.get_limb_angle(pose.joints.shoulder_right, pose.joints.wrist_right, pose.joints.hand_right) * math.pi / 180
		# rwy = 1.57 - rwy
		# print rwy
		# print rwy
		# rwy = 1.5708 - rwy
		rwy = rwy - 1.5708
		# rwy = -1 * rwy

		if rwy < -1.8238:
			rwy = -1.8238
		elif rwy > 1.8238:
			rwy = 1.8238
		pose_ids.append('RWristYaw')
		pose_values.append(rwy)

		pose_ids.append('HeadPitch')
		hp = pose.joints.face_orientation.pitch * math.pi / 180
		if hp < -0.6720:
			hp = -0.6720
		elif hp > 0.5149:
			hp = 0.5149
		pose_values.append(hp)

		pose_ids.append('HeadYaw')
		hy = pose.joints.face_orientation.yaw * math.pi / 180
		if hy < -2.0857:
			hy = -2.0857
		elif hy > 2.0857:
			hy = 2.0857
		pose_values.append(hy)

		num_open_l = 0
		num_closed_l = 0
		num_open_r = 0
		num_closed_r = 0

		# print index

		for j in range(max(0, (index-2)), min(len(gesture.timestamps), (index+2))):
			if gesture.joints.hand_state_right[j].state == 0:
				num_closed_r += 1
			elif gesture.joints.hand_state_right[j].state == 1:
				num_open_r += 1
			if gesture.joints.hand_state_left[j].state == 0:
				num_closed_l += 1
			elif gesture.joints.hand_state_left[j].state == 1:
				num_open_l += 1

		pose_ids.append('LHand')
		if pose.joints.hand_left[1] < pose.joints.elbow_left[1]:
			pose_values.append(0.0)
		else:
			if num_closed_l > 1 and num_closed_l > num_open_l:
				pose_values.append(0.0)
				self.prev_hand_l = 0.0
			elif num_open_l > 1:
				pose_values.append(1.0)
				self.prev_hand_l = 1.0
			else:
				pose_values.append(self.prev_hand_l)

		pose_ids.append('RHand')
		if pose.joints.hand_right[1] < pose.joints.elbow_right[1]:
			pose_values.append(0.0)
		else:
			if num_closed_r > 1 and num_closed_r > num_open_r:
				pose_values.append(0.0)
				self.prev_hand_r = 0.0
			elif num_open_r > 1:
				pose_values.append(1.0)
				self.prev_hand_r = 1.0
			else:
				pose_values.append(self.prev_hand_r)

		return [pose_ids, pose_values]

    # Get and return the angle between two NOT JOINT limbs of the skeleton, e.g. angle between (hip to hip vector) ^ ( upper arm )
	def get_angle_between_limbs(self, joint1, joint2, joint3, joint4):
		v1 = [
			joint3[0] - joint4[0],
			joint3[1] - joint4[1],
			joint3[2] - joint4[2]
		]

		v2 = [
			joint1[0] - joint2[0],
			joint1[1] - joint2[1],
			joint1[2] - joint2[2]
		]

		v1_magnitude = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2])
		v2_magnitude = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2])

		if v1_magnitude != 0.0 and v2_magnitude != 0.0:
			v1[0] = v1[0] * (1.0 / v1_magnitude)
			v1[1] = v1[1] * (1.0 / v1_magnitude)
			v1[2] = v1[2] * (1.0 / v1_magnitude)

			v2[0] = v2[0] * (1.0 / v2_magnitude)
			v2[1] = v2[1] * (1.0 / v2_magnitude)
			v2[2] = v2[2] * (1.0 / v2_magnitude)

			theta = math.acos(v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2])
			angle_in_degrees = theta * 180 / math.pi

			return angle_in_degrees

		return None

	def get_limb_angle(self, joint1, joint2, joint3):
		v1 = [
			joint2[0] - joint3[0],
			joint2[1] - joint3[1],
			joint2[2] - joint3[2]
		]

		v2 = [
			joint1[0] - joint2[0],
			joint1[1] - joint2[1],
			joint1[2] - joint2[2]
		]

		v1_magnitude = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2])
		v2_magnitude = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2])

		if v1_magnitude != 0.0 and v2_magnitude != 0.0:
			v1[0] = v1[0] * (1.0 / v1_magnitude)
			v1[1] = v1[1] * (1.0 / v1_magnitude)
			v1[2] = v1[2] * (1.0 / v1_magnitude)

			v2[0] = v2[0] * (1.0 / v2_magnitude)
			v2[1] = v2[1] * (1.0 / v2_magnitude)
			v2[2] = v2[2] * (1.0 / v2_magnitude)

			theta = math.acos(v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2])
			angle_in_degrees = theta * 180 / math.pi

			return angle_in_degrees

		return None
