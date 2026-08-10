<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "boligdata";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname) or die();
// Check connection
if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

?>