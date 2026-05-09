import numpy as np
from typing import Tuple, List

class AigarthTissue:
    def __init__(self, size: int = 512, seed: int = 86):
        np.random.seed(seed)
        self.size = size
        self.parent_weights = np.random.uniform(-1.0, 1.0, size).astype(np.float32)
        self.population = None

    def ternary_activate(self, x: np.ndarray) -> np.ndarray:
        return np.sign(np.clip(x, -0.5, 0.5))

    def simulate_ticks(self, weights: np.ndarray, ticks: int = 200) -> np.ndarray:
        state = np.zeros(self.size, dtype=np.float32)
        for _ in range(ticks):
            interactions = np.dot(weights.reshape(1, -1), state.reshape(-1, 1)).flatten()
            state = self.ternary_activate(interactions * 0.1 + state * 0.9)
        return state

    def hyperidentity_mutate(self, parent: np.ndarray, mut_rate: float = 0.20, mut_strength: float = 0.3) -> Tuple[np.ndarray, float]:
        child = parent.copy()
        mask = np.random.rand(self.size) < mut_rate
        child[mask] += np.random.uniform(-mut_strength, mut_strength, mask.sum())
        child = np.clip(child, -1.0, 1.0)
        
        parent_state = self.simulate_ticks(parent)
        child_state = self.simulate_ticks(child)
        
        fidelity = -np.mean(np.abs(child_state - parent_state)) * 1.0
        diversity = np.std(child_state) * 0.5
        structural_bonus = 0.1 * np.mean(np.abs(child - parent))
        
        helix_score = -np.mean(np.abs(child_state + parent_state)) * 0.15
        teacher_score = -np.mean(np.abs(child_state - np.roll(parent_state, 1))) * 0.1
        
        # Long-term stability (1000 ticks)
        long_parent = self.simulate_ticks(parent, ticks=1000)
        long_child = self.simulate_ticks(child, ticks=1000)
        stability_score = -np.mean(np.abs(long_child - long_parent)) * 0.2
        
        fitness = fidelity + diversity + structural_bonus + helix_score + teacher_score + stability_score
        return child, fitness

    def evolve_population(self, pop_size: int = 128, generations: int = 1, mut_rate: float = 0.20) -> List:
        if self.population is None:
            self.population = [(self.parent_weights.copy(), 0.0)]
        
        for _ in range(generations):
            new_pop = []
            for _ in range(pop_size):
                parent_idx = np.random.randint(0, len(self.population))
                parent_w = self.population[parent_idx][0]
                child, fit = self.hyperidentity_mutate(parent_w, mut_rate=mut_rate)
                new_pop.append((child, fit))
            
            new_pop.sort(key=lambda x: x[1], reverse=True)
            self.population = new_pop[:pop_size//3] + new_pop[:pop_size//2]
        return self.population
