<?php
$HOST = '127.0.0.1';
$PORT = '3306';
$USER = 'root';
$PASS = 'root';
$DBNAME = 'anfanapi';

$db = new PDO("mysql:host={$HOST}; dbname={$DBNAME}; port={$PORT}; charset=utf8", $USER, $PASS);

function createTableSql($fields) {
    $data = [];
    foreach($fields as $f){
        $data[] = "`{$f}` int(11) DEFAULT NULL";
    }
    
    $sql = "CREATE TABLE `t` (" . PHP_EOL;
    $sql.= implode(",\n", $data) . PHP_EOL;
    $sql.= ") ENGINE=InnoDB DEFAULT CHARSET=utf8;";
    
    return $sql;
}

for($i = 0; $i < 10000; $i++) {
    $masterFields = array_map(function($v) { return "f{$v}"; }, range(0, rand(5, 9)));
    shuffle($masterFields); unset($masterFields[0], $masterFields[1], $masterFields[2]);
    shuffle($masterFields);
    $masterSql = createTableSql($masterFields);
    file_put_contents("master.sql", $masterSql);
    
    $slaveFields = array_map(function($v) { return "f{$v}"; }, range(0, rand(5, 9)));
    shuffle($slaveFields); unset($slaveFields[0], $slaveFields[1], $slaveFields[2]);
    shuffle($slaveFields);
    $slaveSql = createTableSql($slaveFields);
    file_put_contents("slave.sql", $slaveSql);
    
    $output = [];
    $return = 0;
    exec("python diff.py master.sql slave.sql", $output, $return);
    $alterSql = implode("\n", $output);
    
    $db->exec("drop table if exists `t`");
    $db->exec($slaveSql);
    $db->exec($alterSql);
    
    $rows = $db->query("desc `t`")->fetchAll(PDO::FETCH_ASSOC);
    
    $fields = [];
    foreach($rows as $row) {
        $fields[] = $row['Field'];
    }
    
    echo $i . "<----" . PHP_EOL;
    
    if(implode($masterFields) !== implode($fields)) {
        echo $masterSql . PHP_EOL;
        echo "----------------------------------" . PHP_EOL;
        echo $slaveSql . PHP_EOL;
        echo "----------------------------------" . PHP_EOL;
        echo $alterSql . PHP_EOL;
        echo "----------------------------------" . PHP_EOL;
        echo implode('-', $fields) . PHP_EOL;
        exit;
    }
}