import networkx as nx
import numpy as np

from nltk.tokenize.punkt import PunktSentenceTokenizer
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer


class SummaryUsingGooglePageRank():
	'''Summarization algo based on page ranking algorithm
	used by google'''

	def __init__(self, input_file, output_file):
		self.input_file = input_file
		self.output_file = output_file

	def textrank(self, document):
	    sentence_tokenizer = PunktSentenceTokenizer()
	    sentences = sentence_tokenizer.tokenize(document)

	    bow_matrix = CountVectorizer().fit_transform(sentences)
	    normalized = TfidfTransformer().fit_transform(bow_matrix)

	    similarity_graph = normalized * normalized.T

	    nx_graph = nx.from_scipy_sparse_matrix(similarity_graph)
	    scores = nx.pagerank(nx_graph)
	    return sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True)

	def summarize(self):
		'''Main function which deals with summarizing
		the text'''

		f = open(self.input_file, "r")
		document = f.read()
		f.close()

		f = open(self.output_file, "wb")

		ranked = self.textrank(document)

		summary = ""
		for i in range(10):
			summary += ranked[i][1]

		print summary
		f.write(summary)
