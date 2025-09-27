"""
公司估值分析系统 - Jupyter Notebook 调试片段
将 complete_valuation_system.py 划分为可独立执行的代码块
"""

# =============================================================================
# 片段 1: 导入依赖库和基础配置
# =============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import akshare as ak
from datetime import datetime, timedelta
import warnings
import time
import random
import logging
from scipy import stats
import seaborn as sns

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 设置图表样式
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

print("✅ 库导入完成")

# =============================================================================
# 片段 2: 数据加载和演示数据创建函数
# =============================================================================

def load_stock_info(stock_code):
    """加载股票基本信息"""
    try:
        stock_info = ak.stock_individual_info_em(symbol=stock_code)
        if stock_info is not None and not stock_info.empty:
            # 提取公司名称
            name_info = stock_info[stock_info['item'] == '股票简称']
            if not name_info.empty:
                company_name = name_info.iloc[0]['value']
                print(f"✅ 成功加载股票信息: {company_name}")
                return stock_info, company_name
        print("⚠️ 股票信息为空，使用演示数据")
        return create_demo_stock_info(stock_code), f"{stock_code}演示公司"
    except Exception as e:
        print(f"❌ 加载股票信息失败: {e}")
        return create_demo_stock_info(stock_code), f"{stock_code}演示公司"

def load_historical_data(stock_code):
    """加载历史价格数据"""
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        k_data = ak.stock_zh_a_hist(symbol=stock_code,
                                  start_date=start_date,
                                  end_date=end_date,
                                  adjust="qfq")
        
        if k_data is not None and not k_data.empty:
            k_data['日期'] = pd.to_datetime(k_data['日期'])
            k_data.set_index('日期', inplace=True)
            print(f"✅ 成功加载历史价格数据，共 {len(k_data)} 条记录")
            return k_data
        print("⚠️ 历史价格数据为空，使用演示数据")
        return create_demo_historical_data()
    except Exception as e:
        print(f"❌ 加载历史价格数据失败: {e}")
        return create_demo_historical_data()

def load_financial_data(stock_code):
    """加载财务数据"""
    try:
        financial_data = {}
        
        # 财务指标数据
        try:
            financial_indicators = ak.stock_financial_analysis_indicator(symbol=stock_code)
            if financial_indicators is not None and not financial_indicators.empty:
                financial_data['indicators'] = financial_indicators.iloc[0]
                print("✅ 成功加载财务指标数据")
        except Exception as e:
            print(f"⚠️ 加载财务指标数据失败: {e}")
        
        # 实时数据
        try:
            realtime_data = ak.stock_zh_a_spot_em()
            if realtime_data is not None and not realtime_data.empty:
                stock_data = realtime_data[realtime_data['代码'] == stock_code]
                if not stock_data.empty:
                    financial_data['realtime'] = stock_data.iloc[0]
                    print("✅ 成功加载实时数据")
        except Exception as e:
            print(f"⚠️ 加载实时数据失败: {e}")
        
        if financial_data:
            print("✅ 财务数据加载完成")
            return financial_data
        print("⚠️ 所有财务数据加载失败，使用演示数据")
        return create_demo_financial_data()
    except Exception as e:
        print(f"❌ 加载财务数据失败: {e}")
        return create_demo_financial_data()

def create_demo_stock_info(stock_code):
    """创建演示股票信息"""
    return pd.DataFrame({
        'item': ['股票名称', '行业', '总股本', '市盈率', '市净率'],
        'value': [f'{stock_code}演示公司', '信息技术', '100000', '25.5', '3.2']
    })

def create_demo_historical_data():
    """创建演示历史价格数据"""
    dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
    base_price = 10 + random.random() * 40
    
    returns = np.random.normal(0.001, 0.02, 252)
    prices = base_price * np.cumprod(1 + returns)
    
    return pd.DataFrame({
        '收盘': prices,
        '开盘': prices * (1 + np.random.normal(0, 0.008, 252)),
        '最高': prices * (1 + np.random.normal(0.005, 0.012, 252)),
        '最低': prices * (1 - np.random.normal(0.005, 0.012, 252)),
        '成交量': np.random.randint(10000000, 50000000, 252)
    }, index=dates)

def create_demo_financial_data():
    """创建演示财务数据"""
    revenue = 1e6 + random.random() * 9e6
    net_income = revenue * (0.08 + random.random() * 0.12)
    total_assets = revenue * (1.5 + random.random() * 1.0)
    equity = total_assets * (0.5 + random.random() * 0.2)
    
    return {
        'indicators': pd.Series({
            '营业收入': revenue,
            '净利润': net_income,
            '总资产': total_assets,
            '净资产': equity,
            '每股收益': net_income / 1e9,
            '每股净资产': equity / 1e9
        })
    }

# =============================================================================
# 片段 3: 估值方法函数
# =============================================================================

def dcf_valuation(financial_data, stock_info, growth_rate=0.08, discount_rate=0.12, terminal_growth=0.03, years=5):
    """DCF估值法"""
    try:
        if financial_data is None:
            print("⚠️ 财务数据为空，无法执行DCF估值")
            return None
        
        indicators = financial_data.get('indicators')
        if indicators is None:
            print("⚠️ 财务指标为空，无法执行DCF估值")
            return None
        
        net_income = indicators.get('净利润', 0)
        if net_income <= 0:
            print("⚠️ 净利润为负或为零，无法执行DCF估值")
            return None
        
        fcf = net_income * 0.8  # 自由现金流为净利润的80%
        
        # 计算未来现金流现值
        future_cash_flows = []
        for year in range(1, years + 1):
            future_fcf = fcf * (1 + growth_rate) ** year
            present_value = future_fcf / (1 + discount_rate) ** year
            future_cash_flows.append(present_value)
        
        # 计算终值
        terminal_fcf = fcf * (1 + growth_rate) ** years * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        terminal_value_pv = terminal_value / (1 + discount_rate) ** years
        
        # 计算企业价值
        enterprise_value = sum(future_cash_flows) + terminal_value_pv
        
        # 获取总股本
        total_shares = 1e9
        if stock_info is not None:
            shares_info = stock_info[stock_info['item'] == '总股本']
            if not shares_info.empty:
                try:
                    total_shares = float(shares_info.iloc[0]['value']) * 1e4
                except:
                    pass
        
        intrinsic_value_per_share = enterprise_value / total_shares
        
        print(f"✅ DCF估值完成: 内在价值 {intrinsic_value_per_share:.2f} 元")
        
        return {
            'method': 'DCF估值',
            '内在价值': intrinsic_value_per_share,
            '企业价值': enterprise_value,
            '假设参数': {
                '增长率': f"{growth_rate*100:.1f}%",
                '折现率': f"{discount_rate*100:.1f}%",
                '永续增长率': f"{terminal_growth*100:.1f}%"
            }
        }
    except Exception as e:
        print(f"❌ DCF估值失败: {e}")
        return None

def relative_valuation(historical_data, financial_data, stock_info):
    """相对估值法"""
    try:
        if historical_data is None:
            print("⚠️ 历史数据为空，无法执行相对估值")
            return None
        
        current_price = historical_data['收盘'].iloc[-1]
        
        # 获取估值指标
        pe_ratio = 25.0
        pb_ratio = 3.0
        
        if stock_info is not None:
            pe_info = stock_info[stock_info['item'] == '市盈率']
            if not pe_info.empty:
                try:
                    pe_ratio = float(pe_info.iloc[0]['value'])
                except:
                    pass
        
        # 计算每股收益和每股净资产
        indicators = financial_data.get('indicators') if financial_data else None
        
        eps = indicators.get('每股收益', 0) if indicators is not None else 0
        bvps = indicators.get('每股净资产', 0) if indicators is not None else 0
        
        # 相对估值计算
        pe_value = eps * pe_ratio if eps > 0 else current_price
        pb_value = bvps * pb_ratio if bvps > 0 else current_price
        
        print(f"✅ 相对估值完成: PE估值 {pe_value:.2f} 元, PB估值 {pb_value:.2f} 元")
        
        return {
            'method': '相对估值',
            '当前价格': current_price,
            'PE估值': pe_value,
            'PB估值': pb_value,
            '行业PE': pe_ratio,
            '行业PB': pb_ratio,
            '每股收益': eps,
            '每股净资产': bvps
        }
    except Exception as e:
        print(f"❌ 相对估值失败: {e}")
        return None

def asset_based_valuation(financial_data):
    """资产基础估值法"""
    try:
        indicators = financial_data.get('indicators') if financial_data else None
        if indicators is None:
            print("⚠️ 财务指标为空，无法执行资产基础估值")
            return None
        
        nav_per_share = indicators.get('每股净资产', 0)
        
        print(f"✅ 资产基础估值完成: 每股净资产 {nav_per_share:.2f} 元")
        
        return {
            'method': '资产基础估值',
            '每股净资产': nav_per_share,
            '总资产': indicators.get('总资产', 0),
            '净资产': indicators.get('净资产', 0)
        }
    except Exception as e:
        print(f"❌ 资产基础估值失败: {e}")
        return None

def monte_carlo_valuation(historical_data, num_simulations=1000):
    """蒙特卡洛模拟估值"""
    try:
        if historical_data is None:
            print("⚠️ 历史数据为空，无法执行蒙特卡洛模拟")
            return None
        
        current_price = historical_data['收盘'].iloc[-1]
        
        returns = historical_data['收盘'].pct_change().dropna()
        if len(returns) == 0:
            print("⚠️ 收益率数据为空，无法执行蒙特卡洛模拟")
            return None
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        simulated_prices = []
        for i in range(num_simulations):
            future_returns = np.random.normal(mean_return, std_return, 252)
            simulated_price = current_price * np.prod(1 + future_returns)
            simulated_prices.append(simulated_price)
        
        simulated_prices = np.array(simulated_prices)
        
        avg_price = np.mean(simulated_prices)
        ci_95 = np.percentile(simulated_prices, [2.5, 97.5])
        
        print(f"✅ 蒙特卡洛模拟完成: 平均价格 {avg_price:.2f} 元, 95%置信区间 {ci_95[0]:.2f}-{ci_95[1]:.2f} 元")
        
        return {
            'method': '蒙特卡洛模拟',
            '当前价格': current_price,
            '模拟结果': {
                '平均价格': avg_price,
                '中位数价格': np.median(simulated_prices),
                '标准差': np.std(simulated_prices),
                '95%置信区间': ci_95,
                '68%置信区间': np.percentile(simulated_prices, [16, 84])
            }
        }
    except Exception as e:
        print(f"❌ 蒙特卡洛模拟失败: {e}")
        return None

def dividend_discount_model(historical_data, dividend_growth=0.05, required_return=0.1):
    """股利贴现模型"""
    try:
        if historical_data is None:
            print("⚠️ 历史数据为空，无法执行股利贴现模型")
            return None
        
        current_price = historical_data['收盘'].iloc[-1]
        
        dividend_yield = 0.03
        current_dividend = current_price * dividend_yield
        
        if required_return > dividend_growth:
            intrinsic_value = current_dividend * (1 + dividend_growth) / (required_return - dividend_growth)
        else:
            intrinsic_value = current_price
            print("⚠️ 要求回报率小于股息增长率，使用当前价格作为内在价值")
        
        print(f"✅ 股利贴现模型完成: 内在价值 {intrinsic_value:.2f} 元")
        
        return {
            'method': '股利贴现模型',
            '内在价值': intrinsic_value,
            '当前股息': current_dividend,
            '股息增长率': f"{dividend_growth*100:.1f}%",
            '要求回报率': f"{required_return*100:.1f}%"
        }
    except Exception as e:
        print(f"❌ 股利贴现模型失败: {e}")
        return None

def risk_analysis(historical_data):
    """风险分析"""
    try:
        if historical_data is None:
            print("⚠️ 历史数据为空，无法执行风险分析")
            return None
        
        returns = historical_data['收盘'].pct_change().dropna()
        if len(returns) == 0:
            print("⚠️ 收益率数据为空，无法执行风险分析")
            return None
        
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        var_95 = np.percentile(returns, 5)
        expected_shortfall = returns[returns <= var_95].mean()
        max_drawdown = calculate_max_drawdown(historical_data)
        
        print(f"✅ 风险分析完成: 年化波动率 {volatility*100:.2f}%, 夏普比率 {sharpe_ratio:.2f}, 最大回撤 {max_drawdown*100:.2f}%")
        
        return {
            '年化波动率': volatility,
            '夏普比率': sharpe_ratio,
            '95%VaR': var_95,
            '条件VaR': expected_shortfall,
            '最大回撤': max_drawdown
        }
    except Exception as e:
        print(f"❌ 风险分析失败: {e}")
        return None

def calculate_max_drawdown(historical_data):
    """计算最大回撤"""
    if historical_data is None:
        return 0
    
    prices = historical_data['收盘']
    peak = prices.expanding().max()
    drawdown = (prices - peak) / peak
    max_drawdown = drawdown.min()
    
    return max_drawdown

# =============================================================================
# 片段 4: 可视化函数
# =============================================================================

def create_valuation_charts(historical_data, valuation_results, company_name, stock_code):
    """创建估值图表"""
    try:
        # 创建多个子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{company_name} ({stock_code}) - 完整估值分析', fontsize=16, fontweight='bold')
        
        # 1. 价格走势图
        ax1 = axes[0, 0]
        if historical_data is not None:
            ax1.plot(historical_data.index, historical_data['收盘'], linewidth=1.5, color='blue')
            ax1.set_title('历史价格走势', fontsize=12)
            ax1.set_ylabel('价格 (元)', fontsize=10)
            ax1.grid(True, alpha=0.3)
        
        # 2. 估值方法对比
        ax2 = axes[0, 1]
        methods = []
        values = []
        current_price = None
        
        for method, result in valuation_results.items():
            if method == '相对估值':
                current_price = result.get('当前价格', 0)
                methods.extend(['PE估值', 'PB估值'])
                values.extend([result.get('PE估值', 0), result.get('PB估值', 0)])
            elif method == 'DCF估值':
                methods.append('DCF估值')
                values.append(result.get('内在价值', 0))
            elif method == '资产基础估值':
                methods.append('净资产估值')
                values.append(result.get('每股净资产', 0))
            elif method == '蒙特卡洛模拟':
                methods.append('蒙特卡洛均值')
                values.append(result.get('模拟结果', {}).get('平均价格', 0))
            elif method == '股利贴现模型':
                methods.append('DDM估值')
                values.append(result.get('内在价值', 0))
        
        if current_price:
            methods.insert(0, '当前股价')
            values.insert(0, current_price)
        
        if methods and values:
            colors = ['lightblue' if '当前' in method else 'lightgreen' for method in methods]
            bars = ax2.bar(methods, values, color=colors, alpha=0.7)
            ax2.set_title('各种估值方法对比', fontsize=12)
            ax2.set_ylabel('价格 (元)', fontsize=10)
            ax2.tick_params(axis='x', rotation=45)
            
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                        f'{value:.2f}', ha='center', va='bottom', fontsize=9)
        
        # 3. 风险指标
        ax3 = axes[1, 0]
        if '风险分析' in valuation_results:
            risk_result = valuation_results['风险分析']
            metrics = ['年化波动率', '夏普比率', '最大回撤']
            values = [
                risk_result.get('年化波动率', 0) * 100,
                risk_result.get('夏普比率', 0),
                abs(risk_result.get('最大回撤', 0)) * 100
            ]
            
            ax3.bar(metrics, values, color=['orange', 'purple', 'red'], alpha=0.7)
            ax3.set_title('风险收益指标', fontsize=12)
            ax3.set_ylabel('百分比/比率', fontsize=10)
        
        # 4. 估值区间
        ax4 = axes[1, 1]
        if '蒙特卡洛模拟' in valuation_results:
            mc_result = valuation_results['蒙特卡洛模拟']
            sim_results = mc_result.get('模拟结果', {})
            ci_95 = sim_results.get('95%置信区间', [0, 0])
            ci_68 = sim_results.get('68%置信区间', [0, 0])
            
            intervals = ['68%置信区间', '95%置信区间']
            lower_bounds = [ci_68[0], ci_95[0]]
            upper_bounds = [ci_68[1], ci_95[1]]
            
            for i, (lower, upper) in enumerate(zip(lower_bounds, upper_bounds)):
                ax4.barh(i, upper - lower, left=lower, alpha=0.6,
                        color=['lightcoral', 'lightblue'][i])
                ax4.text((lower + upper) / 2, i, f'{lower:.2f}-{upper:.2f}',
                        ha='center', va='center', fontweight='bold')
            
            ax4.set_yticks(range(len(intervals)))
            ax4.set_yticklabels(intervals)
            ax4.set_title('估值区间分布', fontsize=12)
            ax4.set_xlabel('价格 (元)', fontsize=10)
        
        plt.tight_layout()
        plt.show()
        
        print("📊 可视化图表已生成")
        
    except Exception as e:
        print(f"❌ 图表生成失败: {e}")

# =============================================================================
# 片段 5: 完整分析流程示例
# =============================================================================

def run_complete_analysis(stock_code='600036'):
    """运行完整分析流程示例"""
    print(f"🚀 开始分析 {stock_code}...")
    
    # 1. 加载数据
    print("\n📊 步骤1: 加载数据")
    stock_info, company_name = load_stock_info(stock_code)
    historical_data = load_historical_data(stock_code)
    financial_data = load_financial_data(stock_code)
    
    # 2. 执行各种估值方法
    print("\n🔍 步骤2: 执行估值分析")
    valuation_results = {}
    
    # DCF估值
    dcf_result = dcf_valuation(financial_data, stock_info)
    if dcf_result:
        valuation_results['DCF估值'] = dcf_result
    
    # 相对估值
    relative_result = relative_valuation(historical_data, financial_data, stock_info)
    if relative_result:
        valuation_results['相对估值'] = relative_result
    
    # 资产基础估值
    asset_result = asset_based_valuation(financial_data)
    if asset_result:
        valuation_results['资产基础估值'] = asset_result
    
    # 蒙特卡洛模拟
    mc_result = monte_carlo_valuation(historical_data)
    if mc_result:
        valuation_results['蒙特卡洛模拟'] = mc_result
    
    # 股利贴现模型
    ddm_result = dividend_discount_model(historical_data)
    if ddm_result:
        valuation_results['股利贴现模型'] = ddm_result
    
    # 风险分析
    risk_result = risk_analysis(historical_data)
    if risk_result:
        valuation_results['风险分析'] = risk_result
    
    # 3. 生成可视化图表
    print("\n📈 步骤3: 生成可视化图表")
    create_valuation_charts(historical_data, valuation_results, company_name, stock_code)
    
    # 4. 显示结果汇总
    print("\n💰 步骤4: 结果汇总")
    current_price = None
    for method, result in valuation_results.items():
        if method == '相对估值':
            current_price = result.get('当前价格', 0)
            break
    
    if current_price:
        print(f"当前股价: {current_price:.2f} 元")
    
    for method, result in valuation_results.items():
        if method == '风险分析':
            continue
            
        print(f"\n【{method}】")
        if method == 'DCF估值':
            intrinsic_value = result.get('内在价值', 0)
            premium = ((intrinsic_value - current_price) / current_price * 100) if current_price else 0
            print(f"  内在价值: {intrinsic_value:.2f} 元")
            print(f"  溢价/折价: {premium:+.2f}%")
        
        elif method == '相对估值':
            pe_value = result.get('PE估值', 0)
            pb_value = result.get('PB估值', 0)
            print(f"  PE估值: {pe_value:.2f} 元")
            print(f"  PB估值: {pb_value:.2f} 元")
        
        elif method == '资产基础估值':
            nav = result.get('每股净资产', 0)
            print(f"  每股净资产: {nav:.2f} 元")
        
        elif method == '蒙特卡洛模拟':
            sim_results = result.get('模拟结果', {})
            ci_95 = sim_results.get('95%置信区间', [0, 0])
            print(f"  平均预测价格: {sim_results.get('平均价格', 0):.2f} 元")
            print(f"  95%置信区间: {ci_95[0]:.2f} - {ci_95[1]:.2f} 元")
        
        elif method == '股利贴现模型':
            intrinsic_value = result.get('内在价值', 0)
            print(f"  内在价值: {intrinsic_value:.2f} 元")
    
    print(f"\n✅ {stock_code} 分析完成！")
    return valuation_results

# =============================================================================
# 片段 6: 独立测试函数
# =============================================================================

def test_dcf_valuation():
    """测试DCF估值函数"""
    print("🧪 测试DCF估值函数")
    financial_data = create_demo_financial_data()
    stock_info = create_demo_stock_info('600036')
    result = dcf_valuation(financial_data, stock_info)
    print(f"测试结果: {result}")

def test_relative_valuation():
    """测试相对估值函数"""
    print("🧪 测试相对估值函数")
    historical_data = create_demo_historical_data()
    financial_data = create_demo_financial_data()
    stock_info = create_demo_stock_info('600036')
    result = relative_valuation(historical_data, financial_data, stock_info)
    print(f"测试结果: {result}")

def test_data_loading():
    """测试数据加载函数"""
    print("🧪 测试数据加载函数")
    stock_info, company_name = load_stock_info('600036')
    historical_data = load_historical_data('600036')
    financial_data = load_financial_data('600036')
    print(f"公司名称: {company_name}")
    print(f"历史数据形状: {historical_data.shape}")
    print(f"财务数据: {financial_data}")

# =============================================================================
# 主程序入口
# =============================================================================

if __name__ == "__main__":
    # 运行完整分析示例
    results = run_complete_analysis('600036')
    
    # 或者运行单个测试
    # test_dcf_valuation()
    # test_relative_valuation()
    # test_data_loading()