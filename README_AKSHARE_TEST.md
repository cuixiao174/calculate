# AKSHARE接口测试脚本套件

本套件包含多个专门用于测试AKSHARE金融数据接口的Python脚本，帮助您全面验证AKSHARE接口的功能、性能和数据质量。

## 📁 文件说明

### 1. `akshare_test_script.py` - 全面测试脚本
**功能**: 完整的AKSHARE接口测试，包含所有主要数据类型的测试
**特点**:
- 测试股票、基金、期货、宏观经济、债券、新闻、期权、指数等接口
- 包含性能测试和数据质量检查
- 生成详细的JSON格式测试报告
- 统计测试成功率和响应时间

**使用方法**:
```bash
python akshare_test_script.py
```

### 2. `akshare_quick_test.py` - 快速测试脚本
**功能**: 日常快速检查AKSHARE主要接口状态
**特点**:
- 快速测试核心接口的可用性
- 显示简洁的测试结果
- 包含特定股票数据完整性测试
- 检查AKSHARE版本和模块信息

**使用方法**:
```bash
python akshare_quick_test.py
```

### 3. `akshare_data_quality_test.py` - 数据质量测试脚本
**功能**: 专门测试AKSHARE接口返回数据的质量
**特点**:
- 测试数据完整性（缺失值检查）
- 测试数据一致性（异常值检测）
- 测试数据新鲜度（更新时间检查）
- 生成详细的数据质量报告

**使用方法**:
```bash
python akshare_data_quality_test.py
```

## 🚀 快速开始

### 环境要求
```bash
pip install akshare pandas numpy matplotlib
```

### 运行所有测试
```bash
# 1. 先运行快速测试了解基本状态
python akshare_quick_test.py

# 2. 运行数据质量测试
python akshare_data_quality_test.py

# 3. 运行全面测试（耗时较长）
python akshare_test_script.py
```

## 📊 测试内容详解

### 股票数据接口测试
- ✅ 股票列表 (`stock_info_a_code_name`)
- ✅ 股票基本信息 (`stock_individual_info_em`)
- ✅ 历史K线数据 (`stock_zh_a_hist`)
- ✅ 实时行情 (`stock_zh_a_spot_em`)
- ✅ 财务指标 (`stock_financial_analysis_indicator`)
- ✅ 资金流向 (`stock_individual_fund_flow`)
- ✅ 龙虎榜数据 (`stock_sina_lhb_detail_daily`)

### 基金数据接口测试
- ✅ 开放式基金 (`fund_em_open_fund_daily`)
- ✅ ETF基金 (`fund_etf_hist_sina`)
- ✅ LOF基金 (`fund_em_lof_hist`)

### 期货数据接口测试
- ✅ 期货主力合约 (`futures_main_sina`)
- ✅ 期货历史数据 (`futures_zh_hist`)

### 宏观经济数据接口测试
- ✅ CPI数据 (`macro_china_cpi`)
- ✅ PPI数据 (`macro_china_ppi`)
- ✅ GDP数据 (`macro_china_gdp`)
- ✅ 银行间利率 (`rate_interbank`)

### 其他数据接口测试
- ✅ 债券数据 (`bond_zh_us_rate`, `bond_zh_cov`)
- ✅ 新闻数据 (`news_roll`)
- ✅ 期权数据 (`option_finance_board`)
- ✅ 指数数据 (`index_stock_info`, `index_zh_a_hist`)

## 🔍 测试指标说明

### 1. 接口可用性测试
- **状态检查**: 接口是否可正常调用
- **返回类型**: 验证返回数据的类型是否正确
- **数据非空**: 确保返回的数据不为空

### 2. 数据质量测试
- **完整性**: 检查数据缺失情况
- **一致性**: 检测异常值和数据逻辑
- **新鲜度**: 验证数据更新时间

### 3. 性能测试
- **响应时间**: 测量接口调用耗时
- **批量性能**: 测试批量请求的性能
- **稳定性**: 检查接口的稳定性表现

## 📈 测试报告示例

### 快速测试报告
```
🚀 AKSHARE接口快速测试
==================================================
⏰ 测试时间: 2025-09-26 22:45:00
==================================================

📊 测试进度:
------------------------------------------------------------
 1. 股票列表         ✅ 通过   数据形状: (5000, 2)       0.345s
 2. 股票基本信息     ✅ 通过   数据形状: (20, 2)         0.123s
 3. 实时行情         ✅ 通过   数据形状: (5000, 15)      0.567s
...

📈 测试结果汇总
==================================================
总测试数: 10
通过测试: 9
失败测试: 1
成功率: 90.0%
总耗时: 3.456 秒
平均响应时间: 0.346 秒
```

### 数据质量报告
```
📊 数据质量报告汇总
==================================================
平均完整性得分: 98.5%
一致性通过率: 8/10
新鲜度通过率: 9/10

📋 详细结果:
✅ 股票基本信息:
  完整性: PASS (100.0%)
  一致性: PASS
  新鲜度: PASS
⚠️ 基金数据:
  完整性: WARNING (85.2%)
  一致性: PASS
  新鲜度: PASS
```

## 💡 使用建议

### 日常监控
```bash
# 每天运行快速测试监控接口状态
python akshare_quick_test.py
```

### 版本升级后测试
```bash
# 升级AKSHARE后运行全面测试
python akshare_test_script.py
```

### 数据质量定期检查
```bash
# 每周运行数据质量测试
python akshare_data_quality_test.py
```

## 🛠️ 故障排除

### 常见问题

1. **接口返回空数据**
   - 检查网络连接
   - 验证股票代码格式
   - 检查数据源是否可用

2. **数据缺失严重**
   - 尝试不同的数据源
   - 检查参数格式是否正确
   - 确认接口是否已更新

3. **性能问题**
   - 减少批量请求数量
   - 增加请求间隔时间
   - 检查网络带宽

### 调试技巧
```python
# 在代码中添加调试信息
import akshare as ak
try:
    data = ak.stock_zh_a_hist(symbol="000001", period="daily")
    print(f"数据形状: {data.shape}")
    print(f"列名: {data.columns.tolist()}")
except Exception as e:
    print(f"错误信息: {e}")
```

## 📞 技术支持

如果遇到问题，可以：
1. 查看AKSHARE官方文档
2. 检查网络连接状态
3. 验证Python环境和依赖版本
4. 查看生成的详细错误报告

## 🎯 最佳实践

1. **定期测试**: 建议每周运行一次全面测试
2. **监控关键接口**: 对重要接口进行日常监控
3. **版本控制**: 在升级AKSHARE版本前后进行测试
4. **数据备份**: 重要数据定期备份和验证
5. **错误日志**: 记录测试结果便于问题追踪

---
*最后更新: 2025-09-26*
*测试脚本版本: 1.0*