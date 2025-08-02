import uuid
import py.common as common

def avg(l):
    if len(l) == 0:
        return 0
    return sum(l) / len(l)

class Team():

    def __init__(self, name):
        self.team_id = str(uuid.uuid4())
        self.name = name
        self.scores = []

    def get_id(self):
        return self.team_id

    def get_name(self):
        return self.name

    def add_score(self, scores):
        self.scores.append(scores)

    def get_total_score(self):
        return avg([avg(round_scores) for round_scores in self.scores])

def find_team_by_id(team_id):
    for team in common.teams:
        if team.get_id() == team_id:
            return team
    return None

def find_team_by_name(name):
    for team in common.teams:
        if team.get_name() == name:
            return team
    return None


