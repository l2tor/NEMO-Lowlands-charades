class Gesture:
	def __init__(self):
		self.id = ''
		self.filename = ''
		self.timestamps = list()
		self.joints = JointCollection()


# @TODO: add hands and face from Kinect recording tool
class JointCollection:
	def __init__(self):
		self.hip_center = list()
		self.spine = list()
		self.shoulder_center = list()
		self.head = list()
		self.face_orientation = list()
		self.neck = list()
		self.shoulder_left = list()
		self.elbow_left = list()
		self.wrist_left = list()
		self.hand_left = list()
		self.hand_state_left = list()
		self.hand_tip_left = list()
		self.thumb_left = list()
		self.shoulder_right = list()
		self.elbow_right = list()
		self.wrist_right = list()
		self.hand_right = list()
		self.hand_state_right = list()
		self.hand_tip_right = list()
		self.thumb_right = list()
		self.hip_left = list()
		self.knee_left = list()
		self.ankle_left = list()
		self.foot_left = list()
		self.hip_right = list()
		self.knee_right = list()
		self.ankle_right = list()
		self.foot_right = list()

class Pose:
	def __init__(self):
		self.id = ''
		self.filename = ''
		self.timestamp = 0.0
		self.joints = SingleJointCollection()

	@staticmethod
	def from_gesture(gesture, index):
		p = Pose()
		p.id = gesture.id
		p.filename = gesture.filename
		p.timestamp = gesture.timestamps[index]
		p.joints.hip_center = gesture.joints.hip_center[index]
		p.joints.spine = gesture.joints.spine[index]
		p.joints.shoulder_center = gesture.joints.shoulder_center[index]
		p.joints.head = gesture.joints.head[index]
		if len(gesture.joints.face_orientation) > 0:
			p.joints.face_orientation = gesture.joints.face_orientation[index]
		if len(gesture.joints.neck) > 0:
			p.joints.neck = gesture.joints.neck[index]
		p.joints.shoulder_left = gesture.joints.shoulder_left[index]
		p.joints.elbow_left = gesture.joints.elbow_left[index]
		p.joints.wrist_left = gesture.joints.wrist_left[index]
		p.joints.hand_left = gesture.joints.hand_left[index]
		if len(gesture.joints.hand_state_left) > 0:
			p.joints.hand_state_left = gesture.joints.hand_state_left[index]
		if len(gesture.joints.hand_tip_left) > 0:
			p.joints.hand_tip_left = gesture.joints.hand_tip_left[index]
		if len(gesture.joints.thumb_left) > 0:
			p.joints.thumb_left = gesture.joints.thumb_left[index]
		p.joints.shoulder_right = gesture.joints.shoulder_right[index]
		p.joints.elbow_right = gesture.joints.elbow_right[index]
		p.joints.wrist_right = gesture.joints.wrist_right[index]
		p.joints.hand_right = gesture.joints.hand_right[index]
		if len(gesture.joints.hand_state_right) > 0:
			p.joints.hand_state_right = gesture.joints.hand_state_right[index]
		if len(gesture.joints.hand_tip_right) > 0:
			p.joints.hand_tip_right = gesture.joints.hand_tip_right[index]
		if len(gesture.joints.thumb_right) > 0:
			p.joints.thumb_right = gesture.joints.thumb_right[index]
		p.joints.hip_left = gesture.joints.hip_left[index]
		p.joints.knee_left = gesture.joints.knee_left[index]
		p.joints.ankle_left = gesture.joints.ankle_left[index]
		p.joints.foot_left = gesture.joints.foot_left[index]
		p.joints.hip_right = gesture.joints.hip_right[index]
		p.joints.knee_right = gesture.joints.knee_right[index]
		p.joints.ankle_right = gesture.joints.ankle_right[index]
		p.joints.foot_right = gesture.joints.foot_right[index]

		return p

# @TODO: add hands and face from Kinect recording tool
class SingleJointCollection:
	def __init__(self):
		self.hip_center = 0.0
		self.spine = 0.0
		self.shoulder_center = 0.0
		self.head = 0.0
		self.face_orientation = FaceOrientation(0, 0, 0)
		self.neck = 0.0
		self.shoulder_left = 0.0
		self.elbow_left = 0.0
		self.wrist_left = 0.0
		self.hand_left = 0.0
		self.hand_state_left = HandState(-1, "Low")
		self.hand_tip_left = 0.0
		self.thumb_left = 0.0
		self.shoulder_right = 0.0
		self.elbow_right = 0.0
		self.wrist_right = 0.0
		self.hand_right = 0.0
		self.hand_state_right = HandState(-1, "Low")
		self.hand_tip_right = 0.0
		self.thumb_right = 0.0
		self.hip_left = 0.0
		self.knee_left = 0.0
		self.ankle_left = 0.0
		self.foot_left = 0.0
		self.hip_right = 0.0
		self.knee_right = 0.0
		self.ankle_right = 0.0
		self.foot_right = 0.0

class HandState:
	def __init__(self, state, confidence):
		self.state = state
		self.confidence = confidence

class FaceOrientation:
	def __init__(self, pitch, yaw, roll):
		self.pitch = pitch
		self.yaw = yaw
		self.roll = roll