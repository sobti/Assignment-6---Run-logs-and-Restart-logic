<?php

$data_string = (file_get_contents("./data.php"));
$data = unserialize($data_string);

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <link rel="stylesheet" href="main.css">
    <title><?=$data['title'];?></title>
    <script src = "main.js"></script>
</head>
<body>
    <div class="resume">
        <h2><?=$data['title'];?></h2>
        <div class="content">
            <?=nl2br( $data['content']);?>
        </div>
    </div>
</body>
</html>