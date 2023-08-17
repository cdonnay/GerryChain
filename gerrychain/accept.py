from .random import random
from gerrychain.partition import Partition
from typing import Callable

def always_accept(partition: Partition) -> bool:
    return True

def swap_county_accept(partition: Partition,
                 ell: float = 1) -> bool:
    """ Implements Metropolis/Hastings Hill climber for number of violation to Ohio county rules.
    If the new map decreases the number of violations, move there.
    If it increases, move with probability proportional to increase.

    :param ell: float, the metropolis constant, larger values move distribution towards global max/min

    Requires that partitions have the "swap_ohio_county_violations" updater.
    """

    bound = 1.0

    if partition.parent is not None:
        parent_score = sum(partition.parent["swap_ohio_county_violations"])
        new_score = sum(partition["swap_ohio_county_violations"])
        bound = min(1,  ell**(parent_score-new_score))

    return random.random() < bound

def recom_county_accept(partition: Partition,
                 ell: float = 1) -> bool:
    """ Implements Metropolis/Hastings Hill climber for number of violation to Ohio county rules.
    If the new map decreases the number of violations, move there.
    If it increases, move with probability proportional to increase.

    :param ell: float, the metropolis constant, larger values move distribution towards global max/min

    Requires that partitions have the "recom_ohio_county_violations" updater.
    """

    bound = 1.0

    if partition.parent is not None:
        parent_score = sum(partition.parent["recom_ohio_county_violations"])
        new_score = sum(partition["recom_ohio_county_violations"])
        bound = min(1,  ell**(parent_score-new_score))

    return random.random() < bound

def simulated_annealing_recom_county_accept(partition: Partition,
                 temperature_schedule: Callable,
                 counter: int) -> bool:
    """ Implements Simulated Annealing  for number of violation to Ohio county rules.
    If the new map decreases the number of violations, move there.
    If it increases, move with probability proportional to increase.

    :param temperature_schedule: Callable, the annealing schedule, takes in counter, spits out ell value
    :param counter: int, the counter of the markov chain

    Requires that partitions have the "recom_ohio_county_violations" updater.
    """

    bound = 1.0

    ell = temperature_schedule(counter)

    if partition.parent is not None:
        parent_score = sum(partition.parent["recom_ohio_county_violations"])
        new_score = sum(partition["recom_ohio_county_violations"])
        bound = min(1,  ell**(parent_score-new_score))

    return random.random() < bound

def cut_edge_accept(partition: Partition) -> bool:
    """Always accepts the flip if the number of cut_edges increases.
    Otherwise, uses the Metropolis criterion to decide.

    :param partition: The current partition to accept a flip from.
    :return: True if accepted, False to remain in place

    """
    bound = 1.0

    if partition.parent is not None:
        bound = min(1, len(partition.parent["cut_edges"]) / len(partition["cut_edges"]))

    return random.random() < bound

def seat_bias_accept(partition: Partition,
                     election_name: str,
                    ell: int = 1,
                 party: str = "Dem") -> bool:
    """ Implements Metropolis/Hastings Hill climber for number of seats won by party.
    If the new map increases the number of seats, move there.
    If it decreases, move with probability proportional to decrease.

    :param ell: float, the metropolis constant, larger values move distribution towards global max/min
    :param election_name: str, the name of the election updater
    :param party: str, the name of the party whose seats you increase
    """

    bound = 1.0

    if partition.parent is not None:
        parent_score = partition.parent[election_name].seats(party)
        new_score = partition[election_name].seats(party)
        bound = min(1,  ell**(new_score-parent_score))

    return random.random() < bound