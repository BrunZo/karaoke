import http.cookies
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from .team import find_team_by_id
from .judge import find_judge_by_id 
from .endpoints import register_team, enqueue_team, dequeue_team
from .endpoints import register_judge, send_score
from .endpoints import register_presenter, commit_scores, find_presenter_by_id
import py.common as common

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

    def _get_cookie(self, cookie_name):
        cookie_header = self.headers.get("Cookie")
        cookies = http.cookies.SimpleCookie(cookie_header)
        return cookies.get(cookie_name)

    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard":
            self._render_page("dashboard")

        elif self.path == "/presenter":
            presenter_id = self._get_cookie("presenter_id")
            if presenter_id and find_presenter_by_id(presenter_id.value):
                self._render_page("dequeue")
            else:
                self._render_page("presenter")

        elif self.path == "/user":
            team_id = self._get_cookie("team_id")
            if team_id and find_team_by_id(team_id.value):
                self._render_page("enqueue")
            else:
                self._render_page("register")
        
        elif self.path == "/judge":
            judge_id = self._get_cookie("judge_id")
            if judge_id and find_judge_by_id(judge_id.value):
                self._render_page("vote")
            else:
                self._render_page("judge")

        elif self.path == "/dequeue":
            presenter_id = self._get_cookie("presenter_id")
            if presenter_id and find_presenter_by_id(presenter_id.value):
                self._render_page("dequeue")
            else:
                self._render_page("presenter")

        elif self.path == "/team_name":
            team_id = self._get_cookie("team_id")
            if team_id and find_team_by_id(team_id.value):
                team = find_team_by_id(team_id.value)
                self._send_json(200, {"name": team.name})
            else:
                self._send_json(400, {"message": "Usuario no registrado"})

        elif self.path == "/teams":
            self._send_json(200, {"teams": [team.name for team in common.teams]})

        elif self.path == "/queue":
            global queue
            self._send_json(200, {"queue": [item.get("team").name for item in common.queue]})

        elif self.path == "/live_score":
            team = find_team_by_id(common.singer)
            if not team:
                self._send_json(200, { "singer": "esperando..." })
            else:
                self._send_json(200, { "singer": team.name, "live_score": common.live_score })

        elif self.path == "/scoreboard":
            self._send_json(200, { "scoreboard": [{
                    "name": team.name,
                    "total_score": round(team.get_total_score(), 2)
                } for team in common.teams]
            })

        else:
            self._send_json(404, {"error": "Página no encontrada"})

    def do_POST(self):

        try:
            content_length = int(self.headers.get("Content-Length"))
            body = self.rfile.read(content_length)
            data = json.loads(body)

        except json.JSONDecodeError:
            self._send_json(400, {"error": "Solicitud inválida"})
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
            team_id = self._get_cookie("team_id")
            if team_id and find_team_by_id(team_id.value):
                timestamp = datetime.now()
                code, data = enqueue_team(team_id.value, timestamp)
                self._send_json(code, data)
            else:
                self._send_json(400, {"message": "Por favor, registrese"})
            
        elif self.path == "/dequeue":
            presenter_id = self._get_cookie("presenter_id")
            if presenter_id and find_presenter_by_id(presenter_id.value):
                code, data = dequeue_team()
                self._send_json(code, data)
            else:
                self._send_json(400, {"error": "Solo el presentador puede desencolar"})


        elif self.path == "/send_score":
            judge_id = self._get_cookie("judge_id")
            score = data.get("score")
            if judge_id and find_judge_by_id(judge_id.value):
                code, data = send_score(judge_id.value, score)
                self._send_json(code, data)
            else:
                self._send_json(400, { "error": "Solo los jueces pueden enviar puntaje" })

        elif self.path == "/commit_scores":
            presenter_id = self._get_cookie("presenter_id")
            if presenter_id and find_presenter_by_id(presenter_id.value):
                code, data = commit_scores()
                self._send_json(code, data)
            else:
                self._send_json(400, {"error": "Solo el presentador puede confirmar puntajes"})
                        
        else:
            self._send_json(404, {"error": "Página no encontrada"})


if __name__ == "__main__":

    server = HTTPServer(("127.0.0.1", 8000), RequestHandler)
    server.serve_forever()