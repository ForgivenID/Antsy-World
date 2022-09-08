import math
import random as rn
import uuid

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

blob_inputs = ['Light', 'Saltness',
               'Minerals', 'Sine', 'Mass',
               'SenseU', 'SenseD',
               'SenseR', 'SenseL', 'MyY']

blob_outputs = ['Photo', 'MoveU',
                'MoveD', 'MoveR', 'MoveL', 'MoveRNG',
                'Pass', 'SplitR', 'SplitL', 'SplitRNG',
                'SplitU', 'SplitD',
                'EatR', 'EatL',
                'EatU', 'EatD', ]


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
    return round(math.sin(x*t))


def none(x, t):
    return x


activation_funcs = {'step': step, 'nstep': nstep, 'sigm': sigmoid, 'relu': relu, 'nrelu': nrelu, 'timec': timecurve,
                    'none': none}


class Genome:
    def __init__(self, parent=None):
        self.accident_split_chance = 0.001
        if parent is None:
            self.connections = {str: Connection}
            self.connections = {str(uid): Connection(self.connections, str(uid), []) for uid in
                                [uuid.uuid4() for _ in range(START_BRANCHES)]}
            self.input_uids = []
            self.output_uids = []
            self.min_split_age = 10
            self.max_age = 300
            self.capability = 1
            self.max_energy = 150
            self.mutation_rate = 1.5
            self.create()
        else:
            self.min_split_age = parent.min_split_age
            self.mutation_rate = parent.mutation_rate
            self.photosynthesis_efficiency = parent.photosynthesis_efficiency
            self.capability = parent.capability
            self.input_uids = parent.input_uids
            self.output_uids = parent.output_uids
            self.max_energy = parent.max_energy
            self.max_age = parent.max_age
            self.connections = {uid: Connection().from_connection(conn) for uid, conn in parent.connections.items()}
            self.mutate()
        print(self.photosynthesis_efficiency) if self.photosynthesis_efficiency > 6 else None

    def mutate(self):
        if rn.random() < MUTATION_CHANCE * self.mutation_rate:
            split_photo = rn.choices([0, -1, 1], weights=[.6, .15, .15])[0]
            cap_maxenergy = rn.choices([0, -1, 1], weights=[.6, .15, .15])[0]
            if rn.random() < MUTATION_CHANCE:
                if self.mutation_rate < 3:
                    self.mutation_rate += rn.choices([0, 1], weights=[.3, .15])[0]
                elif self.mutation_rate > 0:
                    self.mutation_rate -= rn.choices([0, -1], weights=[.3, .15])[0]
            if rn.random() < MUTATION_CHANCE:
                if self.max_age < 650:
                    self.max_age += rn.choices([0, 1], weights=[.3, .15])[0]
                elif self.max_age > 0:
                    self.max_age -= rn.choices([0, -1], weights=[.3, .15])[0]
            if (1 < self.capability and cap_maxenergy < 0 and self.max_energy < 350) \
                    or (self.capability < 3 and cap_maxenergy > 0 and self.max_energy > 25):
                self.capability += cap_maxenergy
                self.max_energy -= cap_maxenergy * 10
            if (10 < self.min_split_age and split_photo < 0 and self.photosynthesis_efficiency < 6) \
                    or (self.min_split_age < 150 and split_photo > 0 and self.photosynthesis_efficiency > -5):
                self.min_split_age += CHARACTERISTIC_MUTATION_AMPLITUDE * split_photo * self.mutation_rate
                self.photosynthesis_efficiency -= CHARACTERISTIC_MUTATION_AMPLITUDE * split_photo * self.mutation_rate
            for uid, connection in rn.choices(list(self.connections.items()), k=len(self.connections.items()) // 3):
                if rn.random() < FUNC_MUTATION_CHANCE * self.mutation_rate:
                    connection.function = rn.choice(list(activation_funcs.values()))
                for conn_uid in self.connections.keys():
                    if uid != conn_uid:
                        if rn.random() < MUTATION_INPUT_CHANCE:
                            connection.connections_in.append(conn_uid)
                        elif rn.random() < MUTATION_DEGRADATION_CHANCE and len(connection.connections_in) > 0:
                            connection.connections_in.pop(rn.randint(0, len(connection.connections_in) - 1))

    def create(self):
        self.input_uids = rn.choices(blob_inputs, k=START_INPUT_AMOUNT)
        self.output_uids = rn.choices(blob_outputs, k=START_OUTPUT_AMOUNT)
        ids_to_add = self.output_uids + self.input_uids
        # print(ids_to_add)
        self.connections.update({uid: Connection(self.connections, uid, []) for uid in ids_to_add})
        self.mutate()

    def update(self, inputs):
        outputs = {}
        [(conn.reactivate(), conn.set_input(inputs[uid]()) if uid in self.input_uids else None) for uid, conn in
         self.connections.items()]
        [(outputs.update({uid: max(self.connections[uid].update()[0], .01)})) for uid in self.output_uids]
        return outputs


class Connection:
    def __init__(self, connections=None, uid='0', connections_in=None, func=activation_funcs['none']):
        if connections is None:
            connections = []
        if connections_in is None:
            connections_in = []
        self.halted = False
        self.connections_pool = connections
        self.connections_in = connections_in
        self.function = func
        self.uid = uid
        self.weight = 1
        self.last_output = 0
        self.last_input = []
        self.input = 0
        self.activations = 0

    def update(self, actors: list = None):
        if actors is None:
            actors = []
        if self.halted:
            return round(self.last_output, 3), list(actors)
        if self.activations > 1:
            self.input = self.last_input
            for actor in actors:
                actor.halt()
            return round(self.last_output, 3), list(actors)
        else:
            if self.activations == 0:
                self.activations += 1
                if self in actors:
                    self.input = self.last_input
                    for actor in actors:
                        actor.halt()
                    return self.last_output, list(actors)
                self.last_input = []
                for conn in self.connections_in:
                    if conn in self.connections_pool:
                        data = self.connections_pool[conn].update(actors)
                        self.last_input.append(round(data[0], 3) if data[0] is not None else 0)
                        actors.extend(data[1])
                        actors = list(set(actors))
                        continue
                    self.connections_in.remove(conn)
                self.last_input.append(self.input if self.input is not None else 0)
                self.input = 0
                if len(self.last_input) > 0:
                    self.last_output = self.function(((sum(self.last_input) / len(self.last_input)) * self.weight))
            actors.append(self)
            return round(self.last_output, 3), list(actors)

    def from_connection(self, connection):
        self.connections_in = connection.connections_in
        self.function = connection.function
        self.uid = connection.uid
        self.weight = connection.weight
        return self

    def halt(self):
        self.halted = True

    def get_output(self):
        return self.last_output

    def set_input(self, input_value):
        self.input = input_value

    def reactivate(self):
        self.activations = 0
        self.halted = False
