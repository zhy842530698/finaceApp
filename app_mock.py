"""带有模拟数据的金融终端 - akshare接口不稳定时使用"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import random

app = FastAPI(title="金融终端")

STOCKS = {
    'AAPL': 'Apple（苹果）',
    'MSFT': 'Microsoft（微软）',
    'GOOGL': 'Google 母公司 Alphabet',
    'AMZN': 'Amazon（亚马逊）',
    'NVDA': 'NVIDIA（英伟达）',
    'META': 'Meta（原 Facebook）',
    'TSLA': 'Tesla（特斯拉）'
}

BASE_PRICES = {
    'AAPL': 185, 'MSFT': 415, 'GOOGL': 175, 'AMZN': 195,
    'NVDA': 130, 'META': 530, 'TSLA': 175
}

def generate_mock_data(symbol, days=365):
    """生成模拟股票数据"""
    base_price = BASE_PRICES[symbol]
    data = []
    current_price = base_price

    # 生成趋势和波动
    trend = np.random.uniform(-0.0002, 0.0008)  # 整体趋势
    volatility = np.random.uniform(0.015, 0.025)

    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)

        # 加入随机波动
        change = np.random.normal(trend, volatility)
        current_price *= (1 + change)

        high = current_price * (1 + abs(np.random.normal(0, 0.01)))
        low = current_price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = low + (high - low) * random.random()
        volume = int(np.random.uniform(30, 80) * 1e6)

        data.append({
            '日期': date.strftime('%Y-%m-%d'),
            '开盘': round(open_price, 2),
            '收盘': round(current_price, 2),
            '最高': round(high, 2),
            '最低': round(low, 2),
            '成交量': volume
        })

    return data

# 预生成数据
MOCK_DATA = {symbol: generate_mock_data(symbol) for symbol in STOCKS.keys()}

@app.get("/api/stocks")
def get_stocks():
    return MOCK_DATA

@app.get("/api/stocks/{symbol}")
def get_stock(symbol):
    if symbol in MOCK_DATA:
        return {"symbol": symbol, "name": STOCKS[symbol], "data": MOCK_DATA[symbol]}
    return {"error": "Stock not found"}

@app.get("/api/stats")
def get_stats():
    stats = {}
    for symbol, data in MOCK_DATA.items():
        if data:
            start_price = data[0]['收盘']
            end_price = data[-1]['收盘']
            change = (end_price - start_price) / start_price * 100
            stats[symbol] = {
                "name": STOCKS[symbol],
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "change_percent": round(change, 2),
                "data_count": len(data)
            }
    return stats

@app.get("/")
def index():
    html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>金融终端 - 七大科技股走势</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 { font-size: 24px; color: #00d4ff; }
        .header .time { color: #888; font-size: 14px; }
        .container { padding: 20px 40px; }
        .stats-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .stock-card {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 15px 20px;
            min-width: 180px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid transparent;
        }
        .stock-card:hover { background: rgba(255,255,255,0.15); border-color: #00d4ff; }
        .stock-card.active { border-color: #00d4ff; background: rgba(0,212,255,0.2); }
        .stock-card .symbol { font-size: 18px; font-weight: bold; color: #00d4ff; }
        .stock-card .name { font-size: 12px; color: #aaa; margin: 5px 0; }
        .stock-card .change { font-size: 16px; font-weight: bold; }
        .stock-card .price { font-size: 14px; color: #888; }
        .positive { color: #00ff88; }
        .negative { color: #ff4757; }
        .chart-container {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            margin-top: 20px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab {
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .tab.active { background: #00d4ff; color: #000; }
        .chart-wrapper { height: 450px; }
        .loading { text-align: center; padding: 50px; color: #888; }
        .controls {
            display: flex;
            gap: 15px;
            margin-top: 15px;
            align-items: center;
        }
        .controls select {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            background: rgba(255,255,255,0.1);
            color: #fff;
            cursor: pointer;
        }
        .note { color: #666; font-size: 12px; margin-top: 10px; }
        @media (max-width: 768px) {
            .header { padding: 15px 20px; }
            .container { padding: 15px 20px; }
            .stock-card { min-width: 140px; }
            .chart-wrapper { height: 300px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 金融终端</h1>
        <div>
            <div class="time" id="currentTime"></div>
            <div class="note">模拟数据</div>
        </div>
    </div>

    <div class="container">
        <div class="stats-bar" id="statsBar"><div class="loading">加载中...</div></div>

        <div class="controls">
            <select id="timeRange">
                <option value="30">近30天</option>
                <option value="90">近90天</option>
                <option value="180">近半年</option>
                <option value="365" selected>近一年</option>
                <option value="all">全部数据</option>
            </select>
        </div>

        <div class="chart-container">
            <div class="tabs">
                <div class="tab active" onclick="showAllCharts()">📊 综合对比</div>
                <div class="tab" onclick="showSingleChart('AAPL')">🍎 Apple</div>
                <div class="tab" onclick="showSingleChart('MSFT')">🪟 Microsoft</div>
                <div class="tab" onclick="showSingleChart('GOOGL')">🔍 Google</div>
                <div class="tab" onclick="showSingleChart('AMZN')">📦 Amazon</div>
                <div class="tab" onclick="showSingleChart('NVDA')">🎮 NVIDIA</div>
                <div class="tab" onclick="showSingleChart('META')">💬 Meta</div>
                <div class="tab" onclick="showSingleChart('TSLA')">🚗 Tesla</div>
            </div>
            <div class="chart-wrapper"><canvas id="mainChart"></canvas></div>
        </div>
    </div>

    <script>
        let allData = {};
        let mainChart = null;
        let currentMode = 'all';

        function updateTime() {
            document.getElementById('currentTime').textContent = new Date().toLocaleString('zh-CN');
        }
        setInterval(updateTime, 1000);
        updateTime();

        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                const bar = document.getElementById('statsBar');
                bar.innerHTML = Object.entries(stats).map(([symbol, s]) => `
                    <div class="stock-card" onclick="showSingleChart('${symbol}')">
                        <div class="symbol">${symbol}</div>
                        <div class="name">${s.name}</div>
                        <div class="change ${s.change_percent >= 0 ? 'positive' : 'negative'}">
                            ${s.change_percent >= 0 ? '▲' : '▼'} ${s.change_percent.toFixed(2)}%
                        </div>
                        <div class="price">$ ${s.end_price}</div>
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('statsBar').innerHTML = '<div class="loading">数据加载失败</div>';
            }
        }

        async function loadAllStockData() {
            try {
                const res = await fetch('/api/stocks');
                allData = await res.json();
                updateChart();
            } catch (e) { console.error('加载失败:', e); }
        }

        function getFilteredData(symbol) {
            const range = document.getElementById('timeRange').value;
            const data = allData[symbol] || [];
            if (range === 'all' || data.length === 0) return data;
            return data.slice(-parseInt(range));
        }

        function updateChart() {
            const ctx = document.getElementById('mainChart').getContext('2d');
            if (mainChart) mainChart.destroy();

            const colors = {
                'AAPL': '#A2AAAD', 'MSFT': '#00A4EF', 'GOOGL': '#4285F4',
                'AMZN': '#FF9900', 'NVDA': '#76B900', 'META': '#0668E1', 'TSLA': '#CC0000'
            };

            if (currentMode === 'all') {
                mainChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        datasets: Object.keys(allData).map(symbol => {
                            const data = getFilteredData(symbol);
                            const base = data[0]?.收盘 || 100;
                            return {
                                label: symbol,
                                data: data.map(d => ({ x: d.日期, y: (d.收盘 / base) * 100 })),
                                borderColor: colors[symbol], borderWidth: 2, tension: 0.3, pointRadius: 0, fill: false
                            };
                        })
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: { legend: { position: 'top', labels: { color: '#fff' } } },
                        scales: {
                            x: { type: 'time', time: { unit: 'month' }, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#888' } },
                            y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#888' } }
                        }
                    }
                });
            } else {
                const data = getFilteredData(currentMode);
                mainChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        datasets: [{
                            label: '收盘价',
                            data: data.map(d => ({ x: d.日期, y: d.收盘 })),
                            borderColor: colors[currentMode], backgroundColor: colors[currentMode] + '30',
                            borderWidth: 2, tension: 0.3, fill: true
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { type: 'time', time: { unit: 'month' }, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#888' } },
                            y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#888', callback: v => '$' + v.toFixed(0) } }
                        }
                    }
                });
            }
        }

        function showAllCharts() {
            currentMode = 'all';
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector('.tab').classList.add('active');
            updateChart();
        }

        function showSingleChart(symbol) {
            currentMode = symbol;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            const idx = Object.keys(STOCKS).indexOf(symbol) + 1;
            document.querySelectorAll('.tab')[idx]?.classList.add('active');
            updateChart();
        }

        const STOCKS = {
            'AAPL': 'Apple', 'MSFT': 'Microsoft', 'GOOGL': 'Alphabet',
            'AMZN': 'Amazon', 'NVDA': 'NVIDIA', 'META': 'Meta', 'TSLA': 'Tesla'
        };

        document.getElementById('timeRange').addEventListener('change', updateChart);
        loadStats();
        loadAllStockData();
    </script>
</body>
</html>
    '''
    return HTMLResponse(content=html_content)

if __name__ == '__main__':
    import uvicorn
    print("\n" + "="*50)
    print("📈 金融终端已启动")
    print("="*50)
    print("🌐 访问: http://localhost:9000")
    print("📱 手机: http://<本机IP>:9000")
    print("="*50 + "\n")
    uvicorn.run(app, host='0.0.0.0', port=9000)