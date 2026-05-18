import akshare as ak
import pandas as pd
import os
from datetime import datetime, timedelta

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
CACHE_FILE = 'stock_data_cache.pkl'

def download_all_data():
    """下载所有股票数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    all_data = {}

    for symbol in STOCKS.keys():
        csv_path = os.path.join(DATA_DIR, f'{symbol}.csv')

        # 尝试从本地加载
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if len(df) > 100:
                all_data[symbol] = df
                print(f'{symbol} 从本地加载')
                continue

        print(f'下载 {symbol} ({STOCKS[symbol]})...')
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=400)).strftime('%Y%m%d')

            df = ak.stock_us_hist(symbol=symbol, period='daily',
                                   start_date=start_date, end_date=end_date,
                                   adjust='qfq')

            if df is not None and len(df) > 0:
                df.to_csv(csv_path, index=False)
                all_data[symbol] = df
                print(f'  成功: {len(df)} 条')
            else:
                print(f'  返回空数据')
        except Exception as e:
            print(f'  失败: {e}')
            # 尝试备用接口
            try:
                df = ak.stock_zh_index_spot()
                print(f'  尝试备用接口')
            except:
                pass

    return all_data

def get_stock_data():
    """获取所有股票数据"""
    all_data = {}
    for symbol in STOCKS.keys():
        csv_path = os.path.join(DATA_DIR, f'{symbol}.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            all_data[symbol] = df
    return all_data

if __name__ == '__main__':
    download_all_data()