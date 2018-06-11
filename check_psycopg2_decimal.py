#!/usr/bin/env python

import psycopg2

conn=psycopg2.connect(
  database="postgres",
  user="postgres",
)

cur = conn.cursor()

def cur_execute(sql_query):
  try:
   cur.execute(sql_query)
  except psycopg2.Error as e:
   print("Error {0}".format(e))
  return cur.fetchone()

output_cur = cur_execute("select sum(pg_total_relation_size(schemaname||'.'||quote_ident(tablename))) from pg_tables")[0]
print(output_cur)