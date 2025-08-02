import uuid
from .team import Team, teams, queue, find_team_by_id, find_team_by_name
from .judge import Judge, judges, JUDGES_COUNT

singer = None
live_score = [None] * JUDGES_COUNT
presenter_id = None

def find_presenter_by_id(presenter_id_to_check):
    global presenter_id
    return presenter_id == presenter_id_to_check

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

def dequeue_team():
    pass

def register_judge():
    global judges

    if len(judges) >= JUDGES_COUNT:
        return 400, {"error": "All judges are already registered"}

    judge = Judge()
    judges.append(judge)
    return 200, {"message": "success"}, {"judge_id": judge.get_id()} 

def send_score():
    pass

def register_presenter():
    global presenter_id

    if presenter_id:
        return 400, {"error": "Presenter has already been selected"}

    presenter_id = str(uuid.uuid4())
    return 200, {"message": "success"}, {"presenter_id": presenter_id}

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
