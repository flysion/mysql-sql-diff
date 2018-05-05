#coding: utf-8
import re

class Field:

    name = None
    type = None
    length = None
    unsigned = None
    character_set = None
    collate = None
    not_null = None
    auto_increment = None
    default = None
    comment = None
        
    def __str__(self):
        sql = "`%s` %s" % (self.name, self.type)
    
        if self.length != None:
            sql += "(" + self.length + ")"
        
        if self.unsigned == True:
            sql += " UNSIGNED"

        if self.auto_increment == True:
            sql += " AUTO_INCREMENT"
            
        if self.character_set != None:
            sql += " CHARACTER SET " + self.character_set
        
        if self.collate != None:
            sql += " COLLATE " + self.collate
            
        if self.not_null == True:
            sql += " NOT NULL"
            
        if self.default != None:
            sql += " DEFAULT " + self.default
            
        if self.comment != None:
            sql += " COMMENT " + self.comment

        return sql

class Key:
    
    name = None
    field = None
    using = None
    type = None
        
    def __str__(self):
        if self.type == 'PRIMARY':
            return "PRIMARY KEY (%s)" % (self.field)
    
        sql = "";
        if self.type != None:
            sql += self.type + " "
            
        sql += "INDEX `" + self.name + "` (" +self.field+ ")"
        
        if self.using != None:
            sql += " USING " + self.using
            
        return sql

def parse_sql(lines):
    data = {}
    
    table = ''; fields = {}; field_sort = []; keys = {}; sql = ''; state = 0
    
    for line in lines:
        line = line.strip()
        
        if line == "":
            continue
        
        if state == 0:
            r = re.match('^CREATE\s+TABLE\s+`(\w+)`\s+\($', line, re.IGNORECASE)
            if r:
                table = r.group(1)
                sql += line + "\n"
                state = 1

                continue
                
            if line[0:2] == '/*':             # 注释
                continue
            
            if line[0:3] == '-- ':            # 注释
                continue
            
            if line[0:4].upper() == 'SET ':   # SET 
                continue
            
            if line[0:5].upper() == 'DROP ':  # DROP TABLE
                continue
            
            if line == '--':                  # 空注释
                continue

        elif state == 1:
            sql += line + "\n"
            
            r = re.match("^`(\w+)`\s+(\w+)(?:\((.*?)\))*(\s+UNSIGNED)*(?:\s+CHARACTER\s+SET\s+(\w+))*(?:\s+COLLATE\s+(\w+))*(\s+NOT\s+NULL)*(\s+AUTO_INCREMENT)*(?:\s+DEFAULT\s+(.*?))*(?:\s+COMMENT\s+('.*?'))*,*$", line, re.IGNORECASE)
            if r:
                comment = r.group(10)
                origin = None
                
                if comment != None:
                    r_opt = re.match('^\'<origin:(\w+)>(.*?)\'$', comment)
                    if r_opt:
                        origin = r_opt.group(1)
                        comment = r_opt.group(2)

                field = Field()
                field.name = r.group(1)
                field.type = r.group(2)
                field.length = r.group(3)
                field.unsigned = r.group(4) != None
                field.character_set = r.group(5)
                field.collate = r.group(6)
                field.not_null = r.group(7) != None
                field.auto_increment = r.group(8) != None
                field.default = r.group(9)
                field.comment = comment

                if origin != None:
                    field_key = origin
                else:
                    field_key = field.name
                    
                if fields.has_key(field_key):
                    raise Exception('"' + table + '.' + field_key + '" already exists')

                field_sort.append(field_key)
                fields[field_key] = field

                continue
                
            r = re.match('^(?:(FULLTEXT|UNIQUE)\s+)*KEY\s+`(\w+)`\s+\((.*?)\)(?:\s+USING\s+(\w+))*,*$', line, re.IGNORECASE)
            if r:
                key = Key()
                key.name = r.group(2)
                key.field = r.group(3)
                key.using = r.group(4)
                key.type = r.group(1)
                
                key_key = str(key.type) + key.field + str(key.using)
                
                keys[key_key] = key
                
                continue
                
            r = re.match('^PRIMARY\s+KEY\s+\((.*?)\),*$', line, re.IGNORECASE)
            if r:
                key = Key()
                key.field = r.group(1)
                key.type = 'PRIMARY'
                
                keys['PRIMARY' + key.field] = key

                continue

            r = re.match('^\).*?;$', line, re.IGNORECASE)
            if r:
                table_key = table.lower()
                
                data[table_key] = {
                    'name': table,
                    'field_sort': field_sort,
                    'fields': fields,
                    'keys': keys,
                    'sql': sql,
                }
                
                table = ''; fields = {}; field_sort = []; keys = {}; sql = ''; state = 0
                
                continue
                
            raise Exception('Unknown SQL syntax: "' + line + '"')
    
    return data