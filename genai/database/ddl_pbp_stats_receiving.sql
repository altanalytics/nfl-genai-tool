
--- Table: pbp_stats_receiving
--- DDL for pbp_stats_receiving
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `pbp_stats_receiving`(
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
  's3://alt-nfl-database/pbp_stats_receiving/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='222', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='4611', 
  'partition_filtering.enabled'='true', 
  'recordCount'='147582', 
  'sizeKey'='36756428', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')

--- Example queries for pbp_stats_receiving
--- --------------------------------------------------------
--- Can you give me terry mclaurin's receiving stats by squarterback?
select 
quarterback
,sum(case when play_result = 'TOUCHDOWN' then 1 else 0 end) as touchdowns
,count(*) as receptions
,sum(cast(yards_after_catch as double)) as yards_after_catch
,sum(cast(air_yards as double)) as air_yards

from nfl_stats_database.pbp_stats_receiving
where 1=1
and lower(full_name) = 'terry mclaurin'
group by 1