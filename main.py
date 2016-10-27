from flask import Flask, render_template, request, redirect, g
from flask.ext.sqlalchemy import SQLAlchemy
import json
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
sql = SQLAlchemy(app)

#sql = sqlite3.connect("posts.db")
#c = sql.cursor()
c = sql.engine
c.execute("CREATE TABLE IF NOT EXISTS threads(name VARCHAR(140), post VARCHAR(540),id INT, board VARCHAR(140))")
c.execute("CREATE TABLE IF NOT EXISTS posts(name VARCHAR(140), post VARCHAR(540), id INT, board VARCHAR(140), parent INT)")
c.execute("CREATE TABLE IF NOT EXISTS boards(name VARCHAR(140), postcount INT, description VARCHAR(140))")
c.execute("ALTER TABLE boards ALTER COLUMN postcount SET DEFAULT 0")
boards = c.execute("SELECT name FROM boards").fetchall()
with open('boards.json') as config_file:
	config = json.load(config_file)
for i in config["boards"]:
	print(i)
	try:
		name = '$_FLASKBOARD_CONTENT$' + i["name"] + '$_FLASKBOARD_CONTENT$'
		desc = '$_FLASKBOARD_CONTENT$' + i["description"] + '$_FLASKBOARD_CONTENT$'
		board = c.execute("SELECT name FROM boards WHERE name = %s" % name).fetchall()[0][0]
		c.execute("UPDATE boards SET description = '%s' WHERE name = %s" % (desc,name))
		#c.commit()
	except:
		name = '$_FLASKBOARD_CONTENT$' + i["name"] + '$_FLASKBOARD_CONTENT$'
		desc = '$_FLASKBOARD_CONTENT$' + i["description"] + '$_FLASKBOARD_CONTENT$'
		c.execute("INSERT INTO boards(name,description) VALUES(%s,%s)" % (name,desc))
		#c.commit()

@app.before_request
def before_request():
	g.db = SQLAlchemy(app).engine

@app.teardown_request
def teardown_request(exception):
	if hasattr(g,'db'):
		#g.db.close()
		pass
		
@app.route('/')
def hello_world():
	boardlist = g.db.execute("SELECT name,description FROM boards").fetchall()
	returnboards = []
	for i in boardlist:
		returnboards.append([i[0].replace('$_FLASKBOARD_CONTENT$',''), i[1].replace('$_FLASKBOARD_CONTENT$','')])
	return render_template('index.html',boardlist=returnboards)
	
@app.route('/boards/<ident>')
def showboard(ident):
	try:
		realident = "$_FLASKBOARD_CONTENT$" + ident + "$_FLASKBOARD_CONTENT$"
		board = g.db.execute("SELECT name,description FROM boards WHERE name = %s" % realident).fetchall()
		realboard = []
		for i in board:
			realboard.append(i[0])
			realboard.append(i[1].replace('$_FLASKBOARD_CONTENT$',''))
		posts = g.db.execute("SELECT name,post FROM threads WHERE board = %s" % realident).fetchall()
		realpost = []
		for i in posts:
			realpost.append(i[0].replace('$_FLASKBOARD_CONTENT$',''))
			realpost.append(i[1].replace('$_FLASKBOARD_CONTENT$',''))
		print(board)
		print(realboard)
		return render_template('board.html',posts=realpost,board=realboard,ident=ident)
		
	except:
		return "Board not found."
	
@app.route('/boards/<b>/threads/<ident>')
def showthread(ident,b):
	sqlb = "$_FLASKBOARD_CONTENT$" + b + "$_FLASKBOARD_CONTENT$"
	realident = "$_FLASKBOARD_CONTENT$" + ident + "$_FLASKBOARD_CONTENT$"
	try:
		op = g.db.execute("SELECT name,post,id FROM threads WHERE id = %s AND board = %s", (ident,sqlb)).fetchall()[0]
		try:
			posts = g.db.execute("SELECT * FROM posts WHERE parent = %s AND board = %s" % (ident,sqlb)).fetchall()
		except:
			posts = []
		return render_template('thread.html',title=op[0],posts=posts,ident=ident,op=op,b=b)
	except TypeError as e:
		print(e)
		return "Thread not found."
		
@app.route('/boards/<b>/threads/postthread',methods=['POST'])
def post(b):
	name = "$_FLASKBOARD_CONTENT$" + request.form['subject'] + "$_FLASKBOARD_CONTENT$"
	comment = "$_FLASKBOARD_CONTENT$" + request.form['content'] + "$_FLASKBOARD_CONTENT$"
	if name.strip().replace("$_FLASKBOARD_CONTENT$","") == '':
		name = "Anonymous Thread"
	print("Thread subject: " + name)
	print("Thread content: " + comment)
	sqlb = "$_FLASKBOARD_CONTENT$" + b + "$_FLASKBOARD_CONTENT$"
	try:
		id = int(g.db.execute("SELECT postcount FROM boards WHERE name = %s" % sqlb).fetchall()[0][0])
	except:
		id = 0
	print(id+1)
	g.db.execute("INSERT INTO threads VALUES(%s,%s,%s,'%s')" % (name,comment,int(id+1),sqlb))
	g.db.execute("UPDATE boards SET postcount = postcount + 1 WHERE name = %s" % sqlb)
	#g.db.commit()
	return redirect("/boards/%s/threads/%s" % (str(b),str(id+1)))

@app.route('/boards/<b>/threads/postreply/<ident>',methods=['POST'])
def postreply(b,ident):
	name = "$_FLASKBOARD_CONTENT$" + request.form['subject'] + "$_FLASKBOARD_CONTENT$"
	comment = "$_FLASKBOARD_CONTENT$" + request.form['content'] + "$_FLASKBOARD_CONTENT$"#fix ' insert
	if name.strip().replace("$_FLASKBOARD_CONTENT$","") == '':
		name = "$_FLASKBOARD_CONTENT$Anonymous$_FLASKBOARD_CONTENT$"
	print("Post name: " + name)
	print("Post content: " + comment)
	sqlb = "$_FLASKBOARD_CONTENT$" + b + "$_FLASKBOARD_CONTENT$"
	realident = "$_FLASKBOARD_CONTENT$" + ident + "$_FLASKBOARD_CONTENT$"
	try:
		id = int(g.db.execute("SELECT postcount FROM boards WHERE name = %s" % sqlb).fetchall()[0][0])
	except:
		id = 0
	print(id+1)
	g.db.execute("INSERT INTO posts VALUES(%s,%s,%s,'%s',%s)" % (name,comment,int(id+1),sqlb,int(ident)))
	g.db.execute("UPDATE boards SET postcount = postcount + 1 WHERE name = %s" % sqlb)
	#g.db.commit()
	return redirect("/boards/%s/threads/%s" % (str(b),str(ident)))

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
