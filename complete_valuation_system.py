"""
完整公司估值分析系统
包含多种估值方法、风险分析、可视化图表和详细报告
专门针对中国A股市场设计
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import akshare as ak
from datetime import datetime, timedelta
import warnings
import time
import random
import logging
import os
import glob
from scipy import stats
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('valuation_system.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class CompleteValuationSystem:
    """
    完整公司估值分析系统
    包含多种估值方法和高级分析功能
    """
    
    def __init__(self, stock_code):
        """
        初始化估值分析系统
        
        参数:
            stock_code (str): A股股票代码 (如: '000001', '600036')
        """
        self.stock_code = stock_code
        self.company_name = None
        self.stock_info = None
        self.historical_data = None
        self.financial_data = None
        self.valuation_results = {}
        self.analysis_report = ""
        
    def load_data(self):
        """加载所有必要的数据"""
        print(f"\n📊 正在加载 {self.stock_code} 的数据...")
        
        # 加载股票基本信息
        self._load_stock_info()
        
        # 加载历史价格数据
        self._load_historical_data()
        
        # 加载财务数据
        self._load_financial_data()
        
        print("✅ 数据加载完成")
    
    def _load_stock_info(self):
        """加载股票基本信息"""
        try:
            logger.info(f"开始加载股票 {self.stock_code} 的基本信息")
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if stock_info is not None and not stock_info.empty:
                self.stock_info = stock_info
                # 提取公司名称
                name_info = stock_info[stock_info['item'] == '股票简称']
                if not name_info.empty:
                    self.company_name = name_info.iloc[0]['value']
                    logger.info(f"成功加载股票信息: {self.company_name}")
                else:
                    logger.warning("未找到股票简称信息，使用演示数据")
                    self._create_demo_data()
                
                # 尝试获取股息率信息
                self._load_dividend_yield()
            else:
                logger.warning("股票信息为空，使用演示数据")
                self._create_demo_data()
        except Exception as e:
            logger.error(f"加载股票信息失败: {e}")
            logger.info("使用演示数据继续分析")
            self._create_demo_data()
    
    def _load_dividend_yield(self):
        """加载股息率信息"""
        try:
            # 尝试从多个数据源获取股息率
            dividend_yield = None
            
            # 方法1: 从实时数据获取
            try:
                realtime_data = ak.stock_zh_a_spot_em()
                if realtime_data is not None and not realtime_data.empty:
                    stock_data = realtime_data[realtime_data['代码'] == self.stock_code]
                    if not stock_data.empty:
                        # 有些数据源可能包含股息率信息
                        if '股息率' in stock_data.columns:
                            dividend_yield = stock_data.iloc[0]['股息率']
                            logger.info(f"从实时数据获取股息率: {dividend_yield}")
            except Exception as e:
                logger.warning(f"从实时数据获取股息率失败: {e}")
            
            # 方法2: 从财务数据估算
            if dividend_yield is None and self.financial_data is not None:
                indicators = self.financial_data.get('indicators')
                if indicators is not None:
                    # 如果有每股收益和当前价格，可以估算股息率
                    eps = indicators.get('基本每股收益', indicators.get('每股收益', 0))
                    if eps > 0 and self.historical_data is not None:
                        current_price = self.historical_data['收盘'].iloc[-1]
                        # 假设分红率为30%
                        dividend_per_share = eps * 0.3
                        dividend_yield = dividend_per_share / current_price
                        logger.info(f"估算股息率: {dividend_yield*100:.2f}%")
            
            # 方法3: 使用行业平均股息率
            if dividend_yield is None:
                # 使用A股市场平均股息率作为参考
                dividend_yield = 0.03  # 3%作为默认值
                logger.info(f"使用默认股息率: {dividend_yield*100:.2f}%")
            
            # 将股息率添加到stock_info中
            if dividend_yield is not None:
                dividend_row = pd.DataFrame({
                    'item': ['股息率'],
                    'value': [f'{dividend_yield*100:.2f}%']
                })
                self.stock_info = pd.concat([self.stock_info, dividend_row], ignore_index=True)
                
        except Exception as e:
            logger.warning(f"加载股息率信息失败: {e}")
    
    def _load_historical_data(self):
        """加载历史价格数据"""
        try:
            logger.info(f"开始加载股票 {self.stock_code} 的历史价格数据")
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')
            
            k_data = ak.stock_zh_a_hist(symbol=self.stock_code,
                                      start_date=start_date,
                                      end_date=end_date,
                                      adjust="qfq")
            
            if k_data is not None and not k_data.empty:
                k_data['日期'] = pd.to_datetime(k_data['日期'])
                k_data.set_index('日期', inplace=True)
                self.historical_data = k_data
                logger.info(f"成功加载历史价格数据，共 {len(k_data)} 条记录")
            else:
                logger.warning("历史价格数据为空，使用演示数据")
                self._create_demo_data()
        except Exception as e:
            logger.error(f"加载历史价格数据失败: {e}")
            logger.info("使用演示数据继续分析")
            self._create_demo_data()
    
    def _load_financial_data(self):
        """加载财务数据"""
        try:
            logger.info(f"开始加载股票 {self.stock_code} 的财务数据")
            financial_data = {}
            
            # 财务摘要数据 - 使用可用的函数
            try:
                financial_abstract = ak.stock_financial_abstract(symbol=self.stock_code)
                if financial_abstract is not None and not financial_abstract.empty:
                    # 提取最新的财务数据（最新季度）
                    latest_data = {}
                    
                    # 查找最新的有效数据列
                    date_columns = [col for col in financial_abstract.columns if col.isdigit()]
                    if date_columns:
                        latest_date = max(date_columns)
                        latest_period_data = financial_abstract[['指标', latest_date]]
                        
                        # 转换为字典格式
                        for _, row in latest_period_data.iterrows():
                            indicator = row['指标']
                            value = row[latest_date]
                            if pd.notna(value):
                                latest_data[indicator] = value
                    
                    if latest_data:
                        financial_data['indicators'] = pd.Series(latest_data)
                        logger.info(f"成功加载财务摘要数据，最新期间: {latest_date}")
                    else:
                        logger.warning("财务摘要数据为空")
                else:
                    logger.warning("财务摘要数据为空")
            except Exception as e:
                logger.warning(f"加载财务摘要数据失败: {e}")
            
            # 实时数据
            try:
                realtime_data = ak.stock_zh_a_spot_em()
                if realtime_data is not None and not realtime_data.empty:
                    stock_data = realtime_data[realtime_data['代码'] == self.stock_code]
                    if not stock_data.empty:
                        financial_data['realtime'] = stock_data.iloc[0]
                        logger.info("成功加载实时数据")
                else:
                    logger.warning("实时数据为空")
            except Exception as e:
                logger.warning(f"加载实时数据失败: {e}")
            
            if financial_data:
                logger.info(f"财务数据加载完成，包含 {len(financial_data)} 个数据源")
                self.financial_data = financial_data
            else:
                logger.warning("所有财务数据加载失败，使用演示数据")
                self._create_demo_data()
        except Exception as e:
            logger.error(f"加载财务数据失败: {e}")
            logger.info("使用演示数据继续分析")
            self._create_demo_data()
    
    def _create_demo_data(self):
        """创建演示数据"""
        logger.info(f"为 {self.stock_code} 创建演示数据...")
        
        # 历史价格数据
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        base_price = 10 + random.random() * 40
        
        returns = np.random.normal(0.001, 0.02, 252)
        prices = base_price * np.cumprod(1 + returns)
        
        self.historical_data = pd.DataFrame({
            '收盘': prices,
            '开盘': prices * (1 + np.random.normal(0, 0.008, 252)),
            '最高': prices * (1 + np.random.normal(0.005, 0.012, 252)),
            '最低': prices * (1 - np.random.normal(0.005, 0.012, 252)),
            '成交量': np.random.randint(10000000, 50000000, 252)
        }, index=dates)
        
        # 财务数据
        revenue = 1e6 + random.random() * 9e6
        net_income = revenue * (0.08 + random.random() * 0.12)
        total_assets = revenue * (1.5 + random.random() * 1.0)
        equity = total_assets * (0.5 + random.random() * 0.2)
        
        self.financial_data = {
            'indicators': pd.Series({
                '营业总收入': revenue,
                '归母净利润': net_income,
                '净利润': net_income,
                '总资产': total_assets,
                '净资产': equity,
                '基本每股收益': net_income / 1e9,
                '每股净资产': equity / 1e9
            })
        }
        
        if self.stock_info is None:
            self.stock_info = pd.DataFrame({
                'item': ['股票名称', '行业', '总股本', '市盈率', '市净率'],
                'value': [f'{self.stock_code}演示公司', '信息技术', '100000', '25.5', '3.2']
            })
        
        # 设置演示公司名称
        if self.company_name is None:
            self.company_name = f'{self.stock_code}演示公司'
        
        logger.info("演示数据创建完成")
    
    def dcf_valuation(self, growth_rate=0.08, discount_rate=0.12, terminal_growth=0.03, years=5):
        """DCF估值法"""
        try:
            logger.info("开始执行DCF估值分析")
            
            if self.financial_data is None:
                logger.warning("财务数据为空，无法执行DCF估值")
                return None
            
            indicators = self.financial_data.get('indicators')
            if indicators is None:
                logger.warning("财务指标为空，无法执行DCF估值")
                return None
            
            net_income = indicators.get('净利润', indicators.get('归母净利润', 0))
            if net_income <= 0:
                logger.warning("净利润为负或为零，无法执行DCF估值")
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
            if self.stock_info is not None:
                shares_info = self.stock_info[self.stock_info['item'] == '总股本']
                if not shares_info.empty:
                    try:
                        total_shares = float(shares_info.iloc[0]['value']) * 1e4
                        logger.info(f"使用实际总股本: {total_shares}")
                    except Exception as e:
                        logger.warning(f"解析总股本失败: {e}，使用默认值")
                        pass
            
            intrinsic_value_per_share = enterprise_value / total_shares
            
            logger.info(f"DCF估值完成: 内在价值 {intrinsic_value_per_share:.2f} 元")
            
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
            logger.error(f"DCF估值失败: {e}")
            return None
    
    def relative_valuation(self):
        """相对估值法"""
        try:
            logger.info("开始执行相对估值分析")
            
            if self.historical_data is None:
                logger.warning("历史数据为空，无法执行相对估值")
                return None
            
            current_price = self.historical_data['收盘'].iloc[-1]
            
            # 获取估值指标
            pe_ratio = 25.0
            pb_ratio = 3.0
            
            if self.stock_info is not None:
                pe_info = self.stock_info[self.stock_info['item'] == '市盈率']
                if not pe_info.empty:
                    try:
                        pe_ratio = float(pe_info.iloc[0]['value'])
                        logger.info(f"使用实际市盈率: {pe_ratio}")
                    except Exception as e:
                        logger.warning(f"解析市盈率失败: {e}，使用默认值")
                        pass
            
            # 计算每股收益和每股净资产
            indicators = self.financial_data.get('indicators') if self.financial_data else None
            
            eps = indicators.get('基本每股收益', indicators.get('每股收益', 0)) if indicators is not None else 0
            bvps = indicators.get('每股净资产', 0) if indicators is not None else 0
            
            print(f"每股净收益：{eps}")
            print(f'每股净资产{bvps}')
            # 相对估值计算
            pe_value = eps * pe_ratio if eps > 0 else current_price
            pb_value = bvps * pb_ratio if bvps > 0 else current_price
            
            logger.info(f"相对估值完成: PE估值 {pe_value:.2f} 元, PB估值 {pb_value:.2f} 元")
            
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
            logger.error(f"相对估值失败: {e}")
            return None
    
    def asset_based_valuation(self):
        """资产基础估值法"""
        try:
            logger.info("开始执行资产基础估值分析")
            
            indicators = self.financial_data.get('indicators') if self.financial_data else None
            if indicators is None:
                logger.warning("财务指标为空，无法执行资产基础估值")
                return None
            
            nav_per_share = indicators.get('每股净资产', 0)
            
            logger.info(f"资产基础估值完成: 每股净资产 {nav_per_share:.2f} 元")
            
            return {
                'method': '资产基础估值',
                '每股净资产': nav_per_share,
                '总资产': indicators.get('总资产', 0),
                '净资产': indicators.get('净资产', 0)
            }
        except Exception as e:
            logger.error(f"资产基础估值失败: {e}")
            return None
    
    def monte_carlo_valuation(self, num_simulations=1000):
        """蒙特卡洛模拟估值"""
        try:
            logger.info(f"开始执行蒙特卡洛模拟估值，模拟次数: {num_simulations}")
            
            if self.historical_data is None:
                logger.warning("历史数据为空，无法执行蒙特卡洛模拟")
                return None
            
            current_price = self.historical_data['收盘'].iloc[-1]
            
            returns = self.historical_data['收盘'].pct_change().dropna()
            if len(returns) == 0:
                logger.warning("收益率数据为空，无法执行蒙特卡洛模拟")
                return None
            
            mean_return = returns.mean()
            std_return = returns.std()
            
            simulated_prices = []
            for i in range(num_simulations):
                future_returns = np.random.normal(mean_return, std_return, 252)
                simulated_price = current_price * np.prod(1 + future_returns)
                simulated_prices.append(simulated_price)
                
                # 每100次模拟记录一次进度
                if (i + 1) % 100 == 0:
                    logger.info(f"蒙特卡洛模拟进度: {i + 1}/{num_simulations}")
            
            simulated_prices = np.array(simulated_prices)
            
            avg_price = np.mean(simulated_prices)
            ci_95 = np.percentile(simulated_prices, [2.5, 97.5])
            
            logger.info(f"蒙特卡洛模拟完成: 平均价格 {avg_price:.2f} 元, 95%置信区间 {ci_95[0]:.2f}-{ci_95[1]:.2f} 元")
            
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
            logger.error(f"蒙特卡洛模拟失败: {e}")
            return None
    
    def dividend_discount_model(self, dividend_growth=0.05, required_return=0.1):
        """股利贴现模型"""
        try:
            logger.info("开始执行股利贴现模型分析")
            
            if self.historical_data is None:
                logger.warning("历史数据为空，无法执行股利贴现模型")
                return None
            
            current_price = self.historical_data['收盘'].iloc[-1]
            
            dividend_yield = 0.03
            current_dividend = current_price * dividend_yield
            
            if required_return > dividend_growth:
                intrinsic_value = current_dividend * (1 + dividend_growth) / (required_return - dividend_growth)
                logger.info(f"使用标准DDM公式计算内在价值")
            else:
                intrinsic_value = current_price
                logger.warning("要求回报率小于股息增长率，使用当前价格作为内在价值")
            
            logger.info(f"股利贴现模型完成: 内在价值 {intrinsic_value:.2f} 元")
            
            return {
                'method': '股利贴现模型',
                '内在价值': intrinsic_value,
                '当前股息': current_dividend,
                '股息增长率': f"{dividend_growth*100:.1f}%",
                '要求回报率': f"{required_return*100:.1f}%"
            }
        except Exception as e:
            logger.error(f"股利贴现模型失败: {e}")
            return None
    
    def risk_analysis(self):
        """风险分析"""
        try:
            logger.info("开始执行风险分析")
            
            if self.historical_data is None:
                logger.warning("历史数据为空，无法执行风险分析")
                return None
            
            returns = self.historical_data['收盘'].pct_change().dropna()
            if len(returns) == 0:
                logger.warning("收益率数据为空，无法执行风险分析")
                return None
            
            # 基础风险指标
            volatility = returns.std() * np.sqrt(252)  # 年化波动率
            annual_return = returns.mean() * 252  # 年化收益率
            
            # 夏普比率
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # 最大回撤
            max_drawdown = self._calculate_max_drawdown()
            
            # 卡玛比率 (Calmar Ratio)
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # 索提诺比率 (Sortino Ratio)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            
            # 信息比率 (Information Ratio)
            information_ratio = self._calculate_information_ratio(returns)
            
            # VaR和条件VaR
            var_95 = np.percentile(returns, 5)
            expected_shortfall = returns[returns <= var_95].mean()
            
            logger.info(f"风险分析完成: 年化波动率 {volatility*100:.2f}%, 夏普比率 {sharpe_ratio:.2f}")
            logger.info(f"最大回撤 {max_drawdown*100:.2f}%, 卡玛比率 {calmar_ratio:.2f}")
            logger.info(f"索提诺比率 {sortino_ratio:.2f}, 信息比率 {information_ratio:.2f}")
            
            return {
                '年化波动率': volatility,
                '年化收益率': annual_return,
                '夏普比率': sharpe_ratio,
                '最大回撤': max_drawdown,
                '卡玛比率': calmar_ratio,
                '索提诺比率': sortino_ratio,
                '信息比率': information_ratio,
                '95%VaR': var_95,
                '条件VaR': expected_shortfall
            }
        except Exception as e:
            logger.error(f"风险分析失败: {e}")
            return None
    
    def _calculate_max_drawdown(self):
        """计算最大回撤"""
        if self.historical_data is None:
            return 0
        
        prices = self.historical_data['收盘']
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        max_drawdown = drawdown.min()
        
        return max_drawdown
    
    def _calculate_sortino_ratio(self, returns, risk_free_rate=0.03):
        """计算索提诺比率 (Sortino Ratio)"""
        try:
            annual_return = returns.mean() * 252
            downside_returns = returns[returns < 0]
            
            if len(downside_returns) == 0:
                return 0
                
            downside_volatility = downside_returns.std() * np.sqrt(252)
            
            if downside_volatility > 0:
                sortino_ratio = (annual_return - risk_free_rate) / downside_volatility
            else:
                sortino_ratio = 0
                
            return sortino_ratio
        except Exception as e:
            logger.warning(f"索提诺比率计算失败: {e}")
            return 0
    
    def _calculate_information_ratio(self, returns, benchmark_returns=None):
        """计算信息比率 (Information Ratio)"""
        try:
            # 如果没有基准收益率，使用市场平均收益率作为基准
            if benchmark_returns is None:
                # 使用简单的市场基准假设 (例如年化8%)
                benchmark_daily_return = 0.08 / 252
                excess_returns = returns - benchmark_daily_return
            else:
                excess_returns = returns - benchmark_returns
            
            tracking_error = excess_returns.std() * np.sqrt(252)
            mean_excess_return = excess_returns.mean() * 252
            
            if tracking_error > 0:
                information_ratio = mean_excess_return / tracking_error
            else:
                information_ratio = 0
                
            return information_ratio
        except Exception as e:
            logger.warning(f"信息比率计算失败: {e}")
            return 0
    
    def comprehensive_analysis(self):
        """综合估值分析"""
        print(f"\n{'='*60}")
        print(f"📈 完整估值分析报告 - {self.company_name} ({self.stock_code})")
        print(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # 加载数据
        self.load_data()
        
        # 显示公司基本信息
        self._display_company_info()
        
        # 执行各种估值方法
        print(f"\n🔍【估值分析开始】")
        
        valuation_methods = [
            ('DCF估值', self.dcf_valuation),
            ('相对估值', self.relative_valuation),
            ('资产基础估值', self.asset_based_valuation),
            ('蒙特卡洛模拟', self.monte_carlo_valuation),
            ('股利贴现模型', self.dividend_discount_model)
        ]
        
        for method_name, method_func in valuation_methods:
            result = method_func()
            if result:
                self.valuation_results[method_name] = result
                print(f"✅ {method_name}完成")
        
        # 执行风险分析
        print(f"\n📊【风险分析开始】")
        
        risk_result = self.risk_analysis()
        if risk_result:
            self.valuation_results['风险分析'] = risk_result
            print("✅ 风险分析完成")
        
        # 生成分析报告
        self._generate_analysis_report()
        
        # 显示估值结果
        self._display_valuation_results()
        
        # 生成可视化图表
        self._create_comprehensive_charts()
        
        return self.valuation_results
    
    def _display_company_info(self):
        """显示公司基本信息"""
        print(f"\n📋【公司基本信息】")
        
        if self.stock_info is not None:
            for _, row in self.stock_info.iterrows():
                if row['item'] in ['股票名称', '行业', '总股本', '市盈率', '市净率', '股息率']:
                    print(f"  {row['item']}: {row['value']}")
        
        if self.historical_data is not None:
            current_price = self.historical_data['收盘'].iloc[-1]
            print(f"  当前价格: {current_price:.2f} 元")
            
            if len(self.historical_data) >= 20:
                price_20d_ago = self.historical_data['收盘'].iloc[-20]
                change_20d = (current_price - price_20d_ago) / price_20d_ago * 100
                print(f"  20日涨跌幅: {change_20d:+.2f}%")
    
    def _generate_analysis_report(self):
        """生成详细分析报告"""
        report = f"""
📊 公司估值分析报告 - {self.company_name} ({self.stock_code})
⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋【公司基本信息】
"""
        
        # 添加股票基本信息
        if self.stock_info is not None:
            for _, row in self.stock_info.iterrows():
                if row['item'] in ['股票名称', '股票简称', '行业', '总股本', '市盈率', '市净率', '所属板块', '股息率']:
                    report += f"  {row['item']}: {row['value']}\n"
        
        # 添加当前价格信息
        if self.historical_data is not None:
            current_price = self.historical_data['收盘'].iloc[-1]
            report += f"  当前价格: {current_price:.2f} 元\n"
            
            if len(self.historical_data) >= 20:
                price_20d_ago = self.historical_data['收盘'].iloc[-20]
                change_20d = (current_price - price_20d_ago) / price_20d_ago * 100
                report += f"  20日涨跌幅: {change_20d:+.2f}%\n"
        
        # 添加财务数据信息
        report += "\n💰【财务数据摘要】\n"
        if self.financial_data is not None:
            indicators = self.financial_data.get('indicators')
            if indicators is not None:
                financial_metrics = {
                    '营业总收入': '营业收入',
                    '归母净利润': '归母净利润',
                    '净利润': '净利润',
                    '总资产': '总资产',
                    '净资产': '净资产',
                    '基本每股收益': '每股收益',
                    '每股净资产': '每股净资产'
                }
                
                for key, display_name in financial_metrics.items():
                    if key in indicators:
                        value = indicators[key]
                        if value > 1e8:  # 大额数据转换为亿元
                            report += f"  {display_name}: {value/1e8:.2f} 亿元\n"
                        elif value > 1e4:  # 中等数据转换为万元
                            report += f"  {display_name}: {value/1e4:.2f} 万元\n"
                        else:
                            report += f"  {display_name}: {value:.2f} 元\n"
            
            realtime_data = self.financial_data.get('realtime')
            if realtime_data is not None:
                report += f"  最新涨跌幅: {realtime_data.get('涨跌幅', 'N/A')}\n"
                report += f"  成交量: {realtime_data.get('成交量', 'N/A')}\n"
        
        report += """
💡【估值方法说明】
1. DCF估值: 基于未来现金流折现的内在价值计算
2. 相对估值: 基于市盈率、市净率等相对指标
3. 资产基础估值: 基于公司净资产价值
4. 蒙特卡洛模拟: 基于随机过程的概率分布分析
5. 股利贴现模型: 基于未来股息折现的估值方法

📈【估值结果汇总】
"""
        
        current_price = None
        for method, result in self.valuation_results.items():
            if method == '相对估值':
                current_price = result.get('当前价格', 0)
                break
        
        if current_price:
            report += f"当前股价: {current_price:.2f} 元\n\n"
        
        for method, result in self.valuation_results.items():
            if method == '风险分析':
                continue
                
            report += f"【{method}】\n"
            
            if method == 'DCF估值':
                intrinsic_value = result.get('内在价值', 0)
                premium = ((intrinsic_value - current_price) / current_price * 100) if current_price else 0
                report += f"  内在价值: {intrinsic_value:.2f} 元\n"
                report += f"  溢价/折价: {premium:+.2f}%\n"
            
            elif method == '相对估值':
                pe_value = result.get('PE估值', 0)
                pb_value = result.get('PB估值', 0)
                report += f"  PE估值: {pe_value:.2f} 元\n"
                report += f"  PB估值: {pb_value:.2f} 元\n"
            
            elif method == '资产基础估值':
                nav = result.get('每股净资产', 0)
                report += f"  每股净资产: {nav:.2f} 元\n"
            
            elif method == '蒙特卡洛模拟':
                sim_results = result.get('模拟结果', {})
                ci_95 = sim_results.get('95%置信区间', [0, 0])
                report += f"  平均预测价格: {sim_results.get('平均价格', 0):.2f} 元\n"
                report += f"  95%置信区间: {ci_95[0]:.2f} - {ci_95[1]:.2f} 元\n"
            
            elif method == '股利贴现模型':
                intrinsic_value = result.get('内在价值', 0)
                report += f"  内在价值: {intrinsic_value:.2f} 元\n"
            
            report += "\n"
        
        # 添加风险分析结果
        if '风险分析' in self.valuation_results:
            risk_result = self.valuation_results['风险分析']
            report += "📊【风险分析结果】\n"
            report += f"  年化收益率: {risk_result.get('年化收益率', 0)*100:.2f}%\n"
            report += f"  年化波动率: {risk_result.get('年化波动率', 0)*100:.2f}%\n"
            report += f"  夏普比率: {risk_result.get('夏普比率', 0):.2f}\n"
            report += f"  最大回撤: {abs(risk_result.get('最大回撤', 0))*100:.2f}%\n"
            report += f"  卡玛比率: {risk_result.get('卡玛比率', 0):.2f}\n"
            report += f"  索提诺比率: {risk_result.get('索提诺比率', 0):.2f}\n"
            report += f"  信息比率: {risk_result.get('信息比率', 0):.2f}\n"
            report += f"  95%VaR: {risk_result.get('95%VaR', 0)*100:.2f}%\n"
        
        self.analysis_report = report
    
    def _display_valuation_results(self):
        """显示估值结果"""
        print(f"\n{'='*60}")
        print("💰 估值结果汇总")
        print(f"{'='*60}")
        
        print(self.analysis_report)
    
    def _create_comprehensive_charts(self):
        """创建综合可视化图表"""
        try:
            logger.info("开始生成可视化图表")
            
            # 使用非交互式后端，避免阻塞
            plt.switch_backend('Agg')  # 使用非交互式后端
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'{self.company_name} ({self.stock_code}) - 完整估值分析', fontsize=16, fontweight='bold')
            
            # 1. 价格走势图
            ax1 = axes[0, 0]
            if self.historical_data is not None:
                ax1.plot(self.historical_data.index, self.historical_data['收盘'], linewidth=1.5, color='blue')
                ax1.set_title('历史价格走势', fontsize=12)
                ax1.set_ylabel('价格 (元)', fontsize=10)
                ax1.grid(True, alpha=0.3)
            
            # 2. 估值方法对比
            ax2 = axes[0, 1]
            methods = []
            values = []
            current_price = None
            
            for method, result in self.valuation_results.items():
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
            if '风险分析' in self.valuation_results:
                risk_result = self.valuation_results['风险分析']
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
            if '蒙特卡洛模拟' in self.valuation_results:
                mc_result = self.valuation_results['蒙特卡洛模拟']
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
            
            # 保存图表到文件而不是显示
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"估值图表_{self.company_name}_{self.stock_code}_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()  # 关闭图表释放内存
            
            logger.info(f"图表已保存到文件: {filename}")
            print(f"📊 可视化图表已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"图表生成失败: {e}")
            print(f"❌ 图表生成失败: {e}")
    
    def _cleanup_old_files(self):
        """清理旧的估值文件，只保留最近3个图表和报告"""
        try:
            logger.info("开始清理旧的估值文件")
            
            # 查找所有估值图表文件
            chart_pattern = "估值图表_*.png"
            report_pattern = "估值报告_*.txt"
            
            chart_files = glob.glob(chart_pattern)
            report_files = glob.glob(report_pattern)
            
            # 按修改时间排序，最新的在前面
            chart_files.sort(key=os.path.getmtime, reverse=True)
            report_files.sort(key=os.path.getmtime, reverse=True)
            
            # 保留最近3个文件，删除其他的
            files_to_keep = 3
            
            # 删除旧的图表文件
            for old_chart in chart_files[files_to_keep:]:
                try:
                    os.remove(old_chart)
                    logger.info(f"删除旧图表文件: {old_chart}")
                except Exception as e:
                    logger.warning(f"删除图表文件失败 {old_chart}: {e}")
            
            # 删除旧的报告文件
            for old_report in report_files[files_to_keep:]:
                try:
                    os.remove(old_report)
                    logger.info(f"删除旧报告文件: {old_report}")
                except Exception as e:
                    logger.warning(f"删除报告文件失败 {old_report}: {e}")
            
            logger.info(f"文件清理完成，保留最近 {files_to_keep} 个图表和报告文件")
            
        except Exception as e:
            logger.error(f"文件清理失败: {e}")

    def save_report(self, filename=None, cleanup=True):
        """保存分析报告到文件
        
        参数:
            filename: 文件名，如果为None则自动生成
            cleanup: 是否清理旧文件，批量分析时设为False
        """
        if filename is None:
            # 使用公司名称作为文件名的一部分，但移除特殊字符
            safe_company_name = "".join(c for c in self.company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"估值报告_{safe_company_name}_{self.stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.analysis_report)
            print(f"✅ 分析报告已保存到: {filename}")
            
            # 保存后清理旧文件（仅在单只股票分析时执行）
            if cleanup:
                self._cleanup_old_files()
            
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

def analyze_single_stock(stock_code, cleanup=True):
    """分析单只股票
    
    参数:
        stock_code: 股票代码
        cleanup: 是否清理旧文件，批量分析时设为False
    """
    print(f"\n📈 开始分析 {stock_code}...")
    
    # 创建分析器并执行分析
    analyzer = CompleteValuationSystem(stock_code)
    
    try:
        results = analyzer.comprehensive_analysis()
        print(f"\n✅ {stock_code} 分析完成！")
        
        # 自动保存报告
        analyzer.save_report(cleanup=cleanup)
        
        return True
    except Exception as e:
        print(f"❌ {stock_code} 分析失败: {e}")
        return False

def analyze_batch_stocks(csv_file='a_share_leaders.csv'):
    """批量分析股票"""
    try:
        # 读取CSV文件
        leaders_df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"📋 读取到 {len(leaders_df)} 只龙头企业股票")
        
        success_count = 0
        failed_stocks = []
        
        for index, row in leaders_df.iterrows():
            stock_code = str(row['股票代码']).zfill(6)  # 确保6位代码
            company_name = row['公司名称']
            industry = row['行业']
            
            print(f"\n{'='*60}")
            print(f"📊 分析第 {index+1}/{len(leaders_df)} 只股票: {company_name} ({stock_code})")
            print(f"🏢 行业: {industry}")
            print(f"{'='*60}")
            
            # 批量分析时不清理文件
            if analyze_single_stock(stock_code, cleanup=False):
                success_count += 1
            else:
                failed_stocks.append(f"{company_name}({stock_code})")
            
            # 添加延迟避免请求过于频繁
            time.sleep(2)
        
        print(f"\n🎉 批量分析完成！")
        print(f"✅ 成功分析: {success_count} 只股票")
        if failed_stocks:
            print(f"❌ 分析失败: {len(failed_stocks)} 只股票")
            print("失败股票列表:", ", ".join(failed_stocks))
        
    except Exception as e:
        print(f"❌ 批量分析失败: {e}")

def main():
    """主函数"""
    print("🚀 完整公司估值分析系统")
    print("=" * 50)
    print("包含多种估值方法、风险分析和可视化图表")
    print("=" * 50)
    
    while True:
        print("\n请选择分析模式:")
        print("1. 单只股票分析")
        print("2. 批量分析龙头企业")
        print("3. 退出程序")
        
        choice = input("请输入选择 (1/2/3): ").strip()
        
        if choice == '1':
            # 单只股票分析
            stock_code = input("请输入A股股票代码 (如600036): ").strip()
            
            if not stock_code:
                stock_code = '600036'  # 默认分析招商银行
            
            analyze_single_stock(stock_code, cleanup=True)
            break
            
        elif choice == '2':
            # 批量分析
            csv_file = input("请输入龙头企业CSV文件路径 (默认: a_share_leaders.csv): ").strip()
            if not csv_file:
                csv_file = 'a_share_leaders.csv'
            
            analyze_batch_stocks(csv_file)
            break
            
        elif choice == '3':
            print("👋 程序退出")
            return
            
        else:
            print("❌ 无效选择，请重新输入")
    
    print("\n🎉 程序运行完成！")

if __name__ == "__main__":
    main()