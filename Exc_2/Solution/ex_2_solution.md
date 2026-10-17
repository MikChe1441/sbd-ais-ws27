 **2.1:** your `CREATE TABLE` statement and the SQL for A–D with their
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_name TEXT,
  product_category TEXT,
  quantity INTEGER,
  price_per_unit NUMERIC(10,2),
  order_date DATE,
  country TEXT
);


**A.** Which order has the highest `price_per_unit`?
SELECT * FROM orders ORDER BY price_per_unit DESC LIMIT 1;
   id   | customer_name | product_category | quantity | price_per_unit | order_date | country 
--------+---------------+------------------+----------+----------------+------------+---------
 841292 | Emma Brown    | Automotive       |        3 |        2000.00 | 2024-10-11 | Italy
(1 row)

**B.** What are the top 3 product categories with the highest total quantity
sold across all orders?
SELECT
    product_category, SUM(quantity) AS total_qty
FROM 
    orders
GROUP BY
    product_category
ORDER BY
    total_qty DESC LIMIT 3;

 product_category | total_qty 
------------------+-----------
 Health & Beauty  |    300842
 Electronics      |    300804
 Toys             |    300598
(3 rows)

**C.** What is the total revenue per product category?
(Revenue = `price_per_unit × quantity`)

SELECT 
    product_category, 
    SUM(price_per_unit * quantity) AS revenue
FROM 
    orders 
GROUP BY
    product_category
ORDER BY
    revenue DESC;

 product_category |   revenue    
------------------+--------------
 Automotive       | 306589798.86
 Electronics      | 241525009.45
 Home & Garden    |  78023780.09
 Sports           |  61848990.83
 Health & Beauty  |  46599817.89
 Office Supplies  |  38276061.64
 Fashion          |  31566368.22
 Toys             |  23271039.02
 Grocery          |  15268355.66
 Books            |  12731976.04
(10 rows)

**D.** Who are the top 5 customers by total spending?

SELECT customer_name,
       SUM(price_per_unit * quantity) AS total_spent,
       COUNT(*) AS n_orders
FROM orders GROUP BY customer_name
ORDER BY total_spent DESC LIMIT 5;

 customer_name  | total_spent | n_orders 
----------------+-------------+----------
 Carol Taylor   |   991179.18 |     1028
 Nina Lopez     |   975444.95 |      980
 Daniel Jackson |   959344.48 |     1033
 Carol Lewis    |   947708.57 |      943
 Daniel Young   |   946030.14 |      973

 **E.** Look at the spending totals in D — and at how many orders each of those
customers has. What do you notice? Open `ecommerce/dataset_generator.py` and
explain *why* the data looks like this.

total random nothing special 


### Activity 2.2 — Why Is This Self-Join So Slow?
postgres=# SELECT COUNT(*) FROM people_50k  p1 JOIN people_50k  p2 ON p1.country = p2.country;
  count   
----------
 27501822
(1 row)

Time: 1372.777 ms (00:01.373)
### X 3.35
postgres=# SELECT COUNT(*) FROM people_100k p1 JOIN people_100k p2 ON p1.country = p2.country;
   count   
-----------
 109946508
(1 row)

Time: 4601.171 ms (00:04.601)
### X 4.075
postgres=# SELECT COUNT(*) FROM people_200k p1 JOIN people_200k p2 ON p1.country = p2.country;
   count   
-----------
 439395606
(1 row)

Time: 18751.643 ms (00:18.752)

**Step 2 — Does an index help?** kinda ?
postgres=# SELECT COUNT(*) FROM people_100k p1 JOIN people_100k p2 ON p1.country = p2.country;
   count   
-----------
 109946508
(1 row)
Time: 3681.590 ms (00:03.682)
The index on country did not speed up the query. According to EXPLAIN ANALYZE, table reading takes a few milliseconds, while the major part of the time (about 4.3 s out of 7.3 s) is spent on the Hash Join,


**Step 3 — Rewrite it.**
SELECT SUM(cnt * cnt) AS pairs
FROM (SELECT country, COUNT(*) AS cnt FROM people_100k GROUP BY country) t;
   pairs   
-----------
 109946508
(1 row)
Time: 7.453 ms

**Step 4 — Discussion (submit in writing).** 

Optimizing the algorithm from O(n^2) to O(n) provides exponential gains that hardware cannot replace, while handling massive data outputs requires clarifying business goals through filtering or aggregation. Furthermore, heavy analytical workloads should be moved from OLTP databases to specialized data warehouses to prevent resource starvation.
