
# using flask_
from flask import Flask, jsonify, request 
from flask_restful import Resource, Api
import os
print()
#from pretextprocessing import pretextprocessing
import pretext 
#from premodel import modeltrainning
from sklearn.externals import joblib
knn = joblib.load('/home/thanaphat_phetkrow/API/knn.pkl')
from sklearn.decomposition import PCA
pca = joblib.load('/home/thanaphat_phetkrow/API/pca.pkl')
from sklearn.preprocessing import StandardScaler
scaler = joblib.load('/home/thanaphat_phetkrow/API/scaler.pkl')

import tensorflow_hub as hub
import numpy as np
import tensorflow_text

pre =pretext.pretextprocessing()
embed = hub.load("/home/thanaphat_phetkrow/API/model3")

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
cred = credentials.Certificate('/home/thanaphat_phetkrow/API/serviceAccountKey.json')
firebase_admin.initialize_app(cred,{
	'storageBucket': 'fir-c1ec0.appspot.com'
})
db = firestore.client()
bucket = storage.bucket()
batch = db.batch()
increment = firestore.Increment(1)


from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
line_bot_api = LineBotApi('D0swFcBPAYfgPimK1O9LuyDhDGUUTkMAAPEgpCGB3gdS89Nl4tJpq8FfaVJFpf4dftTky5mCm5LYkbwSquGKZLWr3ye417GRKFvrXYgQPUWHAiocqCPcKT1i+hIRfHF73FxmmWWGyQpUt+YtQl+fAQdB04t89/1O/w1cDnyilFU=')

def getImage_todic(messageIDList):
	
	disImage={}
	
	for index in range(len(messageIDList)):
		t=b''
		message_content = line_bot_api.get_message_content(str(messageIDList[index]))
		for chunk in message_content.iter_content():
			t=t+chunk
		disImage[str(index+1)] = t

	return disImage

import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders
def sent_email(Topic,PetitonID,Detail,dicImage,receiver_email):
	fromaddr = "petition.rmutt@gmail.com"
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = receiver_email
	msg['Subject'] = "Topic : "+Topic + "PetitonID : "+PetitonID
	body = "Topic : "+Topic +"\n\n"+"Detail : "+Detail
	msg.attach(MIMEText(body, 'plain'))
	for filename,y in dicImage.items():
		p = MIMEBase('application', 'octet-stream')
		p.set_payload(y)
		encoders.encode_base64(p)
		p.add_header('Content-Disposition', "attachment; filename= %s" % filename+".jpg")
		msg.attach(p)

	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, "petitionrmutt123")
	text = msg.as_string()
	s.sendmail(fromaddr, receiver_email, text)
	s.quit()
	

from datetime import datetime,timedelta



def save_petition(data_json,num_of_department):
	#--------------------object data----------------------#
	#datetimeObj=data_json['datetime']
	messageObj = data_json['messageObj']
	location = data_json['location']
	#--------------------object data----------------------#

	doc_result=db.collection('User').where('userID_from_line','==',data_json['userid']).stream()
	is_std = True;
	for sub_doc in doc_result :
		is_std = False

	if is_std :
		doc_query_result=db.collection('Student').where('userID_from_line','==',data_json['userid']).stream()
		doc = list(doc_query_result)[0]
		#doc = doc.to_dict()
		doc_ref = db.collection('Student').document(doc.id)
		
		doc = doc_ref.get()
		data_dict=doc.to_dict()
		std_id = data_dict['User_ID']
		num_of_petition = data_dict['nPetition']

		pet_id = std_id+str(num_of_petition)

		image_dict = getImage_todic(messageObj)
		path = std_id+'/'+pet_id+'/'
		imgPath_dict = {}

		for x,y in image_dict.items():
			imgPath_dict[x]=path+x+'.jpg'
			blob = bucket.blob(path+x+'.jpg')
			blob.upload_from_string(y,content_type='image/jpeg')
	
		userid = data_json['userid']

		data_pet={ 'ID':pet_id,
			'Detail':data_json['detail'],
			'Topic':data_json['topic'],
			'User_ID':std_id,
			'userType':True,
			'Date_time':firestore.SERVER_TIMESTAMP,
			'location':firestore.GeoPoint(location['latitude'],location['longitude']),
			'Image':imgPath_dict,
			'Department':num_of_department,
			'currentStatus':0}

		doc_pet = db.collection('Petition').document(pet_id)
		doc_std = db.collection('Student').document(doc.id)
		batch.update(doc_std,{'nPetition':increment})
		batch.set(doc_pet,data_pet)
		batch.commit()

		doc_to_listenning = db.collection('Petition').document(pet_id)
		doc_listenner_dict[pet_id] = doc_to_listenning.on_snapshot(on_snapshot)

	else:
		doc_ref = db.collection('User').document(data_json['userid'])
		doc = doc_ref.get()
		data_dict=doc.to_dict()
		use_id = data_dict['User_ID']
		num_of_petition = data_dict['nPetition']

		userid = data_json['userid']
		pet_id = use_id+str(num_of_petition)

		image_dict = getImage_todic(messageObj)
		path = use_id+'/'+pet_id+'/'
		imgPath_dict = {}

		for x,y in image_dict.items():
			imgPath_dict[x]=path+x+'.jpg'
			blob = bucket.blob(path+x+'.jpg')
			blob.upload_from_string(y,content_type='image/jpeg')

		data_pet={ 'ID':pet_id,
			'Detail':data_json['detail'],
			'Topic':data_json['topic'],
			'User_ID':use_id,
			'userType':False,
			'Date_time':firestore.SERVER_TIMESTAMP,
			'location':firestore.GeoPoint(location['latitude'],location['longitude']),
			'Image':imgPath_dict,
			'Department':num_of_department,
			'currentStatus':0}

		doc_pet = db.collection('Petition').document(pet_id)
		doc_use = db.collection('User').document(userid)
		batch.update(doc_use,{'nPetition':increment})
		batch.set(doc_pet,data_pet)
		batch.commit()



		doc_to_listenning = db.collection('Petition').document(pet_id)
		doc_listenner_dict[pet_id] = doc_to_listenning.on_snapshot(on_snapshot)
	#----------------------gen pet id--------------------#
	
	return pet_id

doc_listenner_dict = {}

def on_snapshot(col_snapshot, changes, read_time):
	dict_num_to_month ={1:'มกราคม',2:'กุมภาพันธ์',3:'มีนาคม',4:'เมษายน',5:'พฤษภาคม',6:'มิถุนายน',
				7:'กรกฎาคม',8:'สิงหาคม',9:'กันยายน',10:'ตุลาคม',11:'พฤศจิกายน',12:'ธันวาคม'}
	for change in changes:
		if change.type.name == 'MODIFIED':
			data_dict = change.document.to_dict()
						
			because = ''
			userid=''

			if data_dict['currentStatus']==3:

				usetype = data_dict['userType']

				use_ID = data_dict['User_ID']
				docs_std=''
				if usetype :
					docs_std = db.collection('Student').where('User_ID','==',use_ID).stream()
				else:
					docs_std = db.collection('User').where('User_ID','==',use_ID).stream()
				
				
				petID = data_dict['ID']
				docs_hist_app = db.collection('History_Approve').where('CaseStatus','==',3).where('petition_ID','==',petID).stream()
				for docHis in docs_hist_app :
					because = docHis.to_dict()['detail_of_approve']

				for docStd in docs_std:
					userid = docStd.to_dict()['userID_from_line']
				send_date = data_dict['Date_time']+timedelta(hours=7)
				
				text = 'คำร้อง: '+data_dict['Topic']+'\n'
				text = text+'ส่งคำร้องเมื่อ: '+str(send_date.day)+' '+dict_num_to_month[send_date.month]+' '+str(send_date.year+543)+'\n'
				
				str_hour=''
				str_min=''
				if send_date.hour<10:
					str_hour='0'+str(send_date.hour)
				else:
					str_hour=str(send_date.hour)
				if send_date.minute<10:
					str_min = '0'+str(send_date.minute)
				else:
					str_min = str(send_date.minute)
				text = text+'เวลา: '+str_hour+':'+str_min+'\n'
				text = text+'ได้ดำเนินการเสร็จสิ้นแล้ว ขอบคุณสำหรับการแจ้งคำร้องครั้งนี้'
				line_bot_api.push_message(userid, TextSendMessage(text=text))
				doc_listenner_dict[petID].unsubscribe()

			elif data_dict['currentStatus']==5:	

				usetype = data_dict['userType']

				use_ID = data_dict['User_ID']
				docs_std=''
				if usetype :
					docs_std = db.collection('Student').where('User_ID','==',use_ID).stream()
				else:
					docs_std = db.collection('User').where('User_ID','==',use_ID).stream()
				petID = data_dict['ID']
				docs_hist_app = db.collection('History_Approve').where('CaseStatus','==',5).where('petition_ID','==',petID).stream()
				for docHis in docs_hist_app :
					because = docHis.to_dict()['detail_of_approve']

				for docStd in docs_std:
					userid = docStd.to_dict()['userID_from_line']

				
				send_date = data_dict['Date_time']+timedelta(hours=7)
				str_hour=''
				str_min=''
				if send_date.hour<10:
					str_hour='0'+str(send_date.hour)
				else:
					str_hour=str(send_date.hour)
				if send_date.minute<10:
					str_min = '0'+str(send_date.minute)
				else:
					str_min = str(send_date.minute)
				text = 'คำร้อง: '+data_dict['Topic']+'\n'
				text = text+'ส่งคำร้องเมื่อ: '+str(send_date.day)+' '+dict_num_to_month[send_date.month]+' '+str(send_date.year+543)+'\n'
				text = text+'เวลา: '+str_hour+':'+str_min+'\n'
				
				text = text+'ถูกปฏิเสธ เนื่องจาก' + because+'\n'
				text=text+'ขออภัยสำหรับการปฏิเสธการแจ้งคำร้องในครั้งนี้'
				line_bot_api.push_message(userid, TextSendMessage(text=text))
				doc_listenner_dict[petID].unsubscribe()

				
			



# creating the flask app 
app = Flask(__name__) 
# creating an API object 
api = Api(app) 

# making a class for a particular resource 
# the get, post methods correspond to get and post requests 
# they are automatically mapped by flask_restful. 
# other methods include put, delete, etc.

class report(Resource):
	def get(self):

		return 0

	def post(self):
		#data = request.get_json()
		dt = datetime.now()
		year = dt.year
		month = dt.month
		lower_date = datetime(year,month,1)
		upper_date=''
		if (month+1)<13:
			upper_date = datetime(year,month+1,1)
		else:
			upper_date = datetime(year+1,1,1)

		collect_ref=db.collection('Petition')
		query_date_result=collect_ref.where('Date_time','>=',lower_date).where('Date_time','<',upper_date)
		query_result = query_date_result.where('currentStatus','==',3).stream()
		use_n_petition={}
		use_n_max=[]
		
		for doc in query_result:
			useID=doc.to_dict()['User_ID']
			if useID in use_n_petition:
				use_n_petition[useID]=use_n_petition[useID]+1
			else:
				use_n_petition[useID]=1
		if len(use_n_petition)==0:
			return jsonify({'data': 'ในเดือนนี้ยังไม่มีนักศึกษาแจ้งคำร้อง'})
		MAX=0
		key_of_max=''
		for key,value in use_n_petition.items():
			if value>MAX:
				MAX=value
				key_of_max=key
		
		for key,value in use_n_petition.items():
			if value==MAX and not(key in use_n_max):
				use_n_max.append(key)

		str_name=u''
		
		for index in range(len(use_n_max)):
			find_std_result = db.collection('Student').where('User_ID','==',use_n_max[index]).stream()
			doc_result=''
			for doc in find_std_result:
				doc_result=doc
				str_name=doc_result.to_dict()['Name']+' '+doc_result.to_dict()['Last_Name']
			if index < len(use_n_max)-1:
				str_name=str_name+'\n'
		return jsonify({'data': str_name})
		



class addExternalUser(Resource):
	def get(self):

		return jsonify({'message': 'hello world'})

	def post(self):
		data = request.get_json()
		result_query = db.collection('User').where('userID_from_line','==',data['userid']).stream()
		use_to_add=True
		for doc in result_query:
			use_to_add = False
		message = ''
		if use_to_add :
			data_add = {'User_ID':data['userid'],
						'nPetition':1,
						'userID_from_line':data['userid']}
			db.collection('User').document(data['userid']).set(data_add)
		
		return jsonify({'add_case': use_to_add})


class statusSelect(Resource):
	status_map={'เสร็จสิ้น':3,'ถูกปฏิเสธ':5}
	def post(self):
		data = request.get_json()
		userID = data['userID']
		docs = db.collection("Student").where('userID_from_line','==',userID).stream()
		#return jsonify(data)
		std_type=False
		use_id = userID
		petition_ref = db.collection("Petition")
		for doc in docs:
			std_type=True
			use_id = doc.to_dict()['User_ID']
		month_last=-1
		month_list=[]
		year = (datetime.now()+timedelta(hours=7)).year
		lower_date = datetime(year,1,1)
		upper_date = datetime(year+1,1,1)
		query_where = ''
		if std_type:
			
			if data['status']=='กำลังดำเนินการ':
				query_where = petition_ref.where('User_ID','==',use_id).where('currentStatus','in',[2,4])
				
			else:
				num_status = self.status_map[data['status']]
				query_where = petition_ref.where('User_ID','==',use_id).where('currentStatus','==',num_status)

			query_where = query_where.where('Date_time','>=',lower_date).where('Date_time','<',upper_date)
				
			query = query_where.order_by('Date_time',direction=firestore.Query.DESCENDING).limit(1)
			result_stream = query.stream()
			docs = list(result_stream)
			last_month=0
			if len(docs)>0:
				last_month = (docs[0].to_dict()['Date_time']+timedelta(hours=7)).month
			for x in range(1,last_month):
				query_doc = query_where.where('Date_time','<',datetime(year,x+1,1))
				query_doc = query_doc.order_by('Date_time',direction=firestore.Query.DESCENDING).limit(1)
				query_doc_result = query_doc.stream()
				list_result = list(query_doc_result)
				if len(list_result)==0:
					continue
				doc = list_result[0].to_dict()
				month = (doc['Date_time']+timedelta(hours=7)).month
				month_list.append(month)
					#mth  = (doc.to_dict()['Date_time']+timedelta(hours=7)).month
					#month_last = dt.month
		else:
			if data['status']=='กำลังดำเนินการ':
				query_where = petition_ref.where('User_ID','==',use_id).where('currentStatus','in',[2,4])

			else:
				num_status = self.status_map[data['status']]
				query_where = petition_ref.where('User_ID','==',use_id).where('currentStatus','==',num_status)

			query_where = query_where.where('Date_time','>=',lower_date).where('Date_time','<',upper_date)

			query = query_where.order_by('Date_time',direction=firestore.Query.DESCENDING).limit(1)
			result_stream = query.stream()
			docs = list(result_stream)
			last_month=0
			if len(docs)>0:
				last_month = (docs[0].to_dict()['Date_time']+timedelta(hours=7)).month
			for x in range(1,last_month):
				query_doc = query_where.where('Date_time','<',datetime(year,x+1,1))
				query_doc = query_doc.order_by('Date_time',direction=firestore.Query.DESCENDING).limit(1)
				query_doc_result = query_doc.stream()
				list_result = list(query_doc_result)
				if len(list_result)==0:
					continue
				doc = list_result[0].to_dict()
				month = (doc['Date_time']+timedelta(hours=7)).month
				month_list.append(month)
			
		return jsonify({'num': month_list})


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
							
			receiver_email,num_of_department = pretext.classifiedToMail(result,mail_department)
			pet_id=save_petition(data,num_of_department)

			dicImage=getImage_todic(data['messageObj'])
			sent_email(data["topic"],pet_id,data["detail"],dicImage,receiver_email)
			userid = data['userid']
			text ='ได้รับคำร้องเรียบร้อยแล้ว ขอบคุณสำหรับการส่งคำร้อง'
			line_bot_api.push_message(userid, TextSendMessage(text=text))
			return jsonify({'data': text})
		except:
			text ='ไม่สามารถส่งคำร้องได้ เนื่องจากระบบรับคำร้องขัดข้อง กรุณาลองอีกครั้ง'
			line_bot_api.push_message(userid, TextSendMessage(text=text))
			return jsonify({'data':'error'})



class StatusMonthSelect(Resource):
	status_map={'เสร็จสิ้น':[3],'กำลังดำเนินการ':[2,4],'ถูกปฏิเสธ':[5]}
	def post(self):
		data = request.get_json()
		userID = data['userID']
		docs = db.collection("Student").where('userID_from_line','==',userID).stream()

		use_id = userID
		petition_ref = db.collection("Petition")
		for doc in docs:
			use_id = doc.to_dict()['User_ID']

		month_select_dict = 	{'มกราคม':1,'กุมภาพันธ์':2,'มีนาคม':3,'เมษายน':4,'พฤษภาคม':5,'มิถุนายน':6,
					 'กรกฎาคม':7,'สิงหาคม':8,'กันยายน':9,'ตุลาคม':10,'พฤศจิกายน':11,'ธันวาคม':12}
		month_select=int(data['month_select']['startDate'][5:7])
		year = int(data['month_select']['startDate'][:4])
		dt_select_lower = datetime(year,month_select,1)
		dt_select_upper=''
		if month_select<12:
			dt_select_upper = datetime(year,month_select+1,1)
		else:
			dt_select_upper = datetime(year+1,1,1)
		petition_ref = db.collection(u'Petition')
		query_by_userID = petition_ref.where('User_ID','==',use_id)
		query_by_status = query_by_userID.where('currentStatus','in',self.status_map[data['status']])
		query_from_month = query_by_status.where(u'Date_time', u'>=', dt_select_lower).where('Date_time','<',dt_select_upper)
		query_result = query_from_month.stream()
		
		num_of_docs_ref = len(list(query_result))
		n=(num_of_docs_ref//10)+1


		return jsonify({'num':n})

class ShowPetition_Select(Resource):
	status_map={'เสร็จสิ้น':[3],'กำลังดำเนินการ':[2,4],'ถูกปฏิเสธ':[5]}
	def post(self):

		data = request.get_json()
		#return jsonify({'data':data})
		userID = data['userID']
		docs = db.collection("Student").where('userID_from_line','==',userID).stream()

		use_id = userID
		petition_ref = db.collection("Petition")
		for doc in docs:
			use_id = doc.to_dict()['User_ID']

		#month_select_dict =     {'มกราคม':1,'กุมภาพันธ์':2,'มีนาคม':3,'เมษายน':4,'พฤษภาคม':5,'มิถุนายน':6,
                #                         'กรกฎาคม':7,'สิงหาคม':8,'กันยายน':9,'ตุลาคม':10,'พฤศจิกายน':11,'ธันวาคม':12}
		month_select=int(data['month_select']['startDate'][5:7])
		dt_now = datetime.now()+timedelta(hours=7)
		year = dt_now.year
		#return jsonify({'data':dt_now})
		dt_select_lower = datetime(year,month_select,1)
		dt_select_upper = datetime(year,month_select,1)
		
		if month_select<12:
			dt_select_upper = datetime(year,month_select+1,1)
		else:
			dt_select_upper = datetime(year+1,1,1)
		petition_ref = db.collection(u'Petition')
		query_by_userID = petition_ref.where('User_ID','==',use_id)
		query_by_status = query_by_userID.where('currentStatus','in',self.status_map[data['status']])
		query_from_month = query_by_status.where(u'Date_time', u'>=', dt_select_lower).where('Date_time','<',dt_select_upper)
		query_order = query_from_month.order_by('Date_time')
		query_result = query_order.stream()
		
		underNum = data['underNum']
		upperNum = data['upperNum']
		doc_list = list(query_result)
		doc_select = doc_list[(underNum-1):upperNum].copy()
		#return jsonify({'data':len(doc_list)})
		dict_query={}
		pet_id_list=[]
		pet_status_list=[]
		pet_dict = {}
		for index in range(len(doc_select)):
			doc_dict=doc_select[index].to_dict()
			#dict_map={'ID':doc_dict['ID'],'currentStatus':doc_dict['currentStatus']}
			#dict_query[str(index+1)]=dict_map.copy()
			pet_id_list.append(doc_dict['ID'])
			pet_status_list.append(doc_dict['currentStatus'])
		
		#return jsonify({'data':pet_status_list})
		his_ref = db.collection('History_Approve')
		query_by_pet_id = his_ref.where('petition_ID','in',pet_id_list)
		#return jsonify({'data':list_message})
		#query_by_status = query_by_pet_id.where('CaseStatus','in',pet_status_list)
		query_pet_id_result = query_by_pet_id.stream()
		his_list=list(query_pet_id_result)
		query_his_result=[]
		for subdoc_his in his_list:
			doc = subdoc_his.to_dict()
			if doc['CaseStatus'] in pet_status_list:
				query_his_result.append(subdoc_his)

		department_dict={'1':'กองอาคารสถานที่','0':'กองประชาสัมพันธ์','3':'สํานักวิทยบริการและเทคโนโลยีสารสนเทศ','2':'สํานักจัดการทรัพย์สิน','4':'กองกลาง'}
		str_work_dict = {0:['ขณะนี้ถูกดำเนินการโดย: '],3:['ดำเนินการโดย: '],5:['ปฏิเสธโดย: ','เนื่องจาก: ']}
		str_show_pet=''
		his_show_count=underNum
		list_message=[]
		for sub_doc in doc_select:
			y=sub_doc.to_dict()
			for doc in query_his_result:
				doc_form_dict = doc.to_dict()
				if y['ID']==doc_form_dict['petition_ID'] and y['currentStatus']==doc_form_dict['CaseStatus']:
					str_show_pet=str(his_show_count)+'.'+y['Topic']+'\n'
					str_show_pet=str_show_pet+'รายละเอียด: '+y['Detail']+'\n'
					number_status_select=0
					if not(y['currentStatus'] in str_work_dict):
						number_status_select = y['currentStatus']%2
						str_show_pet = str_show_pet+str_work_dict[number_status_select][0]
						str_show_pet = str_show_pet+department_dict[doc_form_dict['Department']]
					else:
						number_status_select=y['currentStatus']
						str_show_pet = str_show_pet+str_work_dict[number_status_select][0]
						str_show_pet = str_show_pet+department_dict[doc_form_dict['Department']]
						if number_status_select == 5:
							str_show_pet = str_show_pet+'\n'
							str_show_pet = str_show_pet+str_work_dict[number_status_select][1]
							str_show_pet = str_show_pet+doc_form_dict['detail_of_approve']
					his_show_count+=1
					list_message.append(str_show_pet)
					break
					
			#list_message.append(str_show_pet)
			#if '' in list_message:
			#	list_message.remove('')

		return jsonify({'data':list_message})
class AddStudent(Resource):

	addStd_message = {0:u'ไม่สามารถบัญชีไลน์โมบายแอปพลิเคชันนี้ได้ เนื่องจากรหัสนักศึกษา หรือรหัสสำหรับบันทึกไม่ถูกต้อง กรุณาลองอีกครั้ง',
			1:u'บันทึกบัญชีไลน์โมบายแอปพลิเคชันของนักศึกษาเรียบร้อย'}
	def post(self):
		data = request.get_json()
		std_id = data['studentCode']
		use_id = data['userID']
		token = data['token']
		
		message=''
		std_ref=db.collection('Student')
		query_of_check=std_ref.where('userID_from_line','==',use_id)
		check_result = query_of_check.stream()
		check = list(check_result)
		if len(check)==0: 
			std_query= std_ref.where('User_ID','==',std_id).where('Code','==',token)
			query_result = std_query.stream()
			query_form_list = list(query_result)
			doc=query_form_list[0]
			doc_ref = db.collection('Student').document(doc.id)
			doc_ref.update({'userID_from_line':use_id,'nPetition':1})
			n_query_form_list = len(query_form_list)
		
			message = self.addStd_message[n_query_form_list]
		else:
			message = u'มีบัญชีไลน์โมบายแอปพลิเคชันของนักศึกษาแล้ว สามารถทำรายการต่างๆผ่านไลน์โมบายแอปพลิเคชันได้แล้ว'
		return jsonify({'data':message})
# another resource to calculate the square of a number 



# adding the defined resources along with their corresponding urls 
api.add_resource(Classified, '/') 
api.add_resource(addExternalUser,'/addExternalUser')
api.add_resource(report,'/RequestReport')
api.add_resource(statusSelect,'/StatusSelect')
api.add_resource(StatusMonthSelect,'/status_monthSelect')
api.add_resource(AddStudent,'/addStudent')
# driver function 
api.add_resource(ShowPetition_Select,'/petition_showSelect')

if __name__ == '__main__': 

	app.secret_key = os.environ.get('SECRET_KEY')
	app.run(debug = False,host='0.0.0.0') 
	
