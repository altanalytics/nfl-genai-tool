
--- Table: pbp_stats_rushing
--- DDL for pbp_stats_rushing
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `pbp_stats_rushing`(
  `temp` string, 
  `game_id` string, 
  `posteam` string, 
  `player_id` string, 
  `down` string, 
  `ydstogo` bigint, 
  `play_type` string, 
  `yards_gained` bigint, 
  `shotgun` bigint, 
  `no_huddle` bigint, 
  `qb_dropback` bigint, 
  `qb_kneel` bigint, 
  `qb_spike` bigint, 
  `qb_scramble` bigint, 
  `run_location` string, 
  `run_gap` string, 
  `play_result` string, 
  `play_type_nfl` string, 
  `fumble` bigint, 
  `touchdown` bigint, 
  `interception` bigint, 
  `success` bigint, 
  `desc` string, 
  `full_name` string, 
  `first_name` string, 
  `last_name` string)
PARTITIONED BY ( 
  `nfl_season` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/pbp_stats_rushing/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='187', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='4611', 
  'partition_filtering.enabled'='true', 
  'recordCount'='96840', 
  'sizeKey'='20637145', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')

--- Example queries for pbp_stats_rushing
--- --------------------------------------------------------
-- How many rushes did Adrian Peterson have greater than 10 yards by season
select 
nfl_season,
count(*) as rushes_over_10
from nfl_stats_database.pbp_stats_rushing
where yards_gained > 10
and lower(full_name) = 'adrian peterson'
group by 1


-- What percentage of rushing attempts did Adrian Peterson have that were greater than 10 yards by season
select 
nfl_season,
sum(case when yards_gained > 10 then 1 else 0 end) as rushes_over_10,
count(*) as total_rushes,
round(sum(cast((case when yards_gained > 10 then 1 else 0 end) as double))/cast(count(*) as double),3)*100 as rush_10_rate
from nfl_stats_database.pbp_stats_rushing
where 1=1
and lower(full_name) = 'adrian peterson'
group by 1
