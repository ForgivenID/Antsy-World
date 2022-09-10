import copy
import math
import random as rn
from uuid import uuid4

from misc.ProjSettings import GenomeSettings as settings


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
    def __init__(self, genome, parent=None):
        self.entity = genome.entity
        if parent:
            self.connections = copy.deepcopy(parent.connections)
        else:
            self.connections = {'all': {}, 'input': {}, 'output': {}}
            for c_type in self.entity.sensory_types:
                self.connections['all'][c_type] = {
                    'function': rn.choice(list(activation_funcs.keys())),
                    'preset': None,
                    'fired': False,
                    'inputs': [],
                    'weights': {},
                    'dead': False
                }
                self.connections['input'][c_type] = self.connections['all'][c_type]
            for c_type in self.entity.reactivity_types:
                self.connections['all'][c_type] = {
                    'function': rn.choice(list(activation_funcs.keys())),
                    'preset': None,
                    'fired': False,
                    'inputs': [],
                    'weights': {},
                    'dead': False
                }
                self.connections['output'][c_type] = self.connections['all'][c_type]
            for _ in range(settings.starting_brain_axons):
                self.connections['all'][str(uuid4().int)] = {
                    'function': rn.choice(list(activation_funcs.keys())),
                    'preset': None,
                    'fired': False,
                    'inputs': [],
                    'weights': {},
                    'dead': False
                }
            self.mutate()

    def mutate(self):
        if settings.new_axon_mutation >= rn.random() and len(self.connections['all']) < settings.max_brain_axons:
            connection = rn.choice(list(self.connections['all'].values()))
            c_uuid = rn.choice(list(self.connections['all'].keys()))
            if c_uuid not in connection['inputs']:
                connection['inputs'].append(c_uuid)
                connection['weights'][c_uuid] = rn.random() * 8 - 4
        if settings.axon_degeneration >= rn.random():
            connection = rn.choice(list(self.connections['all'].values()))
            connection['died'] = True
        if settings.function_mutation >= rn.random():
            connection = rn.choice(list(self.connections['all'].values()))
            connection['function'] = rn.choice(list(activation_funcs.keys()))
        if settings.weight_mutation >= rn.random():
            connection = rn.choice(list(self.connections['all'].values()))
            if len(list(connection['weights'].keys())) > 0:
                c_uuid = rn.choice(list(connection['weights'].keys()))
                connection['weights'][c_uuid] = rn.random() * 10 - 5


    def update_brain(self):
        self.set_inputs()
        outputs = {}
        for connection in self.connections['all'].values():
            connection['fired'] = False
        for action in self.connections['output'].keys():
            outputs[action] = self.update_connection(action)
        outputs['halt'] = 0.001
        keys = list(outputs.keys()) + ['halt']
        self.entity.perform(rn.choices(keys, [outputs[key] for key in keys]))

    def set_inputs(self):
        for sense in self.connections['input'].keys():
            self.connections['all'][sense]['preset'] = self.entity.get_sensory_val(sense)

    def update_connection(self, uuid, chain=None):
        if chain is None:
            chain = []
        inputs = 0
        connection = self.connections['all'][uuid]
        if uuid in chain or connection['fired']:
            return connection['last_output']
        if connection['preset'] is not None:
            connection['preset'] = None
            connection['fired'] = True
            output = activation_funcs[connection['function']](connection['preset'])
            connection['last_output'] = output
            return output
        connection['fired'] = True
        for c_uuid in connection['inputs']:
            if self.connections['all'][c_uuid]['died']:
                connection['inputs'].remove(c_uuid)
            inputs += self.update_connection(c_uuid, chain) * connection['weights'][c_uuid]
        output = activation_funcs[connection['function']](inputs, self.entity.age)
        connection['last_output'] = output
        return output


class Genome:
    def __init__(self, entity, parent=None):
        self.entity = entity
        if parent:
            self.modules = copy.deepcopy(parent.moules.items())
            self.brain = Brain(parent.brain)
            self.ant_brains = [Brain(brain) for brain in parent.ant_brains]

        else:
            self.modules = {
                'movement': 0,
                'rotation': 0,
                'brain': 1,
                'additional_cpu': 2,
                'pickaxe': 0,
                'sleepy_mode': 0,
                'exploration': 0,
            }

            self.brain = Brain(self)
