
--- Table: game_schedule
--- DDL for game_schedule
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `game_schedule`(
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
  `game_long_name` string, 
  `game_description` string, 
  `venue` string, 
  `location` string, 
  `game_winner` string, 
  `team_1_id` bigint, 
  `team_1_home_away` string, 
  `team_1_location` string, 
  `team_1_name` string, 
  `team_1_abbreviation` string, 
  `team_1_full_name` string, 
  `team_1_mascot` string, 
  `team_1_q1_score` bigint, 
  `team_1_q2_score` bigint, 
  `team_1_q3_score` bigint, 
  `team_1_q4_score` bigint, 
  `team_1_final_score` bigint, 
  `team_2_id` bigint, 
  `team_2_home_away` string, 
  `team_2_location` string, 
  `team_2_name` string, 
  `team_2_abbreviation` string, 
  `team_2_full_name` string, 
  `team_2_mascot` string, 
  `team_2_q1_score` bigint, 
  `team_2_q2_score` bigint, 
  `team_2_q3_score` bigint, 
  `team_2_q4_score` bigint, 
  `team_2_final_score` bigint)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/game_schedule/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='390', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='1', 
  'recordCount'='4981', 
  'sizeKey'='1942732', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')


  --- Sample queries for game_schedule
  --- --------------------------------------------------------
  -- Can you tell me how many times washington has been shut out at home in the first quarter by season?
with q1 as (
select season, 'home' as home_away, count(*) as q1_shutout from nfl_stats_database.game_schedule 
where team_1_abbreviation = 'WSH'
and team_1_q1_score = 0
group by 1
UNION
select season, 'away'as home_away, count(*) as q1_shutout  from nfl_stats_database.game_schedule 
where team_2_abbreviation = 'WSH'
and team_2_q1_score = 0
group by 1)
select * from q1 where home_away = 'home'