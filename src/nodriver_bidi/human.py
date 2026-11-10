"""Timings and trajectories that look like a person at the mouse and keyboard."""

import math
import random

_random = random.Random()

SHIFT = ""
ENTER = ""
_SHIFTED = set('~!@#$%^&*()_+{}|:"<>?')


def between(low: float, high: float) -> int:
    return round(_random.uniform(low, high))


def resting_point(width: int, height: int) -> tuple[int, int]:
    return between(width * 0.2, width * 0.8), between(height * 0.2, height * 0.8)


def mouse_path(
    start: tuple[float, float], end: tuple[float, float], target_size: float, bounds: tuple[int, int]
) -> list[tuple[int, int, int]]:
    """Points (x, y, milliseconds since the previous one) of a hand moving the mouse from start to end.

    The stroke curves, speeds up and slows down (minimum jerk), lasts what Fitts's law predicts for its
    length and the target's size, trembles slightly and, when long, sometimes overshoots and comes back.
    """
    distance = math.dist(start, end)
    if distance > 250 and _random.random() < 0.3:
        overshoot = _random.uniform(4, 14) / distance
        beyond = (
            end[0] + (end[0] - start[0]) * overshoot + _random.uniform(-3, 3),
            end[1] + (end[1] - start[1]) * overshoot + _random.uniform(-3, 3),
        )
        path = _stroke(start, beyond, target_size) + _stroke(beyond, end, target_size * 2)
    else:
        path = _stroke(start, end, target_size)
    width, height = bounds
    return [(min(max(x, 0), width - 1), min(max(y, 0), height - 1), ms) for x, y, ms in path]


def _stroke(start: tuple[float, float], end: tuple[float, float], target_size: float) -> list[tuple[int, int, int]]:
    distance = math.dist(start, end)
    if distance < 1:
        return [(round(end[0]), round(end[1]), between(8, 20))]
    duration = (80 + 140 * math.log2(1 + distance / max(target_size, 4))) * _random.uniform(0.8, 1.25)
    normal = ((start[1] - end[1]) / distance, (end[0] - start[0]) / distance)
    # Mostly an arc bowing to one side, as an arm pivoting at the elbow draws; sometimes an S.
    side = _random.choice((-1, 1))
    bend = min(distance * _random.uniform(0.05, 0.25), 150)

    def control(fraction: float, same_side: bool) -> tuple[float, float]:
        offset = bend * _random.uniform(0.6, 1.4) * (side if same_side else -side)
        return (
            start[0] + (end[0] - start[0]) * fraction + normal[0] * offset,
            start[1] + (end[1] - start[1]) * fraction + normal[1] * offset,
        )

    c1 = control(_random.uniform(0.2, 0.4), True)
    c2 = control(_random.uniform(0.6, 0.8), _random.random() > 0.2)
    steps = max(4, round(duration / _random.uniform(14, 18)))  # about one mousemove per frame
    path: list[tuple[int, int, int]] = []
    elapsed = 0
    for i in range(1, steps + 1):
        t = i / steps
        u = t**3 * (10 - 15 * t + 6 * t**2)
        x, y = _bezier(start, c1, c2, end, u)
        if i < steps:
            x, y = x + _random.gauss(0, 0.5), y + _random.gauss(0, 0.5)
        point = (round(x), round(y))
        if i < steps and path and point == path[-1][:2]:
            continue
        ms = round(duration * t)
        path.append((*point, ms - elapsed))
        elapsed = ms
    return path


def _bezier(p0, p1, p2, p3, u: float) -> tuple[float, float]:
    a, b, c, d = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u**2, u**3
    return a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]


def keystrokes(text: str) -> list[tuple[str, int, int]]:
    """(character, milliseconds held down, pause before the next one) for typing `text`."""
    strokes = []
    for char in text:
        pause = _random.lognormvariate(math.log(105), 0.35)
        if not char.isalnum():
            pause *= 1.4
        if _random.random() < 0.04:
            pause += _random.uniform(250, 700)
        strokes.append((char, between(45, 115), round(pause)))
    return strokes


def needs_shift(char: str) -> bool:
    return char in _SHIFTED or char != char.lower()


def wheel_steps(distance: int) -> list[tuple[int, int]]:
    """(deltaY, pause after it) for scrolling `distance` pixels in wheel notches."""
    steps = []
    remaining, sign = abs(distance), 1 if distance > 0 else -1
    while remaining > 0:
        delta = min(remaining, between(80, 130))
        remaining -= delta
        steps.append((sign * delta, between(150, 400) if _random.random() < 0.15 else between(25, 90)))
    return steps


def dialog_time(message: str, text: str | None = None) -> int:
    """Milliseconds a person takes to answer a dialog: notice it, read it, type `text` if any, click."""
    reading = between(450, 900) + 35 * min(len(message), 120)
    typing = sum(hold + pause for _, hold, pause in keystrokes(text)) if text else 0
    return reading + typing + between(150, 350)


def key_actions(text: str, humanize: bool) -> list[dict]:
    """BiDi key actions for `text`, holding Shift for capitals and symbols like a keyboard would."""
    actions: list[dict] = [_pause(between(150, 450))] if humanize else []
    shifted = False
    for char, hold, pause in keystrokes(text) if humanize else [(c, 0, 0) for c in text]:
        if needs_shift(char) != shifted:
            shifted = not shifted
            actions.append({"type": "keyDown" if shifted else "keyUp", "value": SHIFT})
            if humanize:
                actions.append(_pause(between(25, 70)))
        key = ENTER if char == "\n" else char
        actions.append({"type": "keyDown", "value": key})
        if hold:
            actions.append(_pause(hold))
        actions.append({"type": "keyUp", "value": key})
        if pause:
            actions.append(_pause(pause))
    if shifted:
        actions.append({"type": "keyUp", "value": SHIFT})
    return actions


def click_actions(humanize: bool) -> list[dict]:
    down, up = {"type": "pointerDown", "button": 0}, {"type": "pointerUp", "button": 0}
    if not humanize:
        return [down, up]
    return [_pause(between(70, 220)), down, _pause(between(50, 130)), up]


def _pause(ms: int) -> dict:
    return {"type": "pause", "duration": ms}
