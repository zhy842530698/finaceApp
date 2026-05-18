import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

STOCKS = {
    'AAPL': 'Apple（苹果）',
    'MSFT': 'Microsoft（微软）',
    'GOOGL': 'Google 母公司 Alphabet',
    'AMZN': 'Amazon（亚马逊）',
    'NVDA': 'NVIDIA（英伟达）',
    'META': 'Meta（原 Facebook）',
    'TSLA': 'Tesla（特斯拉）'
}

DATA_DIR = 'stock_data'

def load_stock_data(symbol):
    """从本地加载股票数据"""
    csv_path = f'{DATA_DIR}/{symbol}.csv'
    try:
        df = pd.read_csv(csv_path)
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    except Exception as e:
        print(f'加载 {symbol} 失败: {e}')
        return None

def plot_stock_charts():
    """绘制股价走势图"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建一个 4x2 的子图布局
    fig, axes = plt.subplots(4, 2, figsize=(16, 20))
    axes = axes.flatten()

    # 颜色列表
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

    for idx, (symbol, name) in enumerate(STOCKS.items()):
        ax = axes[idx]
        df = load_stock_data(symbol)

        if df is not None and '收盘' in df.columns:
            ax.fill_between(df['日期'], df['最低'], df['最高'],
                          alpha=0.3, color=colors[idx], label='High-Low Range')
            ax.plot(df['日期'], df['收盘'], color=colors[idx],
                   linewidth=1.5, label='Close Price')
            ax.set_title(f'{symbol} - {name}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Price (USD)')
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left')

            # 添加统计信息
            start_price = df['收盘'].iloc[0]
            end_price = df['收盘'].iloc[-1]
            change = (end_price - start_price) / start_price * 100
            ax.text(0.02, 0.98, f'涨跌幅: {change:+.2f}%',
                   transform=ax.transAxes, fontsize=10,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        else:
            ax.text(0.5, 0.5, f'无法加载 {symbol} 数据',
                   transform=ax.transAxes, ha='center', va='center')

    # 隐藏最后一个空白子图
    axes[-1].axis('off')

    plt.suptitle('七大科技公司股价走势 (2025-05-17 至 2026-05-17)',
                fontsize=18, fontweight='bold', y=1.02)
    plt.tight_layout()

    # 保存图表
    plt.savefig('stock_charts.png', dpi=150, bbox_inches='tight')
    print('图表已保存到 stock_charts.png')

    # 创建一个综合对比图
    fig2, ax2 = plt.subplots(figsize=(14, 8))

    for idx, (symbol, name) in enumerate(STOCKS.items()):
        df = load_stock_data(symbol)
        if df is not None and '收盘' in df.columns:
            # 归一化到起始价格为100，便于对比
            normalized = (df['收盘'] / df['收盘'].iloc[0]) * 100
            ax2.plot(df['日期'], normalized, color=colors[idx],
                    linewidth=1.5, label=f'{symbol}', alpha=0.8)

    ax2.set_title('七大科技公司股价对比 (归一化, 起始=100)',
                 fontsize=16, fontweight='bold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Normalized Price (Base=100)')
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', ncol=4, fontsize=10)
    plt.tight_layout()

    plt.savefig('stock_comparison.png', dpi=150, bbox_inches='tight')
    print('对比图已保存到 stock_comparison.png')

    plt.show()

if __name__ == '__main__':
    plot_stock_charts()