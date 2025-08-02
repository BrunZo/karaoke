import uuid

JUDGES_COUNT = 3
judges = []

class Judge():

    def __init__(self):
        global judges
        self.judge_id = str(uuid.uuid4())
        self.num = len(judges)
        judges.append(self)
   
    def get_id(self):
        return self.judge_id

    def get_num(self):
        return self.num


def find_judge_by_id(judge_id):
    global judges

    for judge in judges:
        if judge.get_id() == judge_id:
            return judge
    return None


