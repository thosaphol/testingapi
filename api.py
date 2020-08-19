
# using flask_
from flask import Flask, jsonify, request 
from flask_restful import Resource, Api
import os

#from pretextprocessing import pretextprocessing
import pretext 
#from premodel import modeltrainning
import joblib
knn = joblib.load('knn.pkl')
from sklearn.decomposition import PCA
pca = joblib.load('pca.pkl')
from sklearn.preprocessing import StandardScaler
scaler = joblib.load('scaler.pkl')

import tensorflow_hub as hub
import numpy as np
import tensorflow_text

pre =pretext.pretextprocessing()
embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3")


# creating the flask app 
app = Flask(__name__) 
# creating an API object 
api = Api(app) 
#app.config['PROPAGATE_EXCEPTIONS'] = True

# making a class for a particular resource 
# the get, post methods correspond to get and post requests 
# they are automatically mapped by flask_restful. 
# other methods include put, delete, etc.



class Classified(Resource): 

	# corresponds to the GET request. 
	# this function is called whenever there 
	# is a GET request for this resource 
	def get(self): 
		
		return jsonify({'message': 'hello world'}) 

	# Corresponds to POST request 
	def post(self): 
		
		data = request.get_json()	 # status code 
		try:
			text=pre.stopword_remove(data['detail'])
			text_list = [text]

		
		#text_vec= pretext.todimesion_Imp(np.array(text_vec).tolist())
#		return jsonify({'data': str(text_vec)})


			text_vec = embed(text_list)
			scaler.fit(text_vec)
			X_scaled=scaler.transform(text_vec)
			principalComponents = pca.transform(X_scaled)

			result=knn.predict(principalComponents)
			mail_department = {'0':'publicrelations.rmutt@gmail.com',
							'1':'buildingstation.rmutt@gmail.com',
							'2':'asset.rmutt@gmail.com',
							'3':'informationtechnology.rmutt@gmail.com'}
			text = mail_department[str(result)]
			return jsonify({'data': text})
		except:
			text ='ไม่สามารถส่งคำร้องได้ เนื่องจากระบบรับคำร้องขัดข้อง กรุณาลองอีกครั้ง'
			
			return jsonify({'data':'error'})





# another resource to calculate the square of a number 


# adding the defined resources along with their corresponding urls 
api.add_resource(Classified, '/') 

# driver function 


if __name__ == '__main__': 
	app.run(debug=True)
	#app.run(debug = True,host='0.0.0.0',port=5000) 
	