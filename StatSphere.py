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

football_data_api_key = "1964b441b0df4396bb65ea0bf824ad12"
football_data_api_key1 = "b6e238f79009406a8aa66496887dd495"
football_data_url = "https://api.football-data.org/v4/{}/"
football_data_header =  {"X-Auth-Token":football_data_api_key}
news_api_param = {
    "apikey":"pub_28802732a363123dc636e70651fa9df286e10",
    "q":"football",
    "language":"en"
}

news_api_url = "https://newsdata.io/api/1/news"
db = SQLAlchemy(app)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String, nullable = True)
    creator = db.Column(db.String, nullable = True)
    title = db.Column(db.String, nullable = True)
    category =db.Column(db.String, nullable=True)
    link = db.Column(db.String, nullable=True)
    video_url = db.Column(db.String)
    image_url = db.Column(db.String , nullable = True)
    publishDate = db.Column(db.String, nullable = True)
    description = db.Column(db.String, nullable = True)

app.app_context().push()   
db.create_all()

@app.route("/", methods = ["POST","GET"])
def home():
    response = requests.get(football_data_url.format("matches"),headers = football_data_header)
    
    data = response.json()["matches"]
    date_list = []
    time_list = []
    
    comp_names = []    
    
    for get_date in data:
        date_string = get_date["utcDate"]
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        
        parsed_date = datetime.strptime(date_string, date_format)
        day_of_week = parsed_date.strftime("%A")
        
        date_list.append(day_of_week)
        time_list.append(date_string[11:16])
    
    if request.method == "POST":
        data = ast.literal_eval(request.form["data"])
        session["data"] = data
        return redirect("match_details")
    else:
        for get_comp in data:
            if [get_comp["competition"]["name"],get_comp["area"]["flag"],get_comp["area"]["name"]]  not in comp_names:
                comp_names.append([get_comp["competition"]["name"],get_comp["area"]["flag"],get_comp["area"]["name"]])
            else:
                continue
            
        return render_template("home.html", data = data, dates = date_list,time_list = time_list, comp_names = comp_names)

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
          return redirect("/leaguetable")
          
      else:
          response = requests.get(football_data_url.format("competitions"), headers = football_data_header)
          data = response.json()["competitions"]
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
        print(data)
        time.sleep(10)

def publish_news():
    response=requests.get(url=news_api_url, params = news_api_param)
    data = response.json()["results"]
    
    app.app_context().push()
    get_description = db.session.query(News).all()
    
    check_des_list = []
    for check_des in get_description:
        check_des_list.append(check_des.description)
    
    for get_news in data:
        title = get_news["title"]
        link = get_news["link"]
        video_url = get_news["video_url"]
        description = get_news["description"] 
        pubDate = get_news["pubDate"]
        image_url = get_news["image_url"]
        source_id = get_news["source_id"]
        category = get_news["category"][0]
        creator = str(get_news["creator"])
        
        if title == None:
            title = "no title"
        if link == None:
            link = "link not available"
        if video_url == None:
            video_url = "No video"
        if get_news["creator"] == None:
            creator = "No creator"
        if description == None:
            description = "No description"
        if image_url == None:
            image_url = "No image"
        if source_id == None:
            source_id = "No source"
        if get_news["category"] == None:
            category = "No category"
        
        if description not in check_des_list:
            new_news = News(title=title, link=link, video_url = video_url, description=description, publishDate=pubDate, image_url=image_url, source_id = source_id, category=category, creator=creator)
            
            db.session.add(new_news)
            db.session.commit()
    
def news():
    while True:        
        now = datetime.now()        
        if now.hour == 5 and now.minute == 0 and now.second == 0:
            publish_news()    
            time.sleep(5)    
            print("news updated successfully!!!")

def get_user_input():
    while True:        
        user_input = input("Enter your request \n[ptm : Post Today's Match]\n[md : Matches Data]\n[lvs : livescore]: ")
        if user_input=="news":
            news()                                                                       

def update_db():
    while True:
        news_data = db.session.query(News).all()
        return news_data
        time.sleep(10)

@app.route("/newpage", methods=["POST","GET"])
def newspage():
    news_data = db.session.query(News).all()
    
    if request.method == "POST":
        print("ok")
    else:        
        return render_template("newspage.html", news_data = news_data)
        
if __name__ == '__main__':
    threading.Thread(target=news).start()
    threading.Thread(target=live_update).start()  
    #threading.Thread(target=get_user_input).start()
    socketio.run(app, debug=True)