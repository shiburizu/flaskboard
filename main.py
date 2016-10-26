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
c.execute("CREATE TABLE IF NOT EXISTS threads(name VARCHAR(100), post VARCHAR(500),id INT, board VARCHAR(20))")
c.execute("CREATE TABLE IF NOT EXISTS posts(name VARCHAR(100), post VARCHAR(500), id INT, board VARCHAR(20), parent VARCHAR(100))")
c.execute("CREATE TABLE IF NOT EXISTS boards(name VARCHAR(100), postcount INT, description VARCHAR(100))")
c.execute("ALTER TABLE boards ALTER COLUMN postcount SET DEFAULT 0")
boards = c.execute("SELECT name FROM boards").fetchall()
with open('boards.json') as config_file:
	config = json.load(config_file)
for i in config["boards"]:
	print(i)
	try:
		board = c.execute("SELECT name FROM boards WHERE name = '%s'" % i["name"]).fetchall()[0][0]
		c.execute("UPDATE boards SET description = '%s' WHERE name = '%s'" % (i["description"],i["name"]))
		#c.commit()
	except:
		c.execute("INSERT INTO boards(name,description) VALUES('%s','%s')" % (i["name"],i["description"]))
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
	boardlist = g.db.execute("SELECT * FROM boards").fetchall()
	return render_template('index.html',boardlist=boardlist)
	
@app.route('/boards/<ident>')
def showboard(ident):
	try:
		board = g.db.execute("SELECT * FROM boards WHERE name = '%s'" % ident).fetchall()[0]
		posts = g.db.execute("SELECT * FROM threads WHERE board = '%s'" % ident).fetchall()
		return render_template('board.html',posts=posts,board=board,ident=ident)
	except:
		return "Board not found."
	
@app.route('/boards/<b>/threads/<ident>')
def showthread(ident,b):
	try:
		op = g.db.execute("SELECT name,post,id FROM threads WHERE id = %s AND board = '%s'", (ident,b)).fetchall()[0]
		print(op)
		posts = g.db.execute("SELECT * FROM posts WHERE parent = %s AND board = '%s'" % (ident,b)).fetchall()
		title = g.db.execute("SELECT name FROM threads WHERE id = %s AND board = '%s'" % (ident,b)).fetchall()[0][0]
		return render_template('thread.html',title=title,posts=posts,ident=ident,op=op,b=b)
	except Exception as e:
		print(e)
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
		id = int(g.db.execute("SELECT postcount FROM boards WHERE name = '%s'" % b).fetchall()[0][0])
	except:
		id = 0
	print(id+1)
	g.db.execute("INSERT INTO threads VALUES('%s','%s',%s,'%s')" % (name,comment,int(id+1),str(b)))
	g.db.execute("UPDATE boards SET postcount = postcount + 1 WHERE name = '%s'" % b)
	#g.db.commit()
	return redirect("/boards/%s/threads/%s" % (str(b),str(id+1)))

@app.route('/boards/<b>/threads/postreply/<ident>',methods=['POST'])
def postreply(b,ident):
	name = request.form['subject']
	comment = request.form['content']
	if name.strip() == '':
		name = "Anonymous"
	print("Post name: " + name)
	print("Post content: " + comment)
	try:
		id = int(g.db.execute("SELECT postcount FROM boards WHERE name = '%s'" % b).fetchall()[0][0])
	except:
		id = 0
	print(id+1)
	g.db.execute("INSERT INTO posts VALUES('%s','%s',%s,'%s','%s')" % (name,comment,int(id+1),str(b),str(ident)))
	g.db.execute("UPDATE boards SET postcount = postcount + 1 WHERE name = '%s'" % b)
	#g.db.commit()
	return redirect("/boards/%s/threads/%s" % (str(b),str(ident)))

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
