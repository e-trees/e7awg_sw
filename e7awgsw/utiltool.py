import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt


def plot_graph(sampling_rate, samples, title, filepath, color = '#b44c97', marker = None):
    """時刻とサンプル値のグラフをファイルに保存する

    Args:
        sampling_rate (int or float): samples を取得した際のサンプリングレート. (単位: Hz)
        samples (list of [float | int]): グラフに出力するサンプル値のリスト.
        title (string): グラフのタイトル.
        filepath (string): グラフを保存するファイルのパス.
        color (string): グラフの線の色. 16進RGB値で指定する. (例: '#102030')
        marker (string): グラフに描画される点の種類
    """
    time = np.linspace(0, 1000000 * len(samples) / sampling_rate, len(samples), endpoint=False)
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, samples, linewidth=0.8, color=color, marker=marker)
    plt.savefig(filepath)
    plt.close()
    return


def plot_samples(samples, title, filepath, color = '#b44c97', marker = None, x_label = 'Sample No'):
    """サンプル値をグラフとしてファイルに保存する

    Args:
        samples (list of [float | int]): グラフに出力するサンプル値のリスト.
        title (string): グラフのタイトル.
        filepath (string): グラフを保存するファイルのパス.
        color (string): グラフの線の色. 16進RGB値で指定する. (例: '#102030')
        marker (string): グラフに描画される点の種類
        x_label (string): 横軸のラベル
    """
    point_no = [i for i in range(len(samples))]
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel(x_label)
    plt.title(title)
    plt.plot(point_no, samples, linewidth=0.8, color=color, marker=marker)
    plt.savefig(filepath)
    plt.close()
    return