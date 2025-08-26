
--- Table: pbp_stats_passing
--- DDL for pbp_stats_passing
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `pbp_stats_passing`(
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
  `pass_length` string, 
  `pass_location` string, 
  `air_yards` string, 
  `yards_after_catch` bigint, 
  `throw_yards` string, 
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
  's3://alt-nfl-database/pbp_stats_passing/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='212', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='4611', 
  'partition_filtering.enabled'='true', 
  'recordCount'='311580', 
  'sizeKey'='75487066', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')

--- Sample queries for pbp_stats_passing
--- --------------------------------------------------------
-- What was the percentage of passes over 15 yards by QBs in 2024 who took at least 50 snaps?
with final as (select 
full_name,
case when cast(throw_yards as double) >15 then 1 else 0 end as over_15,
1 as total_passes
from nfl_stats_database.pbp_stats_passing
where 1=1
and throw_yards <> 'NA'
and play_result in ('COMPLETE','TOUCHDOWN')
and nfl_season = '2024'
and full_name in (
select 
full_name
from pbp_stats_passing
where 1=1
and nfl_season = '2024'
group by 1
having count(*)>50
)),
rt as (select full_name, sum(over_15) as over15,sum(total_passes) as passes from final group by 1)
select *, round(cast(over15 as double)/cast(passes as double),3)*100 as rate from rt
