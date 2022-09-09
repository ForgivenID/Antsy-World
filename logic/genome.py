import copy
import math

MAX_CONN_RECURSION = 4
MAX_GENE = 64
MAX_GENOME = 64
MAX_BRANCHES = 15
START_BRANCHES = 5

START_OUTPUT_AMOUNT = 5
START_INPUT_AMOUNT = 3
START_CONNECTION_CHANCE = .7
START_GENOME_ITERATIONS = .3

BLOB_CREATION_CHANCE = 10
MUTATION_CHANCE = .1  # percents
MUTATION_INPUT_CHANCE = .05
MUTATION_OUTPUT_CHANCE = .05
MUTATION_CONNECTION_CHANCE = .025
WEIGHT_MUTATION_CHANCE = .1
CONNECTION_CREATION_CHANCE = .007
FUNC_MUTATION_CHANCE = .025
MUTATION_DEGRADATION_CHANCE = .001
WEIGHT_MUTATION_AMPLITUDE = .2
CHARACTERISTIC_MUTATION_AMPLITUDE = .1

blob_inputs = []

blob_outputs = []


def sigmoid(x, t):
    return round(1 / (1 + math.exp(-x)), 3)


def nrelu(x, t):
    return round(max(-.5, x), 3)


def relu(x, t):
    return round(max(0, x), 3)


def nstep(x, t):
    return round(-1 if x < -1 else 1, 3)


def step(x, t):
    return round(0 if x < 0 else 1, 3)


def timecurve(x, t):
    return round(math.sin(x * t))


def none(x, t):
    return x


activation_funcs = {'step': step, 'nstep': nstep, 'sigm': sigmoid, 'relu': relu, 'nrelu': nrelu, 'timec': timecurve,
                    'none': none}


class Brain:
    def __init__(self, parent):
        self.connections = {'all': {}, 'input': {}, 'output': {}}

    def update_brain(self):
        pass

    def update_connection(self, uuid):
        pass


class Genome:
    def __init__(self, parent):
        if parent:
            self.modules = {}
            self.modules.update(parent.moules.items())

        else:
            self.modules = {
                'movement': 0,
                'rotation': 0,
                'brain': 1,
                'additional_cpu': 2,
                'pickaxe': 0,
                'sleepy_mode': 0
            }

            self.brain = None


