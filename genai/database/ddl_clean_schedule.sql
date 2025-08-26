
--- Table: clean_schedule
--- DDL for clean_schedule
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `clean_schedule`(
  `season` bigint, 
  `season_type` bigint, 
  `season_name` string, 
  `season_week` bigint, 
  `game_week` bigint, 
  `espn_id` bigint, 
  `unique_id` string, 
  `date_time` string, 
  `date` string, 
  `game_short_name` string, 
  `matchup` string, 
  `home_team` string, 
  `home_score` bigint, 
  `away_team` string, 
  `away_score` bigint, 
  `winning_team` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/clean_schedule/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='3bb6977e-7aee-4635-bb73-854724c34a30', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='135', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='1', 
  'recordCount'='4135', 
  'sizeKey'='558283', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')

--- Example queries for pbp_stats_rushing
--- --------------------------------------------------------

--- can you give road wins for the Saints by season
select season, count(*) as road_wins
from nfl_stats_database.clean_schedule 
where away_team = 'NO'
and winning_team = 'NO'
group by 1
order by season

--- can you give me total regular season wins for Baltimore
select season, sum(case when winning_team = 'BAL' then 1 else 0 end) as total_wins
from nfl_stats_database.clean_schedule 
where matchup like '%BAL%'
and season_name = 'regular-season'
group by 1
order by season