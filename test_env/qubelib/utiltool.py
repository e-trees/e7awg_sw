import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt


def plot_graph(freq, samples, color, title, filepath):
    time = np.linspace(0, 1000000 * len(samples) / freq, len(samples), endpoint=False)
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, samples, linewidth=0.8, color=color)
    plt.savefig(filepath)
    plt.close()
    return
