"""
AKSHARE接口数据测试脚本
专门用于测试AKSHARE各种金融数据接口的功能和完整性
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import warnings
warnings.filterwarnings('ignore')

class AKShareTester:
    """AKSHARE接口测试器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def start_test(self):
        """开始测试"""
        self.start_time = datetime.now()
        print("🚀 AKSHARE接口测试开始")
        print("=" * 60)
        print(f"⏰ 测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def end_test(self):
        """结束测试并生成报告"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"测试耗时: {duration:.2f} 秒")
        print(f"测试完成时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 显示失败的测试
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for test_name, result in self.test_results.items():
                if result['status'] == 'FAIL':
                    print(f"  - {test_name}: {result.get('error', '未知错误')}")
    
    def _test_function(self, func, *args, **kwargs):
        """测试单个函数"""
        test_name = kwargs.pop('test_name', func.__name__)
        
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 检查结果是否有效
            if result is None:
                self.test_results[test_name] = {
                    'status': 'FAIL',
                    'error': '返回结果为None',
                    'execution_time': execution_time
                }
                return False
            
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    self.test_results[test_name] = {
                        'status': 'FAIL',
                        'error': '返回空DataFrame',
                        'execution_time': execution_time
                    }
                    return False
                else:
                    self.test_results[test_name] = {
                        'status': 'PASS',
                        'data_shape': result.shape,
                        'columns': list(result.columns),
                        'sample_data': result.head(3).to_dict(),
                        'execution_time': execution_time
                    }
                    return True
            else:
                self.test_results[test_name] = {
                    'status': 'PASS',
                    'result_type': type(result).__name__,
                    'execution_time': execution_time
                }
                return True
                
        except Exception as e:
            self.test_results[test_name] = {
                'status': 'FAIL',
                'error': str(e),
                'execution_time': 0
            }
            return False
    
    def test_stock_interfaces(self):
        """测试股票数据接口"""
        print("\n📈 测试股票数据接口")
        print("-" * 40)
        
        # 测试股票列表
        self._test_function(ak.stock_info_a_code_name, test_name="股票列表")
        
        # 测试股票基本信息
        self._test_function(ak.stock_individual_info_em, symbol="000001", test_name="股票基本信息")
        
        # 测试历史K线数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        self._test_function(ak.stock_zh_a_hist, symbol="000001", 
                           start_date=start_date, end_date=end_date, 
                           adjust="qfq", test_name="历史K线数据")
        
        # 测试实时行情
        self._test_function(ak.stock_zh_a_spot_em, test_name="实时行情")
        
        # 测试财务指标
        self._test_function(ak.stock_financial_analysis_indicator, symbol="000001", test_name="财务指标")
        
        # 测试资金流向
        self._test_function(ak.stock_individual_fund_flow, stock="000001", test_name="资金流向")
        
        # 测试龙虎榜
        self._test_function(ak.stock_sina_lhb_detail_daily, date="20240926", test_name="龙虎榜")
    
    def test_fund_interfaces(self):
        """测试基金数据接口"""
        print("\n💰 测试基金数据接口")
        print("-" * 40)
        
        # 测试基金列表
        self._test_function(ak.fund_open_fund_daily_em, test_name="开放式基金")
        
        # 测试ETF基金
        self._test_function(ak.fund_etf_fund_daily_em, test_name="ETF基金")
        
        # 测试LOF基金
        self._test_function(ak.fund_graded_fund_daily_em, test_name="分级基金")
    
    def test_futures_interfaces(self):
        """测试期货数据接口"""
        print("\n⚡ 测试期货数据接口")
        print("-" * 40)
        
        # 测试期货主力合约
        self._test_function(ak.futures_main_sina, test_name="期货主力合约")
        
        # 测试期货历史数据
        self._test_function(ak.futures_zh_hist, symbol="RB0", start_date="20240901", 
                           end_date="20240926", test_name="期货历史数据")
    
    def test_macro_interfaces(self):
        """测试宏观经济数据接口"""
        print("\n🌍 测试宏观经济数据接口")
        print("-" * 40)
        
        # 测试CPI数据
        self._test_function(ak.macro_china_cpi, test_name="CPI数据")
        
        # 测试PPI数据
        self._test_function(ak.macro_china_ppi, test_name="PPI数据")
        
        # 测试GDP数据
        self._test_function(ak.macro_china_gdp, test_name="GDP数据")
        
        # 测试利率数据
        self._test_function(ak.rate_interbank, test_name="银行间利率")
    
    def test_bond_interfaces(self):
        """测试债券数据接口"""
        print("\n📊 测试债券数据接口")
        print("-" * 40)
        
        # 测试国债收益率
        self._test_function(ak.bond_zh_us_rate, test_name="国债收益率")
        
        # 测试可转债数据
        self._test_function(ak.bond_zh_cov, test_name="可转债数据")
    
    def test_news_interfaces(self):
        """测试新闻数据接口"""
        print("\n📰 测试新闻数据接口")
        print("-" * 40)
        
        # 测试财经新闻
        self._test_function(ak.news_roll, test_name="财经新闻")
    
    def test_option_interfaces(self):
        """测试期权数据接口"""
        print("\n📋 测试期权数据接口")
        print("-" * 40)
        
        # 测试期权列表
        self._test_function(ak.option_finance_board, test_name="期权列表")
    
    def test_index_interfaces(self):
        """测试指数数据接口"""
        print("\n📈 测试指数数据接口")
        print("-" * 40)
        
        # 测试指数列表
        self._test_function(ak.index_stock_info, test_name="指数列表")
        
        # 测试指数历史数据
        self._test_function(ak.index_zh_a_hist, symbol="000001", period="daily", 
                           start_date="20240901", end_date="20240926", test_name="指数历史数据")
    
    def test_data_quality(self):
        """测试数据质量"""
        print("\n🔍 测试数据质量")
        print("-" * 40)
        
        # 测试数据完整性
        try:
            # 获取股票数据并检查质量
            stock_data = ak.stock_zh_a_hist(symbol="000001", period="daily", 
                                          start_date="20240901", end_date="20240926")
            
            if stock_data is not None and not stock_data.empty:
                # 检查缺失值
                missing_values = stock_data.isnull().sum().sum()
                # 检查重复值
                duplicates = stock_data.duplicated().sum()
                # 检查数据范围
                price_stats = stock_data[['开盘', '收盘', '最高', '最低']].describe()
                
                self.test_results['数据质量检查'] = {
                    'status': 'PASS',
                    'missing_values': int(missing_values),
                    'duplicates': int(duplicates),
                    'price_stats': price_stats.to_dict(),
                    'data_shape': stock_data.shape
                }
                print("✅ 数据质量检查通过")
            else:
                self.test_results['数据质量检查'] = {
                    'status': 'FAIL',
                    'error': '获取的数据为空'
                }
                print("❌ 数据质量检查失败")
                
        except Exception as e:
            self.test_results['数据质量检查'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"❌ 数据质量检查失败: {e}")
    
    def test_performance(self):
        """测试接口性能"""
        print("\n⚡ 测试接口性能")
        print("-" * 40)
        
        # 测试批量请求性能
        stock_codes = ["000001", "000002", "600036", "601318"]
        performance_results = []
        
        for code in stock_codes:
            try:
                start_time = time.time()
                data = ak.stock_individual_info_em(symbol=code)
                end_time = time.time()
                
                if data is not None and not data.empty:
                    performance_results.append({
                        'stock_code': code,
                        'execution_time': end_time - start_time,
                        'success': True
                    })
                else:
                    performance_results.append({
                        'stock_code': code,
                        'execution_time': end_time - start_time,
                        'success': False
                    })
                    
            except Exception as e:
                performance_results.append({
                    'stock_code': code,
                    'execution_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        avg_time = np.mean([r['execution_time'] for r in performance_results if r['success']])
        success_rate = sum(1 for r in performance_results if r['success']) / len(performance_results)
        
        self.test_results['性能测试'] = {
            'status': 'PASS' if success_rate > 0.5 else 'FAIL',
            'average_time': avg_time,
            'success_rate': success_rate,
            'details': performance_results
        }
        
        print(f"✅ 性能测试完成 - 平均响应时间: {avg_time:.3f}秒, 成功率: {success_rate:.1%}")
    
    def generate_detailed_report(self):
        """生成详细测试报告"""
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results.values() if r['status'] == 'PASS'),
                'failed_tests': sum(1 for r in self.test_results.values() if r['status'] == 'FAIL'),
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': (self.end_time - self.start_time).total_seconds()
            },
            'test_details': self.test_results
        }
        
        # 保存详细报告到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"akshare_test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 详细测试报告已保存到: {filename}")
        return report
    
    def run_comprehensive_test(self):
        """运行全面测试"""
        self.start_test()
        
        # 执行各种测试
        self.test_stock_interfaces()
        self.test_fund_interfaces()
        self.test_futures_interfaces()
        self.test_macro_interfaces()
        self.test_bond_interfaces()
        self.test_news_interfaces()
        self.test_option_interfaces()
        self.test_index_interfaces()
        self.test_data_quality()
        self.test_performance()
        
        self.end_test()
        
        # 生成详细报告
        detailed_report = self.generate_detailed_report()
        
        return detailed_report

def main():
    """主函数"""
    print("🚀 AKSHARE接口全面测试脚本")
    print("=" * 50)
    print("本脚本将测试AKSHARE的各种金融数据接口")
    print("包括股票、基金、期货、宏观经济等数据")
    print("=" * 50)
    
    # 创建测试器
    tester = AKShareTester()
    
    try:
        # 运行全面测试
        report = tester.run_comprehensive_test()
        
        print("\n🎉 测试完成！")
        print(f"📊 共测试了 {len(tester.test_results)} 个接口")
        
        # 显示简要结果
        passed = sum(1 for r in tester.test_results.values() if r['status'] == 'PASS')
        failed = len(tester.test_results) - passed
        
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📈 成功率: {passed/len(tester.test_results):.1%}")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    print("\n💡 提示: 详细的测试报告已保存为JSON文件")

if __name__ == "__main__":
    main()