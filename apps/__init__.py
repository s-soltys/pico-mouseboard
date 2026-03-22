from apps.galaxy_app import GalaxyApp
from apps.mines_app import MinesApp
from apps.space_invaders_app import SpaceInvadersApp
from apps.pacman_app import PacmanApp
from apps.arkanoid_app import ArkanoidApp
from apps.tetris_app import TetrisApp


def build_apps():
    return [
        GalaxyApp(),
        MinesApp(),
        SpaceInvadersApp(),
        PacmanApp(),
        ArkanoidApp(),
        TetrisApp(),
    ]
