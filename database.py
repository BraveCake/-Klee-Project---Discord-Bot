import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
class Database():
  me = None
  def __init__(self):
    if Database.me !=None:
      raise Exception('Instance of database already exists!')
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred)
    self.fdb= firestore.client()
  def __getitem__(self, key):
        return self.fdb.collection(u'mainc').document(key).get().to_dict()['value']
  def __setitem__(self,key,value):
    if(key=='__apps__'):
      key='__appss__'
    self.fdb.collection(u'mainc').document(key).set({"value":value})
  def keys(self):
    return map(lambda doc : doc.id,self.fdb.collection(u'mainc').get())