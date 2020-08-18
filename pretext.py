#---------------dimension_importances session------------------------------#
class pretextprocessing:
	import pythainlp as pynlp
	from pythainlp import tokenize

	def __init__(self,keep_whitespace = False):
		self.keep_whitespace = keep_whitespace

		
		

	def stopword_remove(self,text):
		text_segment_list = self.tokenize.word_tokenize(text, engine="deepcut")
		list_of_stopword=self.pynlp.corpus.common.thai_stopwords()
		list_of_stopword = list(list_of_stopword)
		aftertext=""
		for data in list_of_stopword:
			while data in text_segment_list:
				text_segment_list.remove(data)
		for data in text_segment_list:
			aftertext = aftertext+data
		return aftertext

def todimesion_Imp(List_Input):
	import numpy as np
	list_index = readindexfile()
	newlist1=[]
	newlist2=[]
	for sam in List_Input:
		for index in list_index:
			newlist1.append(sam[index])
		newlist2.append(newlist1)
		newlist1=[]
	return np.array(newlist2)
#---------------dimension_importances session------------------------------#


def readindexfile():
	f = open("index.txt","r")
	text = f.read().split(",")
	#text.pop()
	indexlist = list(map(int,text))
	f.close()
	return indexlist

def classifiedToMail(ndarray,dic_mail):
	list_of_class = ndarray.tolist()
	return dic_mail[list_of_class[0]],list_of_class[0]
