# Load Testing for District Marketplace

This directory contains load testing scripts to prove the **Performance** and **Scalability** quality attributes of the system.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Enable Mock AI Mode (Recommended for Testing)

```bash
export USE_MOCK_AI=True
```

This avoids API costs and allows for unlimited testing.

### 3. Start the Server

```bash
python manage.py runserver
```

### 4. Run Load Tests

```bash
# Run all test scenarios
./load_tests/run_tests.sh

# Or run specific test manually
locust -f load_tests/locustfile.py --host=http://localhost:8000
```

### 5. Analyze Results

```bash
python load_tests/analyze_results.py
```

This generates:
- Performance graphs
- Markdown report
- Metrics comparison

## Test Scenarios

### 1. Light Load (Warmup)
- **Users:** 10
- **Duration:** 30 seconds
- **Purpose:** System warmup and basic functionality test

### 2. Medium Load
- **Users:** 50 concurrent
- **Duration:** 60 seconds
- **Purpose:** Normal operating conditions

### 3. Heavy Load
- **Users:** 100 concurrent
- **Duration:** 90 seconds
- **Purpose:** Stress testing

### 4. Spike Test
- **Users:** 0 → 200 in 10s
- **Duration:** 40 seconds
- **Purpose:** Test rapid traffic spike handling

### 5. Seller-Heavy Workload
- **Users:** 100 sellers
- **Duration:** 60 seconds
- **Purpose:** Product creation load testing

### 6. Buyer-Heavy Workload
- **Users:** 100 buyers
- **Duration:** 60 seconds
- **Purpose:** Search and browse load testing

## User Classes

### MarketplaceUser (Mixed Workload)
Simulates realistic usage with:
- 50% search operations
- 30% product listing
- 20% browsing

### SellerUser
Only creates products (heavy write operations)

### BuyerUser
Only searches and browses (heavy read operations)

## Metrics Collected

- **Response Time:**
  - Average
  - Median
  - P95 (95th percentile)
  - P99 (99th percentile)

- **Throughput:**
  - Requests per second (RPS)
  - Total requests

- **Reliability:**
  - Failure rate
  - Error types

## Performance Targets

For **Performance Quality Attribute** proof:

| Metric | Target | Threshold |
|--------|--------|-----------|
| Avg Response Time | < 500 ms | Good: <500ms, Warning: 500-1000ms, Poor: >1000ms |
| P95 Response Time | < 1000 ms | Good: <1000ms, Warning: 1000-2000ms, Poor: >2000ms |
| Failure Rate | < 1% | Good: <1%, Warning: 1-5%, Poor: >5% |
| Throughput | > 50 RPS | Good: >50 RPS, Warning: 20-50 RPS, Poor: <20 RPS |

## Results Location

After running tests, results are in:
- `load_tests/results/*.html` - Interactive HTML reports
- `load_tests/results/*.csv` - Raw data
- `load_tests/results/*.png` - Performance graphs
- `load_tests/results/PERFORMANCE_REPORT.md` - Summary report

## Manual Testing

To run custom tests with web UI:

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 and configure:
- Number of users
- Spawn rate
- Host

## Tips

1. **Use Mock AI for testing:**
   ```bash
   export USE_MOCK_AI=True
   ```
   This gives consistent, fast responses without API calls.

2. **Monitor system resources:**
   ```bash
   # In another terminal
   watch -n 1 'ps aux | grep python'
   ```

3. **Check database connections:**
   ```bash
   # See active connections
   docker exec marketplace_db psql -U mkt_user -d mkt_db -c "SELECT count(*) FROM pg_stat_activity;"
   ```

4. **Scale workers for better performance:**
   ```python
   # In docker-compose.yml, increase Gunicorn workers
   command: gunicorn marketplace.wsgi:application --bind 0.0.0.0:8000 --workers 5
   ```

## Troubleshooting

**High error rates:**
- Check if server is running
- Check database connectivity
- Reduce concurrent users
- Enable USE_MOCK_AI to rule out external API issues

**Slow response times:**
- Enable database query optimization
- Add caching (Redis)
- Increase Gunicorn workers
- Use select_related() / prefetch_related() in queries

**Connection refused:**
- Ensure server is running on correct port
- Check firewall settings
- Verify host parameter matches server address

## For Project Submission

Include in your report:
1. Screenshots of HTML reports showing response time graphs
2. Performance comparison table across test scenarios
3. Analysis of results (meeting/not meeting targets)
4. Graphs from `analyze_results.py`
5. Discussion of bottlenecks found and optimizations made

Example conclusion:
> "Under heavy load (100 concurrent users), the system maintained an average response time of 250ms with 0.2% error rate, demonstrating the effectiveness of asynchronous processing, caching, and database optimization strategies."
