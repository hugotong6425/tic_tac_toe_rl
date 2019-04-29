import numpy as np

from keras.models import Model
from keras.layers import Input, Dense
from keras.optimizers import Adam

from .memory import Memory


class Player():
    """
    Abstract player class
    """
    def __init__(self, memory_size=500, player_name=None, player_id=None):
        self.memory = Memory(memory_size)
        self.player_name = player_name
        self.player_id = player_id

    def reset(self, player_id):
        '''reset to the initial state
        '''
        self.player_id = player_id

    @staticmethod
    def tune_observation_view(observation, player_id):
        ''' if player_id is -1, swap the 1 and -1 of the observation
        player_id either 1 or -1. Swap the observation such that 1 means self
        and -1 means the opponent

        Args:
            - observation: np array
            - player_id: int, 1 or -1

        e.g.
        if player_id = 1, no need to swap the view,
        input = array([ 1, -1, 0,
                        0,  0, 0,
                       -1, -1, 1 ])

        output = array([ 1, -1, 0,
                         0,  0, 0,
                        -1, -1, 1 ])

        if player_id = -1, need to swap the view,
        input = array([ 1, -1, 0,
                        0,  0, 0,
                       -1, -1, 1 ])

        output = array([-1, 1, 0,
                         0, 0, 0,
                         1, 1, -1 ])

        '''
        return observation * player_id

    def pick_action(self, **kwargs):
        '''different players have different way to pick an action
        '''
        pass

    def memorize(self, record):
        '''some players will jot notes, some will not
        '''
        self.memory.add(record)

    def learn(self, board, **kwargs):
        '''some players will study, some will not
        '''
        pass

    def get_player_name(self):
        return self.player_name

    def get_player_id(self):
        return self.player_id


class Human(Player):
    '''
    choose this player if you want to play the game
    '''
    def __init__(self, player_name='human player'):
        super(Human, self).__init__()
        self.player_name = player_name

    def pick_action(self, **kwargs):
        cell = input('Pick a cell (top left is 0 and bottom right is 8): \n')
        return int(cell)


class Random_player(Player):
    """
    this player will pick random acion for all situation
    """
    def __init__(self, player_name='random player'):
        super(Random_player, self).__init__()
        self.player_name = player_name

    def pick_action(self, **kwargs):
        possible_action_list = np.argwhere(kwargs['is_action_available'] == 1).reshape([-1])
        return np.random.choice(possible_action_list, 1)[0]


class Q_player(Player):
    def __init__(self, hidden_layers_size, batch_size_learn=32,
                 batch_until_copy=20, saved_nn_path=None, optimizer='adam',
                 loss='mse', player_name='q player'):
        super(Q_player, self).__init__()
        self.hidden_layers_size = hidden_layers_size
        self.batch_size_learn = batch_size_learn
        self.batch_until_copy = batch_until_copy
        self.optimizer = optimizer
        self.loss = loss
        self.player_name = player_name
        self.initialize_neural_network(saved_nn_path)

    def initialize_neural_network(self, saved_nn_path=None):
        '''
        if saved_nn_path is not None, load the model.
        if saved_nn_path is None, initialize the model
        '''
        if saved_nn_path is None:
            x = Input(shape=(9,))

            hidden_result = Dense(self.hidden_layers_size[0], activation='relu',
                                  kernel_initializer='he_normal')(x)
            if len(self.hidden_layers_size) > 1:
                for num_hidden_neurons in self.hidden_layers_size[1:]:
                    hidden_result = Dense(num_hidden_neurons, activation='relu',
                                          kernel_initializer='he_normal')(hidden_result)

            y = Dense(9, activation=None)(hidden_result)

            self.brain = Model(inputs=x, outputs=y)

            self.brain.compile(self.optimizer, loss=self.loss)

        else:
            #self.brain = keras.load_model()
            pass

    def pick_action(self, **kwargs):
        '''given observation and is_action_available, predict the best action

        Args:
            - kwargs['observation']: np array with size [9]
            - kwargs['is_action_available']: np array with size [9]

        Returns:
            - picked_cell: int, 0-8

        Note: can only predict 1 observation at a time now
        '''
        observation = kwargs['observation']
        is_action_available = kwargs['is_action_available']

        tuned_observation = self.tune_observation_view(observation, self.player_id)

        # pick the best action within all possible action given by the board
        q_pred = self.brain.predict(x=tuned_observation.reshape([1, 9])).reshape([-1])
        mask = (is_action_available == 1)
        subset_idx = np.argmax(q_pred[mask])
        picked_cell = np.arange(q_pred.shape[0])[mask][subset_idx]

        return picked_cell
