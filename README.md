# mysql-sql-diff
通过比较两份mysqldump导出的表结构文件，生成表结构更新语句  

*这是一个未经测试的版本，在生成更新语句后还请详细检验一下生成的语句是否有错误，有问题联系：sss60@qq.com*

# 使用方法

    python diff.py from.sql to.sql

**注意：** 两份sql文件必须是由mysqldump命令导出的，mysqldump命令只导出表结构的方法是：

	mysqldump -uroot -proot --lock-tables=FALSE -d <database_name>