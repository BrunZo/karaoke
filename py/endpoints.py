import uuid
from .team import Team, find_team_by_id, find_team_by_name
from .judge import Judge, find_judge_by_id
import py.common as common

def find_presenter_by_id(presenter_id_to_check):
    return common.presenter_id == presenter_id_to_check

def register_team(name):

    if not name:
        return 404, {"error": "Nombre inválido"}

    if find_team_by_name(name):
        return 400, {"error": "El nombre de equipo ya existe"} 

    team = Team(name)
    common.teams.append(team)
    team_id = team.team_id
    return 200, {"message": "success", "team_id": team_id}

def enqueue_team(team_id, timestamp):
    
    def comp(team):
        return len(team.get("team").scores), team.get("timestamp")

    for item in common.queue:
        if item.get("team").team_id == team_id:
            return 400, {"error": "El equipo ya está en la cola"} 

    team = find_team_by_id(team_id)
    if not team:
        return 400, {"error": "Equipo no encontrado"} 

    common.queue.append({"team": team, "timestamp": timestamp})
    common.queue.sort(key=comp)

    return 200, {"message": "Success"}

def dequeue_team():
    
    if common.singer:
        return 400, {"error": "Cantante ya elegido"}
    
    if len(common.queue) == 0:
        return 400, {"error": "La cola está vacía"}
    
    common.singer = common.queue.pop(0).get("team").team_id
    return 200, { "message": "Success" }

def register_judge():

    if len(common.judges) >= common.JUDGES_COUNT:
        return 400, {"error": "Todos los jueces ya están registrados"}

    judge = Judge()
    common.judges.append(judge)
    return 200, {"message": "success"}, {"judge_id": judge.get_id()} 

def send_score(judge_id, score):

    judge = find_judge_by_id(judge_id)
    if not judge:
        return 400, {"error": "Juez no encontrado"} 

    if not common.singer:
        return 400, { "error": "Cantante aún no elegido" }

    common.live_score[judge.num] = score
    return 200, {"message": "Success"}

def register_presenter():

    if common.presenter_id:
        return 400, {"error": "El presentador ya ha sido seleccionado"}

    common.presenter_id = str(uuid.uuid4())
    return 200, {"message": "success"}, {"presenter_id": common.presenter_id}

def commit_scores():

    if not common.singer:
        return 400, {"error": "Cantante no elegido"}
    
    if (any([s == None for s in common.live_score])):
        return 400, {"error": "Esperando puntaje de jueces"}

    team = find_team_by_id(common.singer)
    if not team:
        return 400, {"error": "Equipo no encontrado"} 
    team.add_score(common.live_score)
    common.singer, common.live_score = None, [None, None, None]

    return 200, {"message": "success"}
