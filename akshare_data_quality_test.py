"""
AKSHARE数据质量测试脚本
专门测试AKSHARE接口返回数据的质量和完整性
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DataQualityTester:
    """数据质量测试器"""
    
    def __init__(self):
        self.quality_results = {}
    
    def test_data_completeness(self, data, test_name):
        """测试数据完整性"""
        if data is None:
            return {
                'status': 'FAIL',
                'error': '数据为None',
                'completeness_score': 0
            }
        
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return {
                    'status': 'FAIL',
                    'error': 'DataFrame为空',
                    'completeness_score': 0
                }
            
            # 计算完整性指标
            total_cells = data.size
            missing_cells = data.isnull().sum().sum()
            completeness_ratio = 1 - (missing_cells / total_cells) if total_cells > 0 else 0
            
            return {
                'status': 'PASS' if completeness_ratio > 0.9 else 'WARNING',
                'data_shape': data.shape,
                'missing_cells': int(missing_cells),
                'total_cells': total_cells,
                'completeness_score': completeness_ratio,
                'column_missing': data.isnull().sum().to_dict()
            }
        
        return {
            'status': 'PASS',
            'result_type': type(data).__name__,
            'completeness_score': 1.0
        }
    
    def test_data_consistency(self, data, test_name):
        """测试数据一致性"""
        if not isinstance(data, pd.DataFrame) or data.empty:
            return {
                'status': 'SKIP',
                'reason': '非DataFrame或空数据'
            }
        
        try:
            issues = []
            
            # 检查数值列的合理性
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            
            for col in numeric_columns:
                col_data = data[col]
                
                # 检查异常值（使用IQR方法）
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                if len(outliers) > 0:
                    issues.append(f"{col}列有{len(outliers)}个异常值")
            
            # 检查日期列的连续性（如果存在）
            date_columns = data.select_dtypes(include=['datetime64']).columns
            for col in date_columns:
                if len(data) > 1:
                    date_diff = data[col].diff().dropna()
                    if not all(date_diff >= timedelta(days=0)):
                        issues.append(f"{col}列日期不连续")
            
            return {
                'status': 'WARNING' if issues else 'PASS',
                'issues': issues,
                'numeric_columns_count': len(numeric_columns),
                'date_columns_count': len(date_columns)
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': f"一致性检查错误: {str(e)}"
            }
    
    def test_data_freshness(self, data, test_name):
        """测试数据新鲜度"""
        if not isinstance(data, pd.DataFrame) or data.empty:
            return {
                'status': 'SKIP',
                'reason': '非DataFrame或空数据'
            }
        
        try:
            # 查找可能包含日期的列
            date_columns = []
            for col in data.columns:
                if any(keyword in col.lower() for keyword in ['date', '时间', '日期', 'time']):
                    date_columns.append(col)
                elif data[col].dtype == 'object':
                    # 尝试转换日期
                    try:
                        pd.to_datetime(data[col].head())
                        date_columns.append(col)
                    except:
                        pass
            
            freshness_info = {}
            for col in date_columns:
                try:
                    dates = pd.to_datetime(data[col])
                    latest_date = dates.max()
                    days_since_update = (datetime.now() - latest_date).days
                    
                    freshness_info[col] = {
                        'latest_date': latest_date.strftime('%Y-%m-%d'),
                        'days_since_update': days_since_update,
                        'freshness_status': 'FRESH' if days_since_update <= 1 else 'STALE'
                    }
                except:
                    continue
            
            return {
                'status': 'PASS',
                'date_columns_found': len(date_columns),
                'freshness_info': freshness_info
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': f"新鲜度检查错误: {str(e)}"
            }
    
    def test_stock_data_quality(self):
        """测试股票数据质量"""
        print("📈 测试股票数据质量")
        print("-" * 40)
        
        test_cases = [
            ("股票基本信息", lambda: ak.stock_individual_info_em(symbol="000001")),
            ("实时行情", ak.stock_zh_a_spot_em),
            ("历史K线", lambda: ak.stock_zh_a_hist(symbol="000001", 
                                                 start_date="20240901", 
                                                 end_date="20240926")),
        ]
        
        for name, data_func in test_cases:
            try:
                data = data_func()
                print(f"\n🔍 测试: {name}")
                
                # 完整性测试
                completeness = self.test_data_completeness(data, name)
                print(f"  完整性: {completeness['status']} (得分: {completeness.get('completeness_score', 0):.1%})")
                
                # 一致性测试
                consistency = self.test_data_consistency(data, name)
                print(f"  一致性: {consistency['status']}")
                if consistency.get('issues'):
                    for issue in consistency['issues']:
                        print(f"    - {issue}")
                
                # 新鲜度测试
                freshness = self.test_data_freshness(data, name)
                print(f"  新鲜度: {freshness['status']}")
                if freshness.get('freshness_info'):
                    for col, info in freshness['freshness_info'].items():
                        print(f"    - {col}: {info['latest_date']} ({info['days_since_update']}天前)")
                
                self.quality_results[name] = {
                    'completeness': completeness,
                    'consistency': consistency,
                    'freshness': freshness
                }
                
            except Exception as e:
                print(f"❌ {name}测试失败: {e}")
                self.quality_results[name] = {
                    'error': str(e)
                }
    
    def test_fund_data_quality(self):
        """测试基金数据质量"""
        print("\n💰 测试基金数据质量")
        print("-" * 40)
        
        try:
            fund_data = ak.fund_open_fund_daily_em()
            print(f"🔍 测试: 开放式基金数据")
            
            completeness = self.test_data_completeness(fund_data, "开放式基金")
            print(f"  完整性: {completeness['status']}")
            
            consistency = self.test_data_consistency(fund_data, "开放式基金")
            print(f"  一致性: {consistency['status']}")
            
            freshness = self.test_data_freshness(fund_data, "开放式基金")
            print(f"  新鲜度: {freshness['status']}")
            
            self.quality_results['开放式基金'] = {
                'completeness': completeness,
                'consistency': consistency,
                'freshness': freshness
            }
            
        except Exception as e:
            print(f"❌ 基金数据测试失败: {e}")
    
    def test_macro_data_quality(self):
        """测试宏观经济数据质量"""
        print("\n🌍 测试宏观经济数据质量")
        print("-" * 40)
        
        macro_tests = [
            ("CPI数据", ak.macro_china_cpi),
            ("PPI数据", ak.macro_china_ppi),
            ("GDP数据", ak.macro_china_gdp),
        ]
        
        for name, data_func in macro_tests:
            try:
                data = data_func()
                print(f"\n🔍 测试: {name}")
                
                completeness = self.test_data_completeness(data, name)
                print(f"  完整性: {completeness['status']}")
                
                consistency = self.test_data_consistency(data, name)
                print(f"  一致性: {consistency['status']}")
                
                freshness = self.test_data_freshness(data, name)
                print(f"  新鲜度: {freshness['status']}")
                
                self.quality_results[name] = {
                    'completeness': completeness,
                    'consistency': consistency,
                    'freshness': freshness
                }
                
            except Exception as e:
                print(f"❌ {name}测试失败: {e}")
    
    def generate_quality_report(self):
        """生成数据质量报告"""
        print("\n" + "=" * 60)
        print("📊 数据质量报告汇总")
        print("=" * 60)
        
        total_tests = len(self.quality_results)
        if total_tests == 0:
            print("❌ 没有可用的测试结果")
            return
        
        # 统计各维度质量
        completeness_scores = []
        consistency_status = []
        freshness_status = []
        
        for test_name, results in self.quality_results.items():
            if 'error' in results:
                continue
                
            comp = results['completeness']
            cons = results['consistency']
            fresh = results['freshness']
            
            if 'completeness_score' in comp:
                completeness_scores.append(comp['completeness_score'])
            
            consistency_status.append(cons['status'])
            freshness_status.append(fresh['status'])
        
        if completeness_scores:
            avg_completeness = np.mean(completeness_scores)
            print(f"平均完整性得分: {avg_completeness:.1%}")
        
        print(f"一致性通过率: {consistency_status.count('PASS')}/{len(consistency_status)}")
        print(f"新鲜度通过率: {freshness_status.count('PASS')}/{len(freshness_status)}")
        
        # 显示详细结果
        print(f"\n📋 详细结果:")
        for test_name, results in self.quality_results.items():
            if 'error' in results:
                print(f"❌ {test_name}: {results['error']}")
            else:
                comp = results['completeness']
                cons = results['consistency']
                fresh = results['freshness']
                
                status_icon = "✅" if comp['status'] == 'PASS' and cons['status'] == 'PASS' else "⚠️"
                print(f"{status_icon} {test_name}:")
                print(f"  完整性: {comp['status']} ({comp.get('completeness_score', 0):.1%})")
                print(f"  一致性: {cons['status']}")
                print(f"  新鲜度: {fresh['status']}")
    
    def run_comprehensive_quality_test(self):
        """运行全面的数据质量测试"""
        print("🚀 AKSHARE数据质量全面测试")
        print("=" * 60)
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.test_stock_data_quality()
        self.test_fund_data_quality()
        self.test_macro_data_quality()
        
        self.generate_quality_report()
        
        return self.quality_results

def main():
    """主函数"""
    print("🚀 AKSHARE数据质量测试工具")
    print("=" * 50)
    print("本工具专门测试AKSHARE接口返回数据的质量")
    print("包括完整性、一致性、新鲜度等维度")
    print("=" * 50)
    
    tester = DataQualityTester()
    
    try:
        results = tester.run_comprehensive_quality_test()
        print("\n🎉 数据质量测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()