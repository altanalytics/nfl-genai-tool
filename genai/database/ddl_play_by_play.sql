
--- Table: play_by_play
--- DDL for play_by_play
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `play_by_play`(
  `espn_id` string, 
  `unique_id` string, 
  `drive_id` string, 
  `play_id` string, 
  `sequence` string, 
  `yardage` string, 
  `quarter` string, 
  `time_remaining` string, 
  `home_score` string, 
  `away_score` bigint, 
  `down` bigint, 
  `distance` bigint, 
  `yardline` bigint, 
  `yards_to_endzone` bigint, 
  `possession` string, 
  `scoring_play` boolean, 
  `play_text` string, 
  `col17` string, 
  `col18` string)
PARTITIONED BY ( 
  `nfl_season` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/play_by_play/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ceb5e1c8-414a-4c75-b1df-82a6caac7927', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='146', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'commentCharacter'='#', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='5597', 
  'partition_filtering.enabled'='true', 
  'recordCount'='1025330', 
  'sizeKey'='173244477', 
  'skip.header.line.count'='1', 
  'typeOfData'='file')