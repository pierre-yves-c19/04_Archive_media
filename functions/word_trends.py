import pandas as pd
import matplotlib.pyplot as plt

def get_count(row, keyword, normalized=True):
    count = row.lower().count(keyword.lower())
    if normalized:
        count = count / len(row)
    return count

def get_counts(df , keywords, normalized=True):
    df_trend = pd.DataFrame()
    for keyword in keywords:
        df_trend[keyword] = df.apply(
            lambda x: get_count(x, keyword=keyword, normalized=normalized))
    df_trend.index = df.index
    return df_trend

def plot_trends(df_trend):
    fig, ax = plt.subplots(figsize=(12, 3))
    df_trend.resample("M").mean().plot(ax=ax, alpha=0.4, kind="area", stacked=True)
    ax.set_ylabel("Indice d'occurence")
    ax.set_title("Evolution de l'occurence des termes")
    return fig, ax

def analyse_trends(df, keywords, normalized=True):
    df_trend = get_counts(df, keywords, normalized=normalized)
    fig, ax = plot_trends(df_trend)
    return fig, ax

