import csv
import time
import os

class DataManager():

	def __init__(self, to_load = None):
		self.data = list()

		if to_load != None and os.path.isfile(to_load):
			self.load(to_load)

	def load(self, filename):
		print "Load dataset! " + filename
		file = open(filename, 'r')
		self.data = file.readlines()
		file.close()

		for i in range(0, len(self.data)):
			self.data[i] = self.data[i].split(';')
			self.data[i][-1] = self.data[i][-1].replace('\n', '')

	def save(self, filename):
		file = open(filename, 'w')
		save_str = self.data[:]

		for i in range(0, len(save_str)):
			save_str[i] = ';'.join(save_str[i])

		out_str = '\n'.join(save_str)
		file.write(out_str)
		file.close()

	def append(self, string_or_list):
		item = string_or_list
		if not isinstance(string_or_list, list):
			item = string_or_list.split(';')

		# Stuff is slowing down by a lot when the data goes above about 3500 (100 copies of each gesture) so we start dropping lines if that happens
		datalen = len(self.data)
		if datalen >= 3500:
			extra_data = DataManager('data/gists_overflow.csv')
			# self.save("data/gists_" + str(time.time()) + ".csv")

			indices_toremove = list()
			num_to_remove = datalen-3499
			num_removed = 0

			for d in range(0, datalen):
				if self.data[d][0] == item[0]:
					extra_data.append(self.data[d])
					indices_toremove.append(d)
					num_removed += 1

					if num_removed == num_to_remove:
						break

			print indices_toremove
			extra_data.save('data/gists_overflow.csv')
			
			for i in sorted(indices_toremove, reverse=True):
			    del self.data[i]			

		self.data.append(item)


