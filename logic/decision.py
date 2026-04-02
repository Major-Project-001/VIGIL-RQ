from config.settings import LEFT_THRESHOLD, RIGHT_THRESHOLD

def get_direction(nose_x):
    """
    Converts nose x-coordinate into a directional command.
    nose_x is expected to be a normalized coordinate (0.0 to 1.0).
    """
    if nose_x is None:
        return "CENTER" # Default or fallback

    if nose_x < LEFT_THRESHOLD:
        return "LEFT"
    elif nose_x > RIGHT_THRESHOLD:
        return "RIGHT"
    else:
        return "CENTER"
