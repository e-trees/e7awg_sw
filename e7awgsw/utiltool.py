import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt


def plot_graph(sampling_rate, samples, title, filepath, color = '#b44c97'):
    """サンプル値をグラフとしてファイルに保存する

    Args:
        sampling_rate (int or float): samples を取得した際のサンプリングレート. (単位: Hz)
        samples (list of [float | int]): グラフに出力するサンプル値のリスト.
        title (string): グラフのタイトル.
        filepath (string): グラフを保存するファイルのパス.
        color (string): グラフの線の色. 16進RGB値で指定する. (例: '#102030')
    """
    time = np.linspace(0, 1000000 * len(samples) / sampling_rate, len(samples), endpoint=False)
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, samples, linewidth=0.8, color=color)
    plt.savefig(filepath)
    plt.close()
    return
