
--- Table: team_stats
--- DDL for team_stats
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `team_stats`(
  `espn_id` bigint, 
  `unique_id` string, 
  `team_abbreviation` string, 
  `team_id` bigint, 
  `label` string, 
  `name` string, 
  `value` double, 
  `display` string)
PARTITIONED BY ( 
  `nfl_season` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/team_stats/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='64', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='5270', 
  'partition_filtering.enabled'='true', 
  'recordCount'='282987', 
  'sizeKey'='19179932', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')

--- Possible values for lable and name in team_stats
--- --------------------------------------------------------
select distinct label,name 
from nfl_stats_database.team_stats

"label","name"
"1st Downs","firstDowns"
"Passing 1st downs","firstDownsPassing"
"Rushing 1st downs","firstDownsRushing"
"1st downs from penalties","firstDownsPenalty"
"3rd down efficiency","thirdDownEff"
"4th down efficiency","fourthDownEff"
"Total Plays","totalOffensivePlays"
"Total Yards","totalYards"
"Yards per Play","yardsPerPlay"
"Total Drives","totalDrives"
"Passing","netPassingYards"
"Comp/Att","completionAttempts"
"Yards per pass","yardsPerPass"
"Interceptions thrown","interceptions"
"Sacks-Yards Lost","sacksYardsLost"
"Rushing","rushingYards"
"Rushing Attempts","rushingAttempts"
"Yards per rush","yardsPerRushAttempt"
"Red Zone (Made-Att)","redZoneAttempts"
"Penalties","totalPenaltiesYards"
"Turnovers","turnovers"
"Fumbles lost","fumblesLost"
"Defensive / Special Teams TDs","defensiveTouchdowns"
"Possession","possessionTime"


--- Sample queries for team_stats
--- --------------------------------------------------------

-- How many first downs did GreenBay have by season
-- How many first downs did GreenBay have by season
select 
team_abbreviation,
label,
name,
nfl_season,
sum(value) as value
from nfl_stats_database.team_stats
where team_abbreviation = 'GB'
and name = 'firstDowns'
group by 1,2,3,4
order by nfl_season
