#coding: utf-8
import os, sys
import json
import re
import copy
import mysql_diff

m_file = sys.argv[1]
s_file = sys.argv[2]

with open(m_file, 'r') as f:
    m_tables = mysql_diff.parse_sql(f.readlines())

with open(s_file, 'r') as f:
    s_tables = mysql_diff.parse_sql(f.readlines())

for m_table_key in m_tables:
    m_table = m_tables[m_table_key]
    m_field_sort = copy.copy(m_table['field_sort'])
    m_fields = m_table['fields']

    if not s_tables.has_key(m_table_key):
        print m_table['sql']
        continue

    s_table = s_tables[m_table_key]
    s_field_sort = copy.copy(s_table['field_sort'])
    s_fields = s_table['fields']

    sql = ''
    
    # DROP COLUMN
    for s_field_key in s_field_sort:
        if not m_fields.has_key(s_field_key):
            sql += "DROP COLUMN `" + s_fields[s_field_key].name + "`,\n"
            s_field_sort.remove(s_field_key)

    for i in range(0, len(m_field_sort)):
        m_field_key = m_field_sort[i]
        m_field = m_fields[m_field_key]
        m_field_sql = str(m_field)

        # ADD COLUMN
        if not s_fields.has_key(m_field_key):
            sql += "ADD COLUMN " + m_field_sql

            if i > 0:
                sql += " AFTER `" + m_fields[m_field_sort[i - 1]].name + "`"
            else:
                sql += " FIRST"
                
            sql += ",\n"

            s_field_sort.insert(i, m_field_key)

            continue
    
        # CHANGE COLUMN
        s_field = s_fields[m_field_key]
        s_field_sql = str(s_field)

        if m_field_sql == s_field_sql and (i == 0 or m_field_sort[i - 1] == s_field_sort[i - 1]):
            continue

        sql += "CHANGE `" + s_field.name + "` " + m_field_sql;
        
        if m_field_sort[i - 1] != s_field_sort[i - 1]:
            if i > 0:
                sql += " AFTER `" + m_fields[m_field_sort[i - 1]].name + "`"
            else:
                sql += " FIRST"
        
        sql += ",\n"

    m_keys = m_table['keys']
    s_keys = s_table['keys']
    
    # DROP INDEX
    for s_key_key in s_keys:
       s_key = s_keys[s_key_key]
       if not m_keys.has_key(s_key_key):
            if s_key.type != 'PRIMARY':
                sql += "DROP INDEX `" + s_key.name + "`,\n"
            else:
                sql += "DROP PRIMARY KEY,\n"

    for m_key_key in m_keys:
    
        m_key = m_keys[m_key_key]
        m_key_sql = str(m_key)

        # ADD INDEX
        if not s_keys.has_key(m_key_key):
            sql += "ADD " + m_key_sql + ",\n"
            continue
            
        # CHANGE INDEX
        s_key = s_keys[m_key_key]
        s_key_sql = str(s_key)
        
        if m_key_sql == s_key_sql:
            continue
        
        sql += "DROP INDEX `" + s_key.name + "`,\n"
        sql += "ADD " + m_key_sql + ",\n"

    if sql != '':
        print "ALTER TABLE `"+ s_table['name'] +"`\n" + sql[0:-2] + ";\n"