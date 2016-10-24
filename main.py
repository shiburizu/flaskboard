from flask import Flask, render_template, request, redirect, g
import sqlite3
import json
app = Flask(__name__)

sql = sqlite3.connect("posts.db")
c = sql.cursor()
c.execute("CREATE TABLE IF NOT EXISTS threads(name TEXT, post TEXT,id INTEGER, board TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS posts(name TEXT, post TEXT, id INTEGER, board TEXT, parent TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS boards(name TEXT, postcount INTEGER DEFAULT 0, desc TEXT)")
boards = c.execute("SELECT name FROM boards").fetchall()
with open('boards.json') as config_file:
	config = json.load(config_file)
for i in config["boards"]:
	print(i)
	try:
		board = c.execute("SELECT name FROM boards WHERE name = ?",(i["name"],)).fetchall()[0][0]
		c.execute("UPDATE boards SET desc = ? WHERE name = ?",(i["desc"],i["name"]))
		sql.commit()
	except:
		c.execute("INSERT INTO boards(name,desc) VALUES(?,?)",(i["name"],i["desc"]))
		sql.commit()

@app.before_request
def before_request():
	g.db = sqlite3.connect("posts.db")

@app.teardown_request
def teardown_request(exception):
	if hasattr(g,'db'):
		g.db.close()

@app.route('/')
def hello_world():
	boardlist = g.db.execute("SELECT * FROM boards").fetchall()
	return render_template('index.html',boardlist=boardlist)
	
@app.route('/boards/<ident>')
def showboard(ident):
	try:
		board = g.db.execute("SELECT * FROM boards WHERE name = ?",(ident,)).fetchall()[0]
		posts = g.db.execute("SELECT * FROM threads WHERE board = ?",(ident,)).fetchall()
		return render_template('board.html',posts=posts,board=board,ident=ident)
	except:
		return "Board not found."
	
@app.route('/boards/<b>/threads/<ident>')
def showthread(ident,b):
	try:
		op = g.db.execute("SELECT name,post,id FROM threads WHERE id = ? AND board = ?",(ident,b)).fetchall()[0]
		print(op)
		posts = g.db.execute("SELECT * FROM posts WHERE parent = ? AND board = ?",(ident,b)).fetchall()
		title = g.db.execute("SELECT name FROM threads WHERE id = ? AND board = ?",(ident,b)).fetchall()[0][0]
		return render_template('thread.html',title=title,posts=posts,ident=ident,op=op,b=b)
	except:
		return "Thread not found."
		
@app.route('/boards/<b>/threads/postthread',methods=['POST'])
def post(b):
	name = request.form['subject']
	comment = request.form['content']
	if name.strip() == '':
		name = "Anonymous Thread"
	print("Thread subject: " + name)
	print("Thread content: " + comment)
	try:
		id = int(g.db.execute("SELECT postcount FROM boards WHERE name = ?", (b,)).fetchall()[0][0])
	except:
		id = 0
	print(id+1)
	g.db.execute("INSERT INTO threads VALUES(?,?,?,?)", (name,comment,int(id+1),str(b)))
	g.db.execute("UPDATE boards SET postcount = postcount + 1 WHERE name = ?", (b,))
	g.db.commit()
	return redirect('/boards/%s/threads/%s' % (str(b),str(id+1)))

@app.route('/boards/<b>/threads/postreply/<ident>',methods=['POST'])
def postreply(b,ident):
	name = request.form['subject']
	comment = request.form['content']
	if name.strip() == '':
		name = "Anonymous"
	print("Post name: " + name)
	print("Post content: " + comment)
	try:
		id = int(g.db.execute("SELECT postcount FROM boards WHERE name = ?", (b,)).fetchall()[0][0])
	except:
		id = 0
	print(id+1)
	g.db.execute("INSERT INTO posts VALUES(?,?,?,?,?)", (name,comment,int(id+1),str(b),str(ident)))
	g.db.execute("UPDATE boards SET postcount = postcount + 1 WHERE name = ?", (b,))
	g.db.commit()
	return redirect('/boards/%s/threads/%s' % (str(b),str(ident)))

if __name__ == '__main__':
	app.run()
