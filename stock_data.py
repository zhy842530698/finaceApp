import akshare as ak
import pandas as pd
import os

# 定义股票代码和公司名称
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

def download_stock_data():
    """下载所有股票数据并保存到本地"""
    os.makedirs(DATA_DIR, exist_ok=True)

    for symbol in STOCKS.keys():
        csv_path = os.path.join(DATA_DIR, f'{symbol}.csv')
        if os.path.exists(csv_path):
            print(f'{symbol} 数据已存在，跳过下载')
            continue

        print(f'正在下载 {symbol} ({STOCKS[symbol]}) ...')
        try:
            # 获取美股历史数据
            df = ak.stock_us_hist(symbol=symbol, period='daily',
                                   start_date='20250517', end_date='20260517',
                                   adjust='qfq')

            # 保存到本地CSV
            df.to_csv(csv_path, index=False)
            print(f'  {symbol} 数据已保存，共 {len(df)} 条记录')

        except Exception as e:
            print(f'  下载 {symbol} 失败: {e}')

def load_stock_data(symbol):
    """从本地加载股票数据"""
    csv_path = os.path.join(DATA_DIR, f'{symbol}.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, parse_dates=['日期'])
        return df
    return None

def get_all_data():
    """加载所有股票数据"""
    all_data = {}
    for symbol in STOCKS.keys():
        df = load_stock_data(symbol)
        if df is not None:
            all_data[symbol] = df
    return all_data