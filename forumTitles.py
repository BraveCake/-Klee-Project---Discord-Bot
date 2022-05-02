import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


class ForumTitles():
    me = None

    def __init__(self):
        if ForumTitles.me != None:
            raise Exception('Instance of database already exists!')
        cred = credentials.Certificate("key.json")
        firebase_admin.initialize_app(cred)
        ForumTitles.me = firestore.client()
    @staticmethod	
    def update(key, value,optional_value=''):
        if (not key.isnumeric()):
            return
        if ForumTitles.me==None:
            ForumTitles()
        ForumTitles.me.collection(u'users').document(key).set({"title": value,"discord":optional_value})
