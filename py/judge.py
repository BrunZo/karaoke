import uuid
import py.common as common

class Judge():

    def __init__(self):
        self.judge_id = str(uuid.uuid4())
        self.num = len(common.judges)
   
    def get_id(self):
        return self.judge_id

    def get_num(self):
        return self.num


def find_judge_by_id(judge_id):

    for judge in common.judges:
        if judge.get_id() == judge_id:
            return judge
    return None


