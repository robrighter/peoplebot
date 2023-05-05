import eel


class RobotFaceUI:
    def __init__(self):
        eel.init('web')
        eel.start('index.html', block=False, size=(600, 400))

    def set_eye_direction(self, x, y):
        eel.setEyeDirection(x, y)


