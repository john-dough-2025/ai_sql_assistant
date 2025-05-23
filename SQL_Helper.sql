SELECT CURRENT_DATABASE();
SELECT CURRENT_USER();
SELECT CURRENT_ROLE();

SELECT * FROM INFORMATION_SCHEMA."DATABASES" 
WHERE 1=1 
LIMIT 10

SELECT * FROM INFORMATION_SCHEMA."SCHEMATA" 
WHERE 1=1 
LIMIT 10

SELECT * FROM INFORMATION_SCHEMA."TABLES" 
WHERE 1=1 
LIMIT 10


SELECT 
TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,ORDINAL_POSITION,COLUMN_DEFAULT,IS_NULLABLE,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,CHARACTER_OCTET_LENGTH,NUMERIC_PRECISION,NUMERIC_PRECISION_RADIX,NUMERIC_SCALE,DATETIME_PRECISION
FROM INFORMATION_SCHEMA."COLUMNS" 
WHERE 1=1 
AND TABLE_SCHEMA = 'TPCH_SF10'
ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION


SELECT S_SUPPKEY, S_NAME, AVG(PS_SUPPLYCOST) AS AVG_SUPPLY_COST
FROM TPCH_SF10.PARTSUPP
JOIN TPCH_SF10.PART ON PARTSUPP.PS_PARTKEY = PART.P_PARTKEY
WHERE P_SIZE > 50  -- Assuming parts with size > 50 are high-demand
GROUP BY S_SUPPKEY, S_NAME
ORDER BY AVG_SUPPLY_COST ASC;