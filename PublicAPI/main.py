import sqlite3
from fastapi import FastAPI, Response, status
from passlib.hash import pbkdf2_sha256
import random
import string
from requests import session
import datetime
from dateutil import parser
app = FastAPI()
db = sqlite3.connect("db.sqlite3",check_same_thread=False)
cursor = db.cursor()


cursor.execute("""CREATE TABLE IF NOT EXISTS `users` (`username` TEXT PRIMARY KEY ,
 `password` TEXT);""")
cursor.execute("""CREATE TABLE IF NOT EXISTS `locations` (`username` TEXT,
 `location` TEXT,
  `time` DATETIME,
   FOREIGN KEY (`username`)
 REFERENCES `users` (`username`));""")
cursor.execute("""CREATE TABLE IF NOT EXISTS `sessions` (`username` TEXT,
 `sessionid` TEXT,
  FOREIGN KEY (`username`)
 REFERENCES `users` (`username`));""")
db.commit()
db.commit()
@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/login")
async def login(username, password, response: Response):
    cursor.execute("SELECT `password` FROM users WHERE `username` = ?;", (username,))
    hash_ = cursor.fetchone()
    if hash_==None or not pbkdf2_sha256.verify(password,hash_[0]):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "error", "message": "Invalid credentials"}
    sessionid = ''.join(random.choice(string.ascii_lowercase) for i in range(64))
    cursor.execute("INSERT INTO `sessions` VALUES (?, ?);", (username, sessionid))
    db.commit()
    return {"status": "ok", "sessionid": sessionid}
    
@app.put("/create_user")
async def create_user(username, password, response: Response):
    cursor.execute("SELECT EXISTS(SELECT `username` FROM users WHERE `username` = ?);", (username,))
    if cursor.fetchone()[0] == 1:
        response.status_code = status.HTTP_409_CONFLICT
        return {"status": "error", "message": "Username already exists"}
    cursor.execute("INSERT INTO users VALUES (?, ?);", (username, pbkdf2_sha256.hash(password)))
    db.commit()
    return {"status": "ok"}


@app.post("/change_password")
async def change_password(sessionid, old_password, new_password, response: Response):
    cursor.execute("SELECT `username` FROM sessions WHERE `sessionid` = ?;", (sessionid,))
    username = cursor.fetchone()
    if username==None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "error", "message": "Invalid sessionid"}
    cursor.execute("SELECT `password` FROM users WHERE `username` = ?;", (username[0],))
    hash_ = cursor.fetchone()
    if not pbkdf2_sha256.verify(old_password,hash_[0]):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "error", "message": "Invalid credentials"}
    cursor.execute("UPDATE users SET `password` = ? WHERE `username` = ?;", (pbkdf2_sha256.hash(new_password), username[0]))
    db.commit()
    return {"status": "ok"}


@app.post("/signout")
async def signout(sessionid, response: Response):
    cursor.execute("SELECT `username` FROM sessions WHERE `sessionid` = ?;", (sessionid,))
    username = cursor.fetchone()
    if username==None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "error", "message": "Invalid sessionid"}
    cursor.execute("DELETE FROM sessions WHERE `username` = ?;", (username[0],))
    db.commit()
    return {"status": "ok"}


@app.put("/send_location")
def log_location(sessionid, location, response: Response):
    cursor.execute("SELECT `username` FROM sessions WHERE `sessionid` = ?;", (sessionid,))
    username = cursor.fetchone()
    if username==None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "error", "message": "Invalid sessionid"}
    cursor.execute("INSERT INTO locations VALUES (?, ?, ?);", (username[0], location, datetime.datetime.now()))
    db.commit()

@app.get("/get_location")
def get_location(sessionid, response: Response):
    cursor.execute("SELECT `username` FROM sessions WHERE `sessionid` = ?;", (sessionid,))
    username = cursor.fetchone()
    if username==None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "error", "message": "Invalid sessionid"}
    cursor.execute("SELECT `location`,`time` FROM `locations` WHERE `username` = ? ORDER BY `time`;", (username[0],))
    location = cursor.fetchall()
    dead_times = []
    old_time=None
    for item in location:
        print(item)
        if old_time==None:
            old_time=item
            continue
        print((parser.parse(item[1])-parser.parse(old_time[1])).total_seconds())
        if (parser.parse(item[1])-parser.parse(old_time[1])).total_seconds() > 5:
            dead_times.append(old_time)
        old_time=item

    return {"status": "ok", "location": dead_times}
