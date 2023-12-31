import torch.nn as nn
import torch

class QNetwork(nn.Module):

    def __init__(self, ob_dim, ac_dim, hidden_dim = 600):
        
        super().__init__()
        self.linear1 = nn.Linear(ob_dim, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, hidden_dim)
        self.linear3 = nn.Linear(hidden_dim, hidden_dim)
        self.linear4 = nn.Linear(hidden_dim, hidden_dim)
        self.linear5 = nn.Linear(hidden_dim, ac_dim)
        self.activation = nn.ReLU()

    def forward(self, x):        
        return self.linear5(self.activation(self.linear4(self.activation(self.linear3(self.activation(self.linear2(self.activation(self.linear1(x)))))))))

def num_params(module):
    return sum(param.numel() for param in module.parameters())

if __name__ == '__main__':
    network = QNetwork(4, 2)
    print(num_params(network))
    print(network(torch.zeros(4)))