import Arena
from MCTS import MCTS
# from othello.OthelloGame import OthelloGame
# from othello.OthelloPlayers import *
# from othello.pytorch.NNet import NNetWrapper as NNet

from _chess.ChessGame import ChessGame
from _chess.ChessPlayers import *
from _chess.pytorch.NNet import NNetWrapper as NNet

import numpy as np
from utils import *

"""
use this script to play any two agents against each other, or play manually with
any agent.
"""

human_vs_cpu = True
cpu_vs_stockfish = False


g = ChessGame(8)

# all players
rp = RandomPlayer(g).play
hp = HumanChessPlayer(g).play
sp = StockFishPlayer(g, './_chess/stockfish/stockfish_13_linux_x64_bmi2').play


# nnet players
n1 = NNet(g)

n1.load_checkpoint('./temp/', 'best.pth.tar')

args1 = dotdict({'numMCTSSims': 25, 'cpuct':1.0})
mcts1 = MCTS(g, n1, args1)
n1p = lambda x: np.argmax(mcts1.getActionProb(x, temp=0))


if human_vs_cpu:
    player2 = hp
else:
    player2 = sp

arena = Arena.Arena(n1p, player2, g, display=ChessGame.display)

print(arena.playGames(2, verbose=True))


