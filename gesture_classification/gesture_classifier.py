import math
import operator

from gesture_comparison.gesture_comparison import GestureComparison

class GestureClassifier():
	def __init__(self, dataset = list()):
		self.dataset = dataset

	def set_dataset(self, dataset):
		self.dataset = dataset

	# Data point is now input as a string with certain structure, maybe consider to turn this into class?
	def classify(self, data_point, prior_not_label = None):
		# We use k nearest neighbors to determine the closest match
		# The number of neighbors 'k' is set to be the square root of half of the number of samples in our dataset, with a maximum of 8.
		k = min(8, int(round(math.sqrt(len(self.dataset.data)) / 2)))
		distances = list()

		for item in self.dataset.data:
			# Invert to find distance instead of similarity
			score = -1 * GestureComparison.compare_datapoints(data_point, item)
			if prior_not_label == None or item[0] != prior_not_label:
				distances.append([item[0], item[1], score])

		distances.sort(key=operator.itemgetter(2), reverse=True)

		total = 0
		minimum = 0

		neighbors = list()
		for i in range(0, k):
			neighbors.append(distances[i])
			if distances[i][2] < minimum:
				minimum = distances[i][2]

		for n in range(0, len(neighbors)):
			neighbors[n][2] -= minimum
			total += neighbors[n][2]

		while True:
			#total = 1 / float(sum(range(1,k+1)))

			classvotes = dict()
			# We use weighted voting now, so depending on how big the distance is it gets a certain amount of weight
			# You can also consider just adding 1 vote for each hit
			for n in range(0, len(neighbors)):
				if neighbors[n][0] in classvotes:
					classvotes[neighbors[n][0]] += neighbors[n][2] / total#1
				else:
					classvotes[neighbors[n][0]] = neighbors[n][2] / total #1

			sortedvotes = sorted(classvotes.iteritems(), key=operator.itemgetter(1), reverse=True)
			print sortedvotes

			if len(sortedvotes) == 1 or sortedvotes[0][1] > sortedvotes[1][1]:
				break
			else:
				neighbors = neighbors[0:len(neighbors)-1]


		print data_point[0] + ' ' + data_point[1] + ' -> ' + sortedvotes[0][0]
		# return sortedvotes[0][0]
		return [sortedvotes, neighbors]
