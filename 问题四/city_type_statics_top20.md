## 数据结构分析

### 表结构

这是一个城市-公司类型统计表，记录了**城市层面按公司类型聚合**的就业市场数据。

### 关键字段含义

**基础维度字段：**

- `city` - 城市代码（如A050、B170等）
- `city_tier` - 城市等级（一线、二线、三线、其他）
- `company_type` - 公司类型编码（type_xxx格式）

**核心统计指标：**

- `job_count` - 该城市在该公司类型的职位数量
- `total_jobs_in_city` - 该城市所有公司类型的职位总数
- `company_count_in_city` - 该城市的所有公司数量
- `national_job_count` - 全国范围内该类型的职位总数

**衍生指标：**

- `industry_ratio` = job_count / total_jobs_in_city（该类型在城市中的占比）

- `location_quotient` - 区位商，衡量产业专业化程度

- `avg_education_rank` - 平均学历要求分数

- `avg_experience_rank` - 平均经验要求分数

- `is_in_ten` - 是否进入前十（0/1标识）

  ### ✅ 数据维度细节说明：

  #### 1. **每个城市只展示前20的行业类型**

  - 表中每个 `city` 都包含最多 20 条具体的 `company_type` 记录（如 `type_lOdYUb`、`type_uTAWZv` 等）。
  - 这些类型是按照 `job_count`（该类型在该城市的职位数量）降序排列的前20名。
  - 剩余的所有职位被合并为一条记录，其 `company_type` 为“其他”。

  #### 2. **“其他”类别的特点**

  - `company_type = '其他'`
  - `job_count` = 该城市中不属于前20类型的职位总数。
  - `industry_ratio` = 0（因为不属于任何具体类型）。
  - `location_quotient`（区位商） = 0。
  - `is_in_ten` = 0（不属于前十类型）。
  - `national_job_count` 为全国该城市所有“其他”类型的职位总数。
  - `avg_education_rank` 和 `avg_experience_rank` 为“其他”类职位的平均值。

  #### 3. **“其他”类别在图表中需注意**

  - **区位商为0**：由于 `location_quotient` 为0，在绘制区位商热力图或条形图时，这些条目将不会显示或显示为0，可能影响颜色映射或排序。
  - **不参与类型对比**：在分析“各城市主导行业”时，“其他”类别应被排除或单独说明，因为它不代表具体行业。
  - **教育/经验排名**：虽然“其他”类也有平均教育/经验排名，但其行业属性不明确，解释时需谨慎。