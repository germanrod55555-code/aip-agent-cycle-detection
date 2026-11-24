"""Графики из сохранённых результатов, без повторного эксперимента."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAMES = {"floyd": "Флойд", "brent": "Брент", "hash": "Своя хеш-таблица", "dict": "Python dict"}
COLORS = {"floyd": "#333333", "brent": "#245c85", "hash": "#9c562b", "dict": "#53765b"}


def make(input_dir, out):
    out.mkdir(parents=True, exist_ok=True)
    with (input_dir/"summary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.dpi": 200})
    for metric, ylabel, filename in (("median_ms", "Медианное время, мс", "time_scaling"),
                                      ("peak_bytes", "Пик отслеживаемых выделений, КиБ", "memory_scaling")):
        fig, ax = plt.subplots(figsize=(7.6, 4.5), layout="constrained")
        for name in NAMES:
            selected = [r for r in rows if r["case"].startswith("rho_") and r["case"].endswith("_50") and r["algorithm"] == name]
            x = [int(r["n"]) for r in selected]
            y = [float(r[metric])/(1024 if metric=="peak_bytes" else 1) for r in selected]
            ax.plot(x, y, marker="o", label=NAMES[name], color=COLORS[name])
        ax.set_xscale("log");ax.set_yscale("log")
        ax.set_xlabel("Число различных состояний N = μ + λ")
        ax.set_ylabel(ylabel);ax.set_title("Равные длины префикса и цикла")
        ax.grid(alpha=.22);ax.legend(fontsize=9)
        fig.savefig(out/(filename+".png"));plt.close(fig)
    for prefix, title, filename in (("rho_100000_", "Дешёвый переход, N = 100 000", "cheap_times"),
                                     ("costly_1000_", "Затратный переход, N = 1 000", "costly_times")):
        fig, ax = plt.subplots(figsize=(7.6, 4.5), layout="constrained")
        for k, name in enumerate(NAMES):
            subset = [r for r in rows if r["case"].startswith(prefix) and r["algorithm"]==name]
            y = [float(r["median_ms"]) for r in subset]
            errors = [[y[i]-float(r["q1_ms"]) for i,r in enumerate(subset)],
                      [float(r["q3_ms"])-y[i] for i,r in enumerate(subset)]]
            ax.bar([i+(k-1.5)*.19 for i in range(3)],y,width=.18,color=COLORS[name],label=NAMES[name],yerr=errors,capsize=2)
        ax.set_xticks(range(3),["μ/N = 0", "μ/N = 0,5", "μ/N = 0,9"])
        ax.set_ylabel("Медианное время, мс");ax.set_title(title,pad=38)
        ax.legend(loc="upper center",bbox_to_anchor=(.5,1.1),ncol=4,fontsize=8,frameon=False)
        ax.grid(axis="y",alpha=.2);ax.set_axisbelow(True)
        fig.savefig(out/(filename+".png"));plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=Path("results"))
    parser.add_argument("--out",type=Path,default=Path("figures"))
    args=parser.parse_args();make(args.input,args.out)
