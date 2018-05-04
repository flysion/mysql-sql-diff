#coding: utf-8
import os, sys
import json
import re

fromFile = sys.argv[1]
toFile = sys.argv[2]

def ParseKey(sql):
    r = re.match('PRIMARY\s+KEY\s*\((.*?)\),*$', sql)
    if r:
        return {
            'name': None,
            'field': r.group(1),
            'using': None,
            'type': 'PRIMARY'
        }
    
    r = re.match('(\w+\s+)*KEY\s+`(\w+)`\s*\((.*?)\)(\s+USING\s+(\w+))*,*$', sql)
    if not r:
        return None

    key = {
        'name': r.group(2),
        'field': r.group(3),
        'using': r.group(5),
        'type': r.group(1)
    }

    if key['type'] != None:
        key['type'] = key['type'].strip()

    return key

def ParseField(sql):
    r = re.match('`(\w+)`\s+(\w+)(\(.*?\))*', sql)
    if not r:
        return None

    field = {
        'name': r.group(1),
        'type': r.group(2),
        'length': r.group(3),
        'notNull': None,
        'autoIncrement': None,
        'unsigned': None,
        'default': None,
        'comment': None,
        'characterSet': None,
        'collate': None,
    }

    if field['length'] != None:
        field['length'] = field['length'].strip('()')
        
    if re.search('NOT\s+NULL', sql):
        field['notNull'] = True
        
    if re.search('AUTO_INCREMENT', sql):
        field['autoIncrement'] = True
        
    if re.search('unsigned', sql):
        field['unsigned'] = True
        
    r = re.search('(CHARACTER\s+SET\s+(\w+)\s+)*COLLATE\s+(\w+)', sql)
    if r:
        field['characterSet'] = r.group(2)
        field['collate'] = r.group(3)

    r = re.search('DEFAULT\s+(.*?)(\s+COMMENT\s+\'.*?\')*,*$', sql)
    if r:
        field['default'] = r.group(1)

    r = re.search('COMMENT\s+(\'.*?\'),*$', sql)
    if r:
        field['comment'] = r.group(1)

    return field

def ParseSql(sqlLines):
    data = {}
    
    table = ''
    fields = {}
    fieldSort = []
    keys = {}
    sql = ''
    state = 0
    
    for line in sqlLines:
        line = line.strip()
        
        if state == 0:
            if line[0:7] == 'CREATE ':          # 创建表
                r = re.match('CREATE\s+TABLE\s+`(\w+)`\s+\(', line)
                
                if not r:
                    continue
                    
                table = r.group(1)
                sql = sql + line + "\n"
                state = 1
            elif line[0:2] == '/*':             # 注释
                continue
            elif line[0:3] == '-- ':            # 注释
                continue
            elif line[0:4] == 'SET ':           # SET 
                continue
            elif line[0:5] == 'DROP ':          # DROP TABLE
                continue
            elif line == '--':                  # 空注释
                continue
            elif line == '':                    # 空行
                continue
        elif state == 1:
            sql = sql + line + "\n"
            
            if re.match('`(\w+)`\s+', line):
                field = ParseField(line)
                if field == None:
                    continue
                
                fieldKey = field['name'].lower()
                
                fields[fieldKey] = field
                
                if len(fieldSort) > 0:
                    fields[fieldKey]['prev'] = fieldSort[-1]
                else:
                    fields[fieldKey]['prev'] = None
                
                fieldSort.append(fieldKey)

            elif re.match('(UNIQUE\s+)*KEY\s+.*?,*$', line):
                key = ParseKey(line)
                if key == None:
                    continue
                    
                keys[key['name']] = key
            elif re.match('\).*?;', line):
                # TODO 解析表属性
                
                data[table.lower()] = {
                    'name': table,
                    'fieldSort': fieldSort,
                    'fields': fields,
                    'keys': keys,
                    'sql': sql,
                }
                
                table = ''
                fields = {}
                fieldSort = []
                keys = {}
                sql = ''
                state = 0
    
    return data

def GenerateFieldSql(opts):
    sql = "`%s` %s" % (opts['name'], opts['type'])
    
    if opts['length'] != None:
        sql = sql + "(" + opts['length'] + ")"
    
    if opts['unsigned'] == True:
        sql = sql + " UNSIGNED"

    if opts['autoIncrement'] == True:
        sql = sql + " AUTO_INCREMENT"
        
    if opts['characterSet'] != None:
        sql = sql + " CHARACTER SET " + opts['characterSet']
    
    if opts['collate'] != None:
        sql = sql + " COLLATE " + opts['collate']
        
    if opts['notNull'] == True:
        sql = sql + " NOT NULL"
        
    if opts['default'] != None:
        sql = sql + " DEFAULT " + opts['default']
        
    if opts['comment'] != None:
        sql = sql + " COMMENT " + opts['comment']

    return sql
    
def GenerateKeySql(opts):
    if opts['type'] == 'PRIMARY':
        return "PRIMARY KEY (%s)" % (opts['field'])
    
    sql = "";
    if opts['type'] != None:
        sql = sql + opts['type'] + " "
        
    sql = sql + "INDEX `" + opts['name'] + "` (" +opts['field']+ ")"
    
    if opts['using'] != None:
        sql = sql + " USING " + opts['using']
        
    return sql
    
fromTables = {}
toTables = {}

with open(fromFile, 'r') as f:
    fromTables = ParseSql(f.readlines())

with open(toFile, 'r') as f:
    toTables = ParseSql(f.readlines())

# 开始比对表

for tableKey in fromTables:
    fromTable = fromTables[tableKey]

    if not toTables.has_key(tableKey):
        print fromTable['sql']
        continue
        
    toTable = toTables[tableKey]
    
    sql = ""
     
    # 删除字段
    for fieldKey in toTable['fieldSort']:
        toField = toTable['fields'][fieldKey]
        if not fromTable['fields'].has_key(fieldKey):
            sql = sql + "DROP COLUMN `" + toField['name'] + "`,\n"
    
    # 修改、增加字段
    for fieldKey in fromTable['fieldSort']:
    
        fromField = fromTable['fields'][fieldKey]
        fromFieldSql = GenerateFieldSql(fromField)
        
        # 增加字段
        if not toTable['fields'].has_key(fieldKey):
            sql = sql + "ADD COLUMN " + fromFieldSql
            if fromField['prev'] != None:
                sql = sql + " AFTER `" +fromField['prev']+ "`"
            else:
                sql = sql + " FIRST"
                
            sql = sql + ",\n"
                
            continue
        
        # 修改字段
        toField = toTable['fields'][fieldKey]
        toFieldSql = GenerateFieldSql(toField)
        
        if fromFieldSql == toFieldSql and fromField['prev'] == toField['prev']:
            continue

        sql = sql + "CHANGE `" + toField['name'] + "` " + fromFieldSql;
        
        if fromField['prev'] != toField['prev']:
            if fromField['prev'] != None:
                sql = sql + " AFTER `" +fromField['prev']+ "`"
            else:
                sql = sql + " FIRST"
        
        sql = sql + ",\n"
            
    # 删除索引
    for keyName in toTable['keys']:
       if not fromTable['keys'].has_key(keyName):
            sql = sql + "DROP INDEX `" + keyName + "`,\n"
        
    # 修改、增加索引
    for keyName in fromTable['keys']:
    
        fromKey = fromTable['keys'][keyName]
        fromKeySql = GenerateKeySql(fromKey)
        
        # 增加索引
        if not toTable['keys'].has_key(keyName):
            sql = sql + "ADD " + fromKeySql + ",\n"
            continue
            
        # 修改索引
        toKeyOpts = toTable['keys'][keyName]
        toKeySql = GenerateKeySql(toKeyOpts)
        
        if fromKeySql == toKeySql:
            continue
        
        sql = sql + "DROP INDEX `" + keyName + "`,\n"
        sql = sql + "ADD " + fromKeySql + ",\n"
    
    if sql != '':
        print "ALTER TABLE `"+ toTable['name'] +"`\n" + sql[0:-2] + ";\n"