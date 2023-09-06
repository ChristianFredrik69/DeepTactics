import numpy as np
from collections import defaultdict
import sys
import torch

# torch.set_default_tensor_type('torch.cuda.FloatTensor')

# The self-made environment for Easy21.
sys.path.append('PracticalRL/Easy21Assignment')
from Environment import Easy21Environment

# Importing function which provides cartesian product:
from itertools import product

# Import for plotting the state-value-function:
import matplotlib.pyplot as plt

# Importing pickle so i can load the action-value function from Monte-Carlo.
import pickle

class LinearFunctionApproximationControl:
    
    def __init__(self, env, gamma = 1.0, lamb = 0.5, epsilon = 0.05, alpha = 0.01):
        
        # We are using the Easy21-environment.
        self.env = env

        # In this task, we are setting the discount factor to 1.
        self.gamma = gamma

        # Setting up lambda to be the specified value:
        self.lamb = lamb
        
        # Epsilon and alpha are set to be constant:
        self.epsilon = epsilon
        self.alpha = alpha

        # Intializing some weights, One weight for each feature:
        self.w = torch.zeros((18, 2))
    

    def learn_episode(self):
        """
        Generates an episode and updates the action-value function for each step taken.
        The updates are made according to the backward-view TD-Sarsa algorithm.
        """
        
        # Env.reset() simply returns the initial state.
        state = self.env.reset()
        action = self.get_action(state)
        
        # Getting the feature vector representation of our state-action pair:
        feature_vector = self.get_feature_vector(state)

        # Initializing the eligibility trace:
        E = torch.zeros((18, 2))

        while True:
            
            # We take a step in the environment and see what happens. 
            next_state, reward, done = self.env.step(action); 

            # We sample our next action according to our epsilon-greedy policy:
            next_action = self.get_action(state)

            # We must remember to represent the next state, next action pair as a feature vector.
            next_feature_vector = self.get_feature_vector(next_state)

            # Updating the eligibility trace:
            E.mul_(self.lamb * self.gamma)
            E[:, action] += feature_vector
            

            if done:
                
                # Some update to the action-value function.
                # Only the action-values in the eligibility trace should be updated.
                # We don't calculate the usual TD-error, as there is no next_action to take here.

                # The dot product between feature vector and the weights essentially gives us the approximated q-value.
                self.w.add_(E.mul_(self.alpha * (reward - self.get_qvalue(state, action))))

                # Jumping out of the training episode.
                break
            
            # Some TD-update to the action-value function:
            # This is for the usual case where we are not in the terminal state yet,
            # so we update our action-value function based on usual TD-error.
            self.w.add_(E.mul_(self.alpha * (reward + self.get_qvalue(next_state, next_action) - self.get_qvalue(state, action))))

            # Setting up for next action:
            state, action, feature_vector = next_state, next_action, next_feature_vector

    def get_feature_vector(self, state):
        """
        Takes in a state-pair of the form (dealer_sum, player_sum, action).
        and returns a 1D vector with 36 entries, where each entry corresponds to some specific feature.
        """

        # Setting up the feature vector:
        feature_vector = torch.zeros(18)

        # Extracting the useful information for the features:
        dealer_sum = state[0]
        player_sum = state[1]

        # Defining the features:
        dealer_ranges = [(1, 4), (4, 7), (7, 10)]
        player_ranges = [(1, 6), (4, 9), (7, 12), (10, 15), (13, 18), (16, 21)]

        for i, (d_range, p_range) in enumerate(product(dealer_ranges, player_ranges)):
            if d_range[0] <= dealer_sum <= d_range[1] and p_range[0] <= player_sum <= p_range[1]:
                feature_vector[i] = 1
        
        return feature_vector

    def get_action(self, state):
        """
        Decides which action we should take in a state, according to our policy.
        Our policy is epsilon-greedy with a constant epsilon. 
        Standard value for epsilon is 0.05
        """

        if (np.random.rand() < self.epsilon):
            return np.random.randint(self.env.action_space.n)

        else:
            return torch.argmax(torch.tensor([self.get_qvalue(state, a) for a in range(self.env.action_space.n)])).item()

    def get_qvalue(self, state, action):
        return torch.matmul(self.get_feature_vector((state[0], state[1])), self.w)[action]
    
    def get_action_values(self):
        """
        Returns the action values which the agent has found:
        """
        q = defaultdict(lambda: torch.zeros(self.env.action_space.n))
        dealer = [i for i in range(1, 11)]
        player = [i for i in range(1, 22)]
        states = product(dealer, player)

        for state in states:
            for action in range(self.env.action_space.n):
                q[state][action] = self.get_qvalue(state, action)

        return q

    def get_policy(self):
        """
        Returns the current policy based on the action-value function.
        """
        policy = defaultdict(int)
        dealer = [i for i in range(1, 11)]
        player = [i for i in range(1, 22)]
        states = product(dealer, player)

        for state in states:
            policy[state] = torch.argmax(torch.tensor([self.get_qvalue(state, a) for a in range(self.env.action_space.n)])).item()

        return policy

    def learn(self, num_episodes):
        """
        Executes a number of episodes of on-policy learning through sampling.
        Returns:
            1) The optimal policy as a dictionary with state and action.
        """
        for i in range(1, num_episodes + 1):
            
            self.learn_episode()

            if (i % 1000 == 0):
                print(i)
        
        return self.get_policy()
       
    def learn_with_mse(self, num_episodes, q_star):
        """
        Executes a number of episodes of on-policy learning through sampling.
        Returns:
            1) The optimal policy as a dictionary with state and action.
            2) A list containing the MSE-values for each time step.
        """
        mse_values = []

        for i in range(1, num_episodes + 1):
            
            self.learn_episode()
            mse_values.append(LinearFunctionApproximationControl.compute_mse(self, q_star))

            if (i % 100 == 0):
                print(i)
        
        return self.get_policy(), mse_values

    def plot_mse(q_star, num_episodes = 1_000):
        
        # Setting up the agents
        agent0 = LinearFunctionApproximationControl(Easy21Environment(), lamb = 0)
        agent1 = LinearFunctionApproximationControl(Easy21Environment(), lamb = 1)

        # Finding the list of calculated MSE for each episode
        _, mse0 = agent0.learn_with_mse(num_episodes, q_star)
        _, mse1 = agent1.learn_with_mse(num_episodes, q_star)

        fig = plt.figure(figsize = (12, 6))

        ax = fig.add_subplot(111)

        ax.plot(mse0, label = 'λ = 0')
        ax.plot(mse1, label = 'λ = 1')

        ax.set_xlabel('Episodes')
        ax.set_ylabel('Mean Squared Error')
        ax.set_title('MSE between Linear Function Approximation and Q*')

        ax.legend()

        plt.show()

    def compute_mse(agent, q_star):
        """
        Simple method which calculates the mean-square error between two action-value functions.
    
        Parameter:
            q_star (dict): The optimal action-value function, which in our case is obtained from Monte Carlo control.
        """
        return sum( (agent.get_qvalue(state, action).item() - q_star[state][action])**2 for state in q_star for action in range(len(q_star[state] ))) / ( len(q_star) * agent.env.action_space.n)

    def plot_error_lambda(mc_action_value, num_episodes = 1000):
        """
        Plotting the MSE for different values of lambda.
        The lambdas which are used are in range [0, 1] with step size 0.1
        """        
        mse_values = []
        for i in range(11):
            agent = LinearFunctionApproximationControl(Easy21Environment(), lamb = i / 10)
            agent.learn(num_episodes)    
            MSE = LinearFunctionApproximationControl.compute_mse(agent, mc_action_value)
            mse_values.append([i/10, MSE])
        
        fig = plt.figure(figsize = (12, 6))
        ax = fig.add_subplot(111)
        
        lambdas, mse_values = zip(*mse_values)
        ax.plot(lambdas, mse_values, marker='o')

        ax.set_xlabel("Lambda")
        ax.set_ylabel("MSE")
        ax.set_title("MSE for different values of lambda:")
        ax.grid(True)

        plt.show()

    

with open("PracticalRL\Pickle\MonteCarloActionValue.pkl", "rb") as f:
    mc_action_value = pickle.load(f)


# LinearFunctionApproximationControl.plot_mse(mc_action_value, num_episodes = 1000)

# with torch.profiler.profile() as prof:
#     LinearFunctionApproximationControl.plot_error_lambda(mc_action_value, num_episodes = 100)


# print(prof.key_averages().table(sort_by="cpu_time_total"))
# print(prof.key_averages().table(sort_by="cuda_time_total"))
# LinearFunctionApproximationControl.plot_error_lambda(mc_action_value, num_episodes = 10_000)
LinearFunctionApproximationControl.plot_mse(mc_action_value, num_episodes = 10_000)