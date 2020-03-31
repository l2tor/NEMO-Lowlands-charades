import os
import nwalign

class GestureComparison:

	@staticmethod
	def _flip_quadrants(quads):
		quads = list(quads)

		for i in range(0, len(quads)):
			if quads[i] == '1':
				quads[i] = '2'
			elif quads[i] == '2':
				quads[i] = '1'
			elif quads[i] == '3':
				quads[i] = '4'
			elif quads[i] == '4':
				quads[i] = '3'
			elif quads[i] == '5':
				quads[i] = '6'
			elif quads[i] == '6':
				quads[i] = '5'
			elif quads[i] == '7':
				quads[i] = '8'
			elif quads[i] == '8':
				quads[i] = '7'

		return "".join(quads)


	@staticmethod
	def compare_datapoints(p1, p2):
		gist_1 = p1[2:len(p1)-2]
		gist_2 = p2[2:len(p2)-2]
		gist_1_flipped = list(gist_1)

		# We also try the 'flipped' (mirrored) version of the gesture to allow comparison between left-handed and right-handed gestures
		# (although it's not super accurate).
		# Need to take into account not to flip spine (so we drop the last 3 parts)
		for i in range(0, (len(gist_1_flipped)-3) / 2):
			tmp = GestureComparison._flip_quadrants(gist_1_flipped[i])
			# print gist_1_flipped[i] + " --> " + tmp
			# print str(i) + "<->" + str(len(gist_1_flipped) / 2 + i - 3 + 1)
			gist_1_flipped[i] = GestureComparison._flip_quadrants(gist_1_flipped[len(gist_1_flipped) / 2 + i - 3 + 1])
			gist_1_flipped[len(gist_1_flipped) / 2 + i - 3 + 1] = tmp

		score = 0.0
		score_flipped = 0.0

		for i in range(0, len(gist_1)):
			if gist_1[i] != 0 and gist_2[i] != '':
				res = nwalign.global_align(gist_1[i], gist_2[i], matrix=os.path.dirname(os.path.realpath(__file__)) + '/alignment.matrix')
				this_score = nwalign.score_alignment(res[0], res[1], gap_open=0, gap_extend=-5, matrix=os.path.dirname(os.path.realpath(__file__)) + '/alignment.matrix')
				if i >= len(gist_1) - 3:
					this_score *= 2

				score += this_score

				res = nwalign.global_align(gist_1_flipped[i], gist_2[i], matrix=os.path.dirname(os.path.realpath(__file__)) + '/alignment.matrix')
				this_score_flipped = nwalign.score_alignment(res[0], res[1], gap_open=0, gap_extend=-5, matrix=os.path.dirname(os.path.realpath(__file__)) + '/alignment.matrix')

				if i >= len(gist_1) - 3:
					this_score_flipped *= 2

				score_flipped += this_score_flipped

		# print str(score_flipped) + " " + str(score)

		if score_flipped > score:
			score_flipped -= abs(int(p1[-2]) - int(p2[-1])) + abs(int(p1[-1]) - int(p2[-2]))
			# print "using flipped! " + p1[1] + " " + p2[1] + " " + str(score_flipped) + " > " + str(score)
			return -score_flipped
		else:
			score -= abs(int(p1[-2]) - int(p2[-2])) + abs(int(p1[-1]) - int(p2[-1]))
			return -score

		# print data_point[0] + data_point[1] + ' <> ' + dataset_item[0] + ': ' + dataset_item[1] + ' -- ' + str(score)
