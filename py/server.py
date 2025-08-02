import http.cookies
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from .team import teams, queue, find_team_by_id
from .judge import find_judge_by_id
from .endpoints import register_team, enqueue_team, register_judge, register_presenter, commit_scores, singer, live_score, find_presenter_by_id

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
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            presenter_id = cookies.get("presenter_id")
            if presenter_id and find_presenter_by_id(presenter_id.value):
                self._render_page("dequeue")
            else:
                self._render_page("presenter")

        elif self.path == "/user":
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            team_id = cookies.get("team_id")
            if team_id and find_team_by_id(team_id.value):
                self._render_page("enqueue")
            else:
                self._render_page("register")
        
        elif self.path == "/judge":
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            judge_id = cookies.get("judge_id")
            if judge_id and find_judge_by_id(judge_id.value):
                self._render_page("vote")
            else:
                self._render_page("judge")

        elif self.path == "/dequeue":
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            presenter_id = cookies.get("presenter_id")
            if presenter_id and find_presenter_by_id(presenter_id.value):
                self._render_page("dequeue")
            else:
                self._render_page("presenter")

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

        elif self.path == "/judge":
            code, data, cookies = register_judge()
            self._send_json(code, data, cookies=cookies)

        elif self.path == "/presenter":
            code, data, cookies = register_presenter()
            self._send_json(code, data, cookies=cookies)

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

            # Check for presenter authentication
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            presenter_id = cookies.get("presenter_id")
            if not presenter_id or not find_presenter_by_id(presenter_id.value):
                self._send_json(400, {"error": "Only presenter can dequeue"})
                return

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

            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            judge_id = cookies.get("judge_id")
            if judge_id and find_judge_by_id(judge_id.value):
                judge = find_judge_by_id(judge_id.value)

                if not singer:
                    self._send_json(400, { "error": "Singer not chosen" })
                    return

                live_score[judge.num] = data.get("score")
                self._send_json(200, {"message": "Success"})

            else:
                self._send_json(400, { "error": "Only judges can send score" })

        elif self.path == "/commit_scores":
            # Check for presenter authentication
            cookie_header = self.headers.get("Cookie")
            cookies = http.cookies.SimpleCookie(cookie_header)
            presenter_id = cookies.get("presenter_id")
            if not presenter_id or not find_presenter_by_id(presenter_id.value):
                self._send_json(400, {"error": "Only presenter can commit scores"})
                return

            code, data = commit_scores()
            self._send_json(code, data)
            singer = None
            live_score = [None, None, None]
            
        else:
            self._send_json(404, {"error": "Page not found"})


if __name__ == "__main__":
    
    server = HTTPServer(("127.0.0.1", 8000), RequestHandler)
    server.serve_forever()

