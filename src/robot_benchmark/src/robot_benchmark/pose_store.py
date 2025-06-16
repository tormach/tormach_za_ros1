import pickle


class PoseStore:
    FILE_NAME = 'poses.dump'

    def __init__(self):
        pass

    def dump(self, poses):
        with open(self.FILE_NAME, 'wb') as f:
            pickle.dump(poses, f)

    def load(self):
        with open(self.FILE_NAME, 'rb') as f:
            return pickle.load(f)
