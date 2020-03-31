from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist
import numpy as np

from gesture_comparison.gesture_comparison import GestureComparison

# https://joernhees.de/blog/2015/08/26/scipy-hierarchical-clustering-and-dendrogram-tutorial/
class GestureClusters():

	def __init__(self, dataset = None):
		self.dataset = dataset

	def set_dataset(self, dataset):
		self.dataset = dataset

	def generate_clusters(self):
		if self.dataset != None:
			print self.dataset[0][0]
			# print self.dataset
			y = pdist(self.dataset, GestureComparison.compare_datapoints)
			z = linkage(y)

			# print z 

			scores = [row[2] for row in z]
			for i in range(0, len(z)):
				z[i][2] -= min(scores)

			# for i in range(0, len(self.dataset)):
			# 	print self.dataset[i][1]

			# c, coph_dists = cophenet(z, y)

			# plt.figure(figsize=(25, 10))
			# plt.title('Hierarchical Clustering Dendrogram')
			# plt.xlabel('sample index')
			# plt.ylabel('distance')
			# dendrogram(
			#     z,
			#     leaf_rotation=90.,  # rotates the x axis labels
			#     leaf_font_size=8.,  # font size for the x axis labels
			# )			


			clusters = fcluster(z, 300, criterion='distance')
			# if self.dataset[0][0] == "spoon":
			# 	fancy_dendrogram(
			# 	    z,
			# 	    truncate_mode='lastp',
			# 	    p=12,
			# 	    leaf_rotation=90.,
			# 	    leaf_font_size=12.,
			# 	    show_contracted=True,
			# 	    annotate_above=10,  # useful in small plots so annotations don't overlap,
			# 	    max_d=300
			# 	)			

			# 	plt.show()			

			return clusters

def fancy_dendrogram(*args, **kwargs):
    max_d = kwargs.pop('max_d', None)
    if max_d and 'color_threshold' not in kwargs:
        kwargs['color_threshold'] = max_d
    annotate_above = kwargs.pop('annotate_above', 0)

    ddata = dendrogram(*args, **kwargs)

    if not kwargs.get('no_plot', False):
        plt.title('Hierarchical Clustering Dendrogram (truncated)')
        plt.xlabel('sample index or (cluster size)')
        plt.ylabel('distance')
        for i, d, c in zip(ddata['icoord'], ddata['dcoord'], ddata['color_list']):
            x = 0.5 * sum(i[1:3])
            y = d[1]
            if y > annotate_above:
                plt.plot(x, y, 'o', c=c)
                plt.annotate("%.3g" % y, (x, y), xytext=(0, -5),
                             textcoords='offset points',
                             va='top', ha='center')
        if max_d:
            plt.axhline(y=max_d, c='k')
    return ddata			