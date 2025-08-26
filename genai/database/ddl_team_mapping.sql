
--- Table: team_mapping
--- DDL for team_mapping
--- --------------------------------------------------------
CREATE EXTERNAL TABLE `team_mapping`(
  `col0` string, 
  `col1` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://alt-nfl-database/team_mapping/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='9cc783e9-8e49-49f7-be0c-6dafdf526f4b', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='NFL-DB-Crawler', 
  'areColumnsQuoted'='false', 
  'averageRecordSize'='22', 
  'classification'='csv', 
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'=',', 
  'objectCount'='1', 
  'recordCount'='40', 
  'sizeKey'='894', 
  'typeOfData'='file')

  --- Output of select * from team_mapping
  --- Allows you to match alias of teams to a single team_id
  --- --------------------------------------------------------
  "col0","col1"
"team_id","team_names"
"ARI","Arizona Cardinals ARI"
"ATL","Atlanta Falcons ATL"
"BAL","Baltimore Ravens BAL"
"BUF","Buffalo Bills BUF"
"CAR","Carolina Panthers CAR"
"CHI","Chicago Bears CHI"
"CIN","Cincinnati Bengals CIN"
"CLE","Cleveland Browns CLE"
"DAL","Dallas Cowboys DAL"
"DEN","Denver Broncos DEN"
"DET","Detroit Lions DET"
"GB","Green Bay Packers GB"
"HOU","Houston Texans HOU"
"IND","Indianapolis Colts IND"
"JAX","Jacksonville Jaguars JAX"
"KC","Kansas City Chiefs KC"
"LAC","San Diego Chargers Los Angeles LAC"
"LAR","St. Louis Rams Los Angeles LAR"
"LV","Oakland Raiders Las Vegas LV"
"MIA","Miami Dolphins MIA"
"MIN","Minnesota Vikings MIN"
"NE","New England Patriots NE"
"NO","New Orleans Saints NO"
"NYG","New York Giants NYG"
"NYJ","New York Jets NYJ"
"PHI","Philadelphia Eagles PHI"
"PIT","Pittsburgh Steelers PIT"
"SEA","Seattle Seahawks SEA"
"SF","San Francisco 49ers SF"
"TB","Tampa Bay Buccaneers TB"
"TEN","Tennessee Titans TEN"
"WSH","Washington Redskins Commanders WSH"
