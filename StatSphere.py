from flask import *
from datetime import datetime
import requests
from flask_socketio import SocketIO, emit
import ast
import threading
from  flask_sqlalchemy import SQLAlchemy
from datetime import *
import time

app = Flask(__name__)
socketio = SocketIO(app)
app.config["SECRET_KEY"] = "animation197i"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///news.db"

football_data_api_key = "a75fb6a4a6f648b6a406b77982c61f7c"
football_data_api_key1 = "b6e238f79009406a8aa66496887dd495"
football_data_url = "https://api.football-data.org/v4/{}/"
football_data_header =  {"X-Auth-Token":football_data_api_key}
news_api_header = {
    "X-Api-Key": "ad4f429ab6dd4fd6b5dd137fcbb6f42a",  
}

current_date = datetime.now()
three_days_ago = current_date - timedelta(days=2)
get_tdate = three_days_ago.strftime("%Y-%m-%d")

get_today = date.today()

football_keywords = ("soccer", "Premier League", "La Liga", "Bundesliga", "Serie A", "Champions League", "World Cup", "UEFA", "FIFA", "goal", "match", "score", "team", "player", "transfer", "manager", "tournament", "penalty", "injury", "referee", "stadium", "fan", "club")

newsapi_param = {
    "q":football_keywords,
    "language":"en",
    "sortBy":"relevancy",
    "from":get_tdate,
    "to":get_today
}
news_api_url = "https://newsapi.org/v2/everything"
db = SQLAlchemy(app)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String, nullable = False)
    author = db.Column(db.String, nullable = True)
    title = db.Column(db.String, nullable = False)
    url = db.Column(db.String, nullable=False)
    urlToImage = db.Column(db.String , nullable = False)
    publishedAt = db.Column(db.String, nullable = False)
    content = db.Column(db.String, nullable = False)

app.app_context().push()
db.create_all()

@app.route("/", methods = ["POST","GET"])
def home():
    response = requests.get(football_data_url.format("matches"),headers = football_data_header)
    
    data = response.json()["matches"]
    date_list = []
    time_list = []
    
    for get_date in data:
        date_string = get_date["utcDate"]
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        
        parsed_date = datetime.strptime(date_string, date_format)
        day_of_week = parsed_date.strftime("%A")
        
        date_list.append(day_of_week)
        time_list.append(date_string[11:16])
    print(time_list)
    
    if request.method == "POST":
        data = ast.literal_eval(request.form["data"])
        print(data)
        session["data"] = data
        return redirect("match_details")
    else:
        return render_template("home.html", data = data, dates = date_list,time_list = time_list)

@app.route("/match_details")   
def match_details():
    data = session.get("data")
    return render_template("match_details.html",data = data)

@app.route("/competitions", methods = ["POST","GET"])
def competitions():
      if request.method == "POST":
          comp_id = request.form["comp_id"]
          format_url = f"/competitions/{comp_id}/standings"
          response = requests.get(football_data_url.format(format_url),headers = football_data_header)
          
          data = response.json()
          session["tabledata"] = data
          print(comp_id)
          return redirect("/leaguetable")
          
      else:
          response = requests.get(football_data_url.format("competitions"), headers = football_data_header)
          data = response.json()["competitions"]
          print(data)
          return render_template("competitions.html",data = data)

@app.route("/leaguetable")
def leaguetable():
          if request.method == "POST":
              return "ok"
          else:
              table_data = session.get("tabledata")
              return render_template("leaguetable.html", data = table_data)

@app.route("/livescore", methods=["POST","GET"])
def livescore():                             
    response = requests.get(football_data_url.format("matches"),headers = football_data_header)
    data = response.json()["matches"]
    
    date_list = []
    time_list = []
    
    for get_date in data:
        date_string = get_date["utcDate"]
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        
        parsed_date = datetime.strptime(date_string, date_format)
        day_of_week = parsed_date.strftime("%A")
        
        date_list.append(day_of_week)
        time_list.append(date_string[11:16])
    
    if request.method == "POST":
        return "ok"
    else:
        response = requests.get(football_data_url.format("matches"),headers = football_data_header)
        data = response.json()["matches"]
        return render_template("livescore.html", data = data, dates = date_list, time_list = time_list)   

def live_update():
    import time
    while True:
        response = requests.get(football_data_url.format("matches"),headers = football_data_header)
        data = response.json()["matches"]
        
        update_data = {}
        
        for get_update in data:
            if get_update["status"] == "IN_PLAY" or get_update["status"] == "PAUSED":
                homeTeamScore = get_update["score"]["fullTime"]["home"]
                awayTeamScore = get_update["score"]["fullTime"]["away"]
                homTeam = get_update["homeTeam"]["tla"]
                awayTeam = get_update["awayTeam"]["tla"]
                update_data[homTeam]= homeTeamScore
                update_data[awayTeam] = awayTeamScore
        
        data = update_data
        socketio.emit('get_update',data)
        time.sleep(10)

def publish_news():
    response=requests.get(news_api_url, headers = news_api_header, params = newsapi_param)
    data = response.json()["articles"]
    app.app_context().push()
    get_content = db.session.query(News).all()
    content_list = []
    for check_con in get_content:
        content_list.append(check_con.content)
    
    for get_article_data in data:
        source = get_article_data["source"]["name"]
        author = get_article_data["author"]
        title = get_article_data["title"]
        url = get_article_data["url"]
        urlToImage = get_article_data["urlToImage"]
        publishedAt = get_article_data["publishedAt"]
        content = get_article_data["content"]
        
        if content not in content_list and author != None and urlToImage!=None and source != None and title  != None and content != None and url != None and publishedAt != None:
            
            new_news_set = News(source=source, author=author, title=title, url=url, urlToImage=urlToImage, publishedAt=publishedAt, content=content)
            db.session.add(new_news_set)
            db.session.commit()
    
def news():
    publish_news()
    while True:
        now = datetime.now()
        if now.hour == 5 and now.minute == 5 and now.second == 0:
            publish_news()        

def get_user_input():
    while True:        
        user_input = input("Enter your request \n[ptm : Post Today's Match]\n[md : Matches Data]\n[lvs : livescore]: ")
        if user_input=="news":
            news()                                                                       

@app.route("/newpage", methods=["POST","GET"])
def newspage():
    
    if request.method == "POST":
        print("ok")
    else:
        news_data = db.session.query(News).all()
        return render_template("newspage.html", news_data = news_data)
if __name__ == '__main__':
    threading.Thread(target=live_update).start()
    threading.Thread(target=news).start()
    #threading.Thread(target=get_user_input).start()
    socketio.run(app, debug=True)