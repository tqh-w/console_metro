import time
import os
import keyboard
import pygame

TEXT_COLORS = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'purple': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    None: '\033[0m',

    '\033[30m': 'black',
    '\033[31m': 'red',
    '\033[32m': 'green',
    '\033[33m': 'yellow',
    '\033[34m': 'blue',
    '\033[35ь': 'purple',
    '\033[36m': 'cyan',
    '\033[37': 'white',
    '\033[0m': None,
}

TRAINS = []
LIGHTS = {}


class train:

    def __init__(self, length=5, head=0, color='blue', mx_speed=2, ai=True):
        self.length = length
        self.head = head
        self.color = color
        self.mx_speed = mx_speed
        self.ai = ai

        self.symbol = TEXT_COLORS[color] + '▉' + TEXT_COLORS[None]
        self.m = .3 * self.length

        self.speed = 0
        self.f = 0
        self.broken = False

        TRAINS.append(self)

    def set_f(self, f):
        if self.broken or f == self.f:
            return

        play_sound('audio/switch.mp3')
        self.f = f

    def boom(self):
        self.broken = True
        self.symbol = TEXT_COLORS['red'] + '▉' + TEXT_COLORS[None]
        self.color = 'red'
        self.speed = 0
        self.f = 0
        play_sound('audio/boom.wav')


class light:

    def __init__(self, position, color='red', ai=True):
        global line
        self.position = position
        self.color = color
        self.ai = ai

        line[position] = TEXT_COLORS[self.color] + '#' + TEXT_COLORS[None]
        LIGHTS[position] = self

    def set(self, color='red'):
        global line

        self.color = color
        line[self.position] = TEXT_COLORS[self.color] + '#' + TEXT_COLORS[None]


def play_sound(sound_file):
    pygame.mixer.init()
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()


def get_cell(position, line):
    position = round(position)

    if position >= len(line):
        return

    e = line[position]
    if e == '=':
        return 'rail'

    if '\033' in e:
        e = e[e.find('m') + 1:].replace('\033[0m', '')

        if e == '#' and position in LIGHTS:
            return LIGHTS[position]
        elif e == '▉':
            for t in TRAINS:
                if t.head - t.length <= position <= t.head:
                    return t


def tick():
    global line
    current_line = line[:]

    for t in TRAINS:
        # просчет новой скорости
        f = t.f - .1 * t.speed
        a = f / t.m
        t.speed += a
        if t.speed < 0:
            t.speed = 0

        # автоматическое управление поездом
        if t.ai:
            red = TEXT_COLORS['red'] + '#' + TEXT_COLORS[None]
            f = .2
            S = round((t.speed ** 2) / (2 * (f / t.m))) + 3
            if red in line[round(t.head) + 1:round(t.head) + S] and t.speed != 0:
                t.set_f(-.2)
            elif t.f == -.2 and red not in line[round(t.head) + 1:round(t.head) + S] and t.speed != 0:
                t.set_f(.2)
            elif t.speed == 0 and red in line[round(t.head):round(t.head) + 5]:
                t.set_f(0)
            elif t.speed == 0 and red not in line[round(t.head):round(t.head) + 5]:
                t.set_f(.2)

        # перемещение поезда
        t.head = (t.head + t.speed) % len(line)

        train_range = range(round(t.head) - t.length + 1, round(t.head) + 1)
        for i in train_range:
            current_line[i % len(line)] = t.symbol

    # проверяем аварии
    for t in TRAINS:
        if type(get_cell(t.head + 1, current_line)) is train and t.speed != 0:
            get_cell(t.head + 1, current_line).boom()
            t.boom()

    # автоматическое управление светофорами
    for k, l in LIGHTS.items():
        if not l.ai:
            continue
        r = (current_line * 2)[k:k + l_delay]
        for e in r:
            if '▉' in e:
                l.set('red')
                break
        else:
            l.set('green')

    return current_line


# НАСТРОЙКИ
# создание линии
line = ['='] * 151

# установка светофоров
l_delay = 30
[light(i) for i in range(l_delay, len(line), l_delay)]

# создание поездов
t1 = train(3, 25, ai=False)

# назначение клавиш
ka = {
    'q': lambda: t1.set_f(-.2),
    'w': lambda: t1.set_f(-.1),
    'e': lambda: t1.set_f(0),
    'r': lambda: t1.set_f(.1),
    't': lambda: t1.set_f(.2),
    'y': lambda: t1.set_f(-.5)
}
[keyboard.add_hotkey(k, v) for k, v in ka.items()]

# станции
station_len = 10
print('\n')
[print(' ' * (2 * (l_delay - station_len) + station_len) + '▉' * station_len, end='') for _ in
 range(len(line) // l_delay // 2)]
print()

if 'audio' not in os.listdir() or ('boom.wav' not in os.listdir('audio') and
                                   'emergency.wav' not in os.listdir('audio') and
                                   'light.wav' not in os.listdir('audio') and
                                   'switch.wav' not in os.listdir('audio')):
    print('Не удалось найти аудио файлы')
    exit()

while True:
    cl = tick()

    # экстренное торможение
    if t1.f == -.5:
        if t1.speed != 0:
            play_sound('audio/emergency.wav')
        else:
            t1.set_f(0)

    # отображение
    text = '\r' + ''.join(cl)
    for t in TRAINS:
        text += f' {TEXT_COLORS[t.color]} {round(t.speed, 1 * 2)} яч/с ({t.f}){TEXT_COLORS[None]}'
    print(text, end='')

    time.sleep(.5)
