
--- Table: player_stats
--- DDL for player_stats
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `player_stats`(
  `espn_id` bigint, 
  `unique_id` string, 
  `team_abbreviation` string, 
  `team_id` bigint, 
  `athlete_id` bigint, 
  `athlete_name` string, 
  `athlete_first` string, 
  `athlete_last` string, 
  `stat_type` string, 
  `stat_label` string, 
  `stat_description` string, 
  `stat_value` string, 
  `athlete_jersey` string)
PARTITIONED BY ( 
  `nfl_season` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/player_stats/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='107', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='5270', 
  'partition_filtering.enabled'='true', 
  'recordCount'='2343746', 
  'sizeKey'='274049832', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')


--- Possible values for stat_type, stat_label, stat_description in player_stats
--- --------------------------------------------------------

select distinct stat_type, stat_label, stat_description 
from nfl_stats_database.player_stats

--- Sample queries for player_stats
--- --------------------------------------------------------

-- How many touchdowns has Tom Brady had by nfl season
select 
athlete_name
,team_abbreviation
,stat_label
,nfl_season
,sum(cast(stat_value as double)) as touchdowns
from nfl_stats_database.player_stats
where 1=1
and lower(athlete_name) = 'tom brady'
and stat_label = 'TD'
group by 1,2,3,4
order by nfl_season


--- Can you give me the top 5 passers by yardage in 2015
with cte as (select 
athlete_name
,team_abbreviation
,stat_label
,nfl_season
,sum(cast(stat_value as double)) as passing_yards
from nfl_stats_database.player_stats
where 1=1
and stat_label = 'YDS'
and stat_type = 'passing'
and nfl_season = '2015'
group by 1,2,3,4
order by nfl_season)
select * from cte order by passing_yards desc
limit 5
