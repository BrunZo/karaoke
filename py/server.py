import http.cookies
import uuid
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

JUDGES_COUNT = 3

def avg(l):
    if len(l) == 0:
        return 0
    return sum(l) / len(l)

def find_team_by_id(team_id):
    global teams
    for team in teams:
        if team.team_id == team_id:
            return team
    return None

def find_team_by_name(name):
    global teams
    for team in teams:
        if team.name == name:
            return team
    return None

def register_team(name):
    global teams

    if not name:
        return 404, {"error": "Invalid name"}

    if find_team_by_name(name):
        return 400, {"error": "Team name already exists"} 

    team = Team(name)
    teams.append(team)
    team_id = team.team_id
    return 200, {"message": "success", "team_id": team_id}

def enqueue_team(team_id, timestamp):
    global teams, queue

    def comp(team):
        return len(team.get("team").scores), team.get("timestamp")

    for item in queue:
        if item.get("team").team_id == team_id:
            return 400, {"error": "Team already in queue"} 

    team = find_team_by_id(team_id)
    if not team:
        return 400, {"error": "Team not found"} 

    queue.append({"team": team, "timestamp": timestamp})
    queue.sort(key=comp)

    return 200, {"message": "Success"}

def commit_scores():
    global singer, live_score

    if not singer:
        return 400, {"error": "Singer not chosen"}
    
    if (any([s == None for s in live_score])):
        return 400, {"error": "Waiting for judge score"}

    team = find_team_by_id(singer)
    if not team:
        return 400, {"error": "Team not found"} 
    team.add_score(live_score)

    return 200, {"score": live_score}

class Team():

    def __init__(self, name):
        self.team_id = str(uuid.uuid4())
        self.name = name
        self.scores = []

    def add_score(self, scores):
        assert len(scores) == JUDGES_COUNT
        self.scores.append(scores)

    def get_total_score(self):
        return avg([avg(round_scores) for round_scores in self.scores])


class RequestHandler(BaseHTTPRequestHandler):

    def _send_json(self, code, data, cookies={}):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for key in cookies:
            self.send_header("Set-Cookie", f"{key}={cookies[key]}; Path=/; HttpOnly")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _render_page(self, file):
        try:
            url = "html/" + file + ".html"
            with open(url, "rb") as f:
                content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset: utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except Exception as e:
            self._send_json(404, {"error": e})

    def do_GET(self):
        global teams

        if self.path == "/" or self.path == "/dashboard":
            self._render_page("dashboard")

        elif self.path == "/presenter":
            # check if request has cookie
            self._render_page("presenter")

        elif self.path == "/user":
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            team_id = cookies.get("team_id")
            if team_id and find_team_by_id(team_id.value):
                self._render_page("enqueue")
            else:
                self._render_page("register")
        
        elif self.path == "/jury":
            # check if request has cookie
            self._render_page("jury")

        elif self.path == "/team_name":
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            team_id = cookies.get("team_id")
            if team_id and find_team_by_id(team_id.value):
                team = find_team_by_id(team_id.value)
                self._send_json(200, {"name": team.name})
            else:
                self._send_json(400, {"message": "Please register"})

        elif self.path == "/teams":
            self._send_json(200, {"teams": [team.name for team in teams]})

        elif self.path == "/queue":
            global queue
            self._send_json(200, {"queue": [item.get("team").name for item in queue]})

        elif self.path == "/live_score":
            global singer, live_score

            team = find_team_by_id(singer)
            if not team:
                self._send_json(200, { "singer": "esperando..." })
            else:
                self._send_json(200, {
                    "singer": team.name,
                    "live_score": live_score
                })

        elif self.path == "/scoreboard":
            self._send_json(200, {
                "scoreboard": [{
                    "name": team.name,
                    "total_score": round(team.get_total_score(), 2)
                } for team in teams]
            })

        else:
            self._send_json(404, {"error": "Page not found"})

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length"))
            body = self.rfile.read(content_length)
            data = json.loads(body)

        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid request"})
            return

        if self.path == "/register":
            name = data.get("name")
            code, data = register_team(name)
            self._send_json(code, data, cookies={"team_id": data.get("team_id")})

        elif self.path == "/enqueue":
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            team_id = cookies.get("team_id")
            if team_id and find_team_by_id(team_id.value):
                timestamp = datetime.now()
                code, data = enqueue_team(team_id.value, timestamp)
                self._send_json(code, data)
            else:
                self._send_json(400, {"message": "Please register"})
            
        elif self.path == "/dequeue":
            global queue, singer

            if singer:
                self._send_json(400, {"error": "Singer already chosen"})
                return

            if len(queue) == 0:
                self._send_json(400, {"error": "Empty queue"})
                return

            singer = queue.pop(0).get("team").team_id
            self._send_json(200, {"singer": singer})

        elif self.path == "/send_score":
            global live_score
            jury = data.get("jury")
            score = data.get("score")
            live_score[jury] = score
            self._send_json(200, {"message": "Success"})

        elif self.path == "/commit_scores":
            code, data = commit_scores()
            self._send_json(code, data)
            singer = None
            live_score = [None, None, None]
            
        else:
            self._send_json(404, {"error": "Page not found"})


if __name__ == "__main__":

    teams = []
    queue = []
    singer = None
    live_score = [None] * JUDGES_COUNT

    server = HTTPServer(("127.0.0.1", 8000), RequestHandler)
    server.serve_forever()

