# Vendor Performance & Inventory Optimization Analysis 
### 📊 Project Overview
#### This project delivers a comprehensive analysis of vendor performance and inventory management for a retail/wholesale business operating in the beverage industry. Through rigorous statistical analysis of 10,692 unique product records, we identify critical opportunities for margin expansion, operational efficiency improvements, and strategic vendor management that can unlock $2.71M in trapped inventory capital while mitigating supply chain risks.Key Dataset Metrics: 10,692 records | 200+ vendors | Price range: $0.74 - $7,499.99 | $2.71M unsold inventory
### 🎯 Business Objectives
This analysis addresses five critical business challenges:
1. Brand Optimization - Identify underperforming brands for promotional or pricing adjustments
2. Vendor Analysis - Determine top vendors contributing to sales and gross profit
3. Bulk Purchasing - Analyze bulk purchasing impact on unit costs and profitability
4. Inventory Efficiency - Assess inventory turnover to reduce holding costs
5. Margin Investigation - Investigate profitability variance across vendor segments
Expected Impact: 15-25% sales velocity increase | $2.71M working capital release | 2-3 point margin improvement

### 🔍 Key Findings
#### 1. The Pareto Principle: 80/20 Rule Confirmed
- 80% of total revenue from approximately 20% of products
- Top 10 vendors contribute 65.69% of total purchases
- Extreme right-skewed distributions indicate market concentration
<img width="800" height="900" alt="4x4" src="https://github.com/user-attachments/assets/b423e557-f268-4d68-a567-bee3099c73f9" />

<img width="800" height="900" alt="4x4_1" src="https://github.com/user-attachments/assets/ac9c822b-420f-499d-b8e8-e67cb792a4fe" />


#### 2. Vendor Concentration Risk: Dependency Alert
Critical Finding: Significant supply chain vulnerability due to vendor over-reliance.
Concentration Breakdown:
- DIAGEO NORTH AMERICA INC: 16.3% of purchases ($67.99M sales)
- MARTIGNETTI COMPANIES: 8.3% of purchases ($39.33M sales)
- Top 3 vendors control ~30% of procurement
- 200+ small vendors create administrative burden

<img width="800" height="900" alt="Pareto_chart_Vendor_contribution" src="https://github.com/user-attachments/assets/8c3efb91-bbfd-456b-a7c4-643b564eed94" />

<img width="800" height="900" alt="Top_10_Vendor" src="https://github.com/user-attachments/assets/7e4be26d-51a6-4278-986d-22303c505e5b" />

<img width="800" height="900" alt="cP_Vendor_Descrip" src="https://github.com/user-attachments/assets/80bf9fc0-329e-4c97-b134-915f1a057e4a" />

<img width="800" height="900" alt="Top_10_vendors_ _Brands" src="https://github.com/user-attachments/assets/ec22a99a-eb7f-4489-9de1-3b4785623d72" />


#### 3. Bulk Purchasing: The Law of Diminishing Returns
Major Discovery: Bulk discounts plateau beyond medium-sized orders.
Key Insights:

✅ Small → Medium orders: 72% cost reduction (maximum efficiency gain)
⚠️ Medium → Large orders: Minimal additional savings (<5%)
🔴 Beyond 10,000 units: Curve flattens—storage costs exceed marginal savings
Strategic Implication: Cap bulk orders at the "knee" of the efficiency curve (~1,000-5,000 units).

<img width="800" height="900" alt="Impact_Bulk_purchasing" src="https://github.com/user-attachments/assets/6f2e6bf0-6c56-4bd0-b7e6-56b720f09ad1" />


#### 4. The Counter-Intuitive Margin Paradox
Breakthrough Finding: Low-performing vendors deliver significantly higher profit margins than industry giants.

Vendor Segment    | Avg Profit Margin | 95% Confidence Interval | Sales Volume
------------------|-------------------|-------------------------|-------------
Top Vendors       | 31.18%            | 30.74% - 31.61%        | High
Low Vendors       | 41.57%            | 40.50% - 42.64%        | Low
Difference        | +10.39%           | Non-overlapping CIs    | Significant

Hypothesis Test Result: ✅ Null hypothesis REJECTED (p < 0.05) — the margin difference is statistically significant.
Visual Representation:

Profit Margin Comparison (95% Confidence Intervals)

Top Vendors:    [████████████████] 30.74% ──── 31.18% ──── 31.61%
                
Low Vendors:                         [████████████████████] 40.50% ──── 41.57% ──── 42.64%

                20%      25%      30%      35%      40%      45%      50%
                
Note: Non-overlapping intervals = Statistically significant difference
                
<img width="800" height="900" alt="confidence_interval_comparison" src="https://github.com/user-attachments/assets/08aa8691-c6b2-4269-980b-29dd85a17e9f" />


Critical Business Implication:

❌ Do NOT cut low-volume vendors → Would eliminate 10.39% margin advantage

✅ Maintain dual strategy → Top vendors for cash flow + Low vendors for profitability

#### 5. Slow-Moving Inventory: $2.71M Opportunity
Problem Identified: Significant capital trapped in underperforming SKUs.
Inventory Issues:
- $2.71M in unsold inventory capital
- 198 brands with high margins (>65%) but low sales (<$1,000)
- Sales-to-Purchase ratio below 0.8 for multiple product lines
  
<img width="800" height="900" alt="Brands_for_promotional_or_pricing_adjustments" src="https://github.com/user-attachments/assets/04127718-2611-4404-a5a0-b72b16482719" />


#### 6. Correlation Insights: What Drives Performance?
<img width="800" height="900" alt="Corr_heatmap" src="https://github.com/user-attachments/assets/1e88ffb9-34bd-4fb0-b823-a363de5e9333" />

- Purchase Quantity ↔ Sales Quantity: 0.99 (excellent inventory turnover)
- Profit Margin ↔ Sales Price: -0.179 (competitive pressure reduces margins)
- Purchase Price ↔ Sales Dollars: -0.012 (pricing has minimal impact on revenue)

<img width="800" height="900" alt="4x4_2" src="https://github.com/user-attachments/assets/ae51dfb8-371b-4651-b1c6-4c8423bad5e3" />

#### 💡 Strategic Recommendations1. 
1. Dynamic Pricing Strategy
🎯Action Plan:
- Launch 10-15% promotional campaigns for 198 identified high-margin, low-sales brands
- Use existing 65%+ margins as buffer to fund aggressive marketing
- Implement dynamic pricing algorithms based on inventory age and demand patterns
Expected Outcomes: Convert $2.71M trapped inventory → working capital | 15-25% sales velocity increase
Timeline: 90-day pilot program with bi-weekly reviews

2. Vendor Diversification Program
🔄Objective: Reduce concentration risk from 65.69% to 55% within 18 months

Strategy Tiers:
- Tier 1 (Giants): Maintain but negotiate harder (leverage volume)
- Tier 2 (Mid-Sized): Cultivate 5-7 strategic partnerships
- Tier 3 (Niche): Preserve for margin enhancement (don't cut!)
- Tier 4 (Emerging): Test 3-5 new suppliers annually
Risk Mitigation: Establish dual-sourcing for top 20 products | Create contingency contracts | Quarterly vendor scorecards

3. Optimized Bulk Purchasing Guidelines📦
   
Order Size    | Quantity Range      | Action
--------------|---------------------|------------------------------------------
Small         | 1-100 units         | Avoid unless specialty/test products
Optimal       | 100-5,000 units     | TARGET ZONE - maximum efficiency
Large         | 5,000-15,000 units  | Only if turnover supports
Excessive     | >15,000 units       | REQUIRES CFO APPROVAL

Decision Logic:
IF (unit_cost_savings < 5%) AND (holding_cost > savings):
    → Do NOT place bulk order
ELSE IF (turnover_rate > 4x annually):
    → Approve bulk purchase
ELSE:
    → Order optimal quantity only
    
4. Inventory Optimisation Protocol📊
  
Quarterly Review Process:

Phase 1: Identification (Week 1)
- Flag products with sales-to-purchase ratio < 0.8
- Identify items with inventory age > 90 days
  
Phase 2: Action (Weeks 2-4)
- Tier 1 (Ratio 0.6-0.8): 15% markdown + email campaign
- Tier 2 (Ratio 0.3-0.6): 20% markdown + bundle promotions
- Tier 3 (Ratio <0.3): 30% clearance + liquidation consideration

Phase 3: Prevention (Ongoing)
- Minimum turnover thresholds for new SKUs (3x annually)
- Automatic reorder points based on historical velocity
- SKU sunset policy for chronic underperformers
  
5. Strategic Vendor Segmentation Framework 🎯
   
Dual-Track Management Approach:

Track A: High-Volume Vendors (Top 10)
- Focus: Cost efficiency and operational excellence
- Tactics: Annual contract negotiations, QBRs, cost-reduction initiatives
- KPIs: Cost per unit, on-time delivery %, fill rate

Track B: High-Margin Vendors (Niche Players)
- Focus: Preserve pricing power and expand distribution
- Tactics: Premium positioning, exclusive agreements, marketing support
- KPIs: Margin %, customer satisfaction, brand loyalty

<div align="center">
📊 Data-Driven | 💡 Actionable | 🚀 Results-Oriented
</div>
