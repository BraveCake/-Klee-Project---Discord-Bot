import os

import psycopg2

class Database():
  me = None
  def __init__(self):
    if Database.me !=None:
      raise Exception('Instance of database already exists!')
    Database.me= psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')
    self.fdb= Database.me.cursor()

  def __getitem__(self, key):
        return self.fdb.execute("SELECT value FROM main WHERE key=%s",(key)).fetchone()
  def __setitem__(self,key,value):
    self.fdb.execute("INSERT INTO main (key,value) VALUES(%s,%s) ON CONFLICT (key) DO UPDATE SET value =%s",(key,value,value))
  def keys(self):
    return self.fdb.execute('SELECT key FROM main').fetchone().fetchall()