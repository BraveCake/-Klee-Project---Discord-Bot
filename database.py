import psycopg2
import os

class Database():
  me = None
  def __init__(self):
    if Database.me !=None:
      raise Exception('Instance of database already exists!')
    Database.me= psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
    self.fdb= Database.me.cursor()

  def __getitem__(self, key):
        return self.fdb.execute('SELECT value FROM main WHERE key='+key).fetchone()
  def __setitem__(self,key,value):
    self.fdb.execute('INSERT INTO main (key,value) VALUES('+key+','+value+') ON DUPLICATE KEY UPDATE key='+key+' value ='+value)
  def keys(self):
    return self.fdb.execute('SELECT key FROM main').fetchone().fetchall()