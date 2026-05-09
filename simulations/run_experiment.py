import click
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from hyper_tissue import AigarthTissue

@click.command()
@click.option('--size', default=512)
@click.option('--mut', default=0.20)
@click.option('--gens', default=60)
@click.option('--pop', default=128)
@click.option('--seed', default=None)
def run(size, mut, gens, pop, seed):
    if seed:
        s = int(seed, 16) % (2**32)
    else:
        s = 42
    tissue = AigarthTissue(size=size, seed=s)
    
    results = []
    print(f"🌱 Aigarth Garden Experiment → mut={mut} gens={gens} pop={pop} [Helix + Teacher]")
    
    for g in range(gens):
        pop_data = tissue.evolve_population(pop_size=pop, generations=1, mut_rate=mut)
        best_fit = pop_data[0][1]
        results.append({'gen': g+1, 'best_fitness': best_fit, 'mut': mut})
        print(f"Gen {g+1:2d} | Best fitness: {best_fit:.6f}")
    
    df = pd.DataFrame(results)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    df.to_csv(f"results_mut{mut}_{ts}.csv", index=False)
    
    plt.figure(figsize=(10,6))
    plt.plot(df['gen'], df['best_fitness'], marker='o', linewidth=2)
    plt.title(f'Hyperidentity Evolution (Mut={mut}) - Helix + Teacher')
    plt.xlabel('Generation')
    plt.ylabel('Best Fitness')
    plt.grid(True)
    plt.savefig(f'fitness_curve_mut{mut}_{ts}.png')
    plt.show()
    
    np.save(f'best_child_mut{mut}_{ts}.npy', pop_data[0][0])
    print(f"✅ Done! Best fitness: {best_fit:.6f} | Advanced fitness active.")

if __name__ == '__main__':
    run()
