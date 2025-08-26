
--- Table: drive_report
--- DDL for drive_report
--- --------------------------------------------------------

CREATE EXTERNAL TABLE `drive_report`(
  `espn_id` bigint, 
  `unique_id` string, 
  `team_abbreviation` string, 
  `team_id` string, 
  `description` string, 
  `start_quarter` bigint, 
  `start_time` string, 
  `yards` bigint, 
  `scoring` boolean, 
  `offensive_plays` bigint, 
  `result` string, 
  `display_result` string, 
  `start_text` string, 
  `start_yard` bigint, 
  `end_text` string, 
  `end_yard` string, 
  `time_length` string)
PARTITIONED BY ( 
  `nfl_season` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/drive_report/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='131', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='5597', 
  'partition_filtering.enabled'='true', 
  'recordCount'='113251', 
  'sizeKey'='15932657', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')



--- Potential values for result in drive_report
--- NOTE: there can be multiple results for the same outcome 
--- (e.g. "INTERCEPTED PASS TD" and "INT TD" both mean interception returned for touchdown)
--- --------------------------------------------------------
select 
result,display_result,count(*) as result_type
from nfl_stats_database.drive_report 
group by 1,2
having count(*) > 10

"result","display_result","result_type"
"TIMEOUT","Timeout","26"
"PUNT RETURN TD","Punt Return Touchdown","19"
"SACK","Sack","28"
"RUSH","Rush","118"
"INT TD","Interception Touchdown","562"
"FUMBLE","Fumble","4844"
"MISSED FG","Missed FG","3097"
"FG","FIELD GOAL","41"
"BLOCKED FG TD","Blocked FG Touchdown","22"
"FG","Field Goal","17758"
"FUMBLE RECOVERY (OPPONENT)","Fumble Recovery (Opponent)","227"
"TD","Touchdown","25708"
"END OF GAME","End of Game","4698"
"INTERCEPTED PASS TD","Intercepted Pass Touchdown","421"
"PENALTY","Penalty","28"
"PASS INT","Pass Interception","70"
"FG GOOD","Field Goal Good","128"
"FG MISSED","Field Goal Missed","23"
"MISSED FG","MISSED FG","15"
"DOWNS","DOWNS","23"
"""BLOCKED FG"," DOWNS""","17"
"SF","Safety","359"
"PUNT","Punt","49820"
"PUNT TD","Punt Touchdown","121"
"INT","INTERCEPTION","21"
"""BLOCKED PUNT"," DOWNS""","41"
"PASS","Pass","110"
"PASS COMPLETION","Pass Completion","11"
"INTERCEPTED PASS","Intercepted Pass","3194"
"NA","NA","17"
"FUMBLE RETURN TD","Fumble Return Touchdown","472"
"END OF HALF","End of Half","4606"
"FUMBLE RECOVERY (OWN)","Fumble Recovery (Own)","30"
"FUMBLE TD","Fumble Touchdown","13"
"DOWNS","Downs","5507"
"BLOCKED FG","Blocked FG","124"
"FUMBLE","FUMBLE","24"
"END OF 1ST HALF","End of 1st Half","115"
"PUNT","PUNT","139"
"BLOCKED PUNT TD","Blocked Punt Touchdown","90"
"TD","TOUCHDOWN","76"
"INT","Interception","5181"
"BLOCKED PUNT","Blocked Punt","99"
"END OF HALF","END OF HALF","31"



--- Example queries for drive_report
--- --------------------------------------------------------
-- How many drives did each team have in the 2015 Cleveland Tennessee game
-- **NOTE** - the unique_id can come from game_schedule or get_schedule
select 
team_abbreviation,
count(*) as number_of_drives
from nfl_stats_database.drive_report 
where unique_id = '2015_2_02_CLE_TEN'
group by 1

-- How many drives did Washington have greater than 40 yards by nfl season
select
team_abbreviation
,nfl_season
,count(*) as drive_count
from nfl_stats_database.drive_report
where yards > 40
and team_abbreviation = 'WSH'
group by 1,2
order by nfl_season

-- How many offensive plays did Chicago have by nfl season during the regular season
select
dr.team_abbreviation
,dr.nfl_season
,sum(offensive_plays) as offensive_plays
from nfl_stats_database.drive_report dr
left join nfl_stats_database.game_schedule gs 
on gs.unique_id = dr.unique_id
where 1=1
and dr.team_abbreviation = 'CHI'
and gs.season_name = 'regular-season'
group by 1,2
order by nfl_season


-- How many missed field goals have there been by nfl post-season
select
dr.nfl_season
,count(*) as missed_fgs
from nfl_stats_database.drive_report dr
left join nfl_stats_database.game_schedule gs 
on gs.unique_id = dr.unique_id
where 1=1
and gs.season_name = 'post-season'
and result = 'MISSED FG'
group by 1
order by nfl_season
