import psycopg2
import os
class Database():
  me = None
  def __init__(self):
    if Database.me !=None:
      raise Exception('Instance of database already exists!')
    Database.me= psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
    Database.me.autocommit = True
    self.fdb= Database.me.cursor()
    Database.me.commit()
  def __getitem__(self, key):
    self.fdb.execute("SELECT value FROM main WHERE key=%s",(key,))
    return self.fdb.fetchone()[0]
  def __setitem__(self,key,value):
    self.fdb.execute("INSERT INTO main (key,value) VALUES(%s,%s) ON CONFLICT (key) DO UPDATE SET value =%s",(key,value,value))
  def keys(self):
    self.fdb.execute('SELECT key FROM main')
    return [ key[0] for key in self.fdb.fetchall()]