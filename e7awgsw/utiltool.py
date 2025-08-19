from __future__ import annotations

import numpy as np
from matplotlib.ticker import MaxNLocator
from collections.abc import Sequence
from matplotlib.axes import Axes
from cycler import cycler

try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt


def plot_graph(
    sampling_rate: float,
    samples: Sequence[float | Sequence[float]],
    title: str,
    filepath: str,
    colors: list[str] = ['#b44c97','#2accd1'],
    formats: list[str] = ['-'],
    line_width: float = 0.8
) -> None:
    """時刻とサンプル値のグラフをファイルに保存する

    Args:
        sampling_rate (float): samples を取得した際のサンプリングレート. (単位: Hz)
        samples (Sequence[float | Sequence[float]]): グラフに出力するサンプル値のリスト.  または, サンプル値のリストのリスト.
        title (str): グラフのタイトル.
        filepath (str): グラフを保存するファイルのパス.
        colors (list[str]): グラフの線と点の色のリスト. 16進RGB値で指定する. (例: '#102030')
        formats (list[str]): 線と点のフォーマット  (参考: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html)
        linewidth (float): 線の幅
    """
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    if len(samples) != 0:
        samples_list: Sequence = [samples] if not isinstance(samples[0], Sequence) else samples
        for i in range(len(samples_list)):
            sample_set = samples_list[i]
            time = np.linspace(
                0,
                1000000 * len(sample_set) / sampling_rate,
                len(sample_set),
                endpoint = False)
            color = colors[i % len(colors)]
            fmt = formats[i % len(formats)]
            plt.plot(
                time,
                sample_set,
                fmt,
                linewidth = line_width,
                color = color)

    plt.savefig(filepath)
    plt.close()
    return


def plot_samples(
    samples: Sequence[float | Sequence[float]],
    title: str,
    filepath: str,
    x_label: str = 'Sample No',
    colors: list[str] = ['#b44c97','#2accd1'],
    formats: list[str] = ['-', '-'],
    line_width: float = 0.8
) -> None:
    """サンプル値をグラフとしてファイルに保存する

    Args:
        samples (Sequence[float | Sequence[float]]): グラフに出力するサンプル値のリスト.  または, サンプル値のリストのリスト.
        title (str): グラフのタイトル.
        filepath (str): グラフを保存するファイルのパス.
        x_label (str): 横軸のラベル
        colors (list[str]): グラフの線と点の色のリスト. 16進RGB値で指定する. (例: '#102030')
        formats (list[str]): 線と点のフォーマット  (参考: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html)
        linewidth (float): 線の幅
    """
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel(x_label)
    plt.title(title)
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer = True))
    if len(samples) != 0:
        samples_list: Sequence = [samples] if not isinstance(samples[0], Sequence) else samples
        for i in range(len(samples_list)):
            sample_set = samples_list[i]
            point_no = [i for i in range(len(sample_set))]
            color = colors[i % len(colors)]
            fmt = formats[i % len(formats)]
            plt.plot(
                point_no,
                sample_set,
                fmt,
                linewidth = line_width,
                color = color)

    plt.savefig(filepath)
    plt.close()
    return


def plot_spectrum(
    spectrum: list[int|float],
    title: str,
    filepath: str, 
    sampling_rate: float,
    plot_range: tuple[int, int],
    label_threshold: float,
    color: str = '#b44c97'
) -> None:
    """
    フーリエ変換をして求めたスペクトルをグラフとしてファイルに保存する

    spectrum (list[int|float]):
        プロットするスペクトル
    title (str):
        グラフのタイトル.
    filepath (str): 
        グラフを保存するファイルのパス.
    sampling_rate (float): 
        フーリエ変換をかけた波形データのサンプリングレート [単位: Hz]
    plot_range (tuple[int, int]): 
        プロットする範囲 (各要素は 0~1.0)
    label_threshold (float): 
        spectrum の中で絶対値が最大の値を a としたとき,
        絶対値が abs(a) * label_threshold 以下の spectrum の bin に対して周波数などの詳細が書かれたラベルを付加する. (0 ~ 1)
    color (str):
        グラフの色 (matplot の CN 記法)
    """
    freq_res = sampling_rate / len(spectrum)
    begin = int(plot_range[0] * len(spectrum))
    end = int(plot_range[1] * len(spectrum))
    part_of_spectrum = spectrum[begin : end]
    bin_no = [i * freq_res / 1e6 for i in range(begin, end)]
    plt.figure(figsize=(8, 6), dpi=300)
    plt.title(title)
    plt.suptitle(
        "sampling rate: {} Msps,  bin: {}-{}\n FFT size: {},  Frequency Resolution: {} kHz"
        .format(sampling_rate / 1e6, begin, end - 1, len(spectrum), freq_res / 1e3),
        fontsize=10)
    ax = plt.gca()
    ax.grid(which="both")
    ax.grid(which="major", alpha=0.5)
    ax.grid(which="minor", alpha=0.2)
    ax.set_ylabel("Power")
    ax.set_xlabel("Frequency [MHz]")
    label_threshold = np.max(np.abs(part_of_spectrum)) * label_threshold
    __annotate_spectrum(ax, freq_res, label_threshold, begin, part_of_spectrum)
    ax.plot(bin_no, part_of_spectrum, linewidth=0.8, color=color)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()
    return


def __annotate_spectrum(
    plot: Axes,
    freq_res: float,
    threshold: float,
    bin_offset: int,
    spectrum: list[int|float]):
    for i in range(len(spectrum)):
        if abs(spectrum[i]) >= threshold:
            freq = "f=" + "{:.2f}".format((i + bin_offset) * freq_res / 1e6)
            bin_no = "bin=" + str(i + bin_offset)
            plot.annotate(f"{freq}\n{bin_no}", (i * freq_res / 1e6, spectrum[i]), size=6)


def plot_stems(
    samples: Sequence[float | Sequence[float]],
    title: str,
    filepath: str,
    x_label: str = 'Sample No',
    colors: list[str] = ['#b44c97','#2accd1'],
    marker_formats: list[str] = ['o', '*'],
    line_format: str = '-',
    base_format: str = 'k-'
) -> None:
    """サンプル値と幹をグラフとしてファイルに保存する

    | samples に複数のリストを指定した場合, 1 つ目のリストのサンプルに対してのみ幹が付く

    Args:
        samples (Sequence[float]): グラフに出力するサンプル値のリスト.  または, サンプル値のリストのリスト.
        title (str): グラフのタイトル.
        filepath (str): グラフを保存するファイルのパス.
        x_label (str): 横軸のラベル
        marker_formats (list[str]): マーカーのフォーマット
        line_format (str): ラインのフォーマット
        base_format (str): ベースラインのフォーマット
    """
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel(x_label)
    plt.title(title)
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer = True))
    if len(samples) != 0:
        samples_list: Sequence = [samples] if not isinstance(samples[0], Sequence) else samples
        for i in range(len(samples_list)):
            color = colors[i % len(colors)]
            marker_format = marker_formats[i % len(marker_formats)]
            point_no = [i for i in range(len(samples_list[i]))]
            if i == 0:
                markerline, stemlines, _ = plt.stem(
                    point_no,
                    samples_list[i],
                    markerfmt = marker_format,
                    linefmt = line_format,
                    basefmt = base_format)
                plt.setp(stemlines, 'color', color)
                plt.setp(markerline, 'color', color)
            else:
                plt.plot(
                    point_no,
                    samples_list[i],
                    marker_format,
                    color = color)

    plt.savefig(filepath)
    plt.close()
    return
