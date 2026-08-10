<?php
session_start();

if (isset($_POST['username']) && isset($_POST['password'])) {
    require_once './../models/Users.php';

    $password = password_hash($_POST['password'], PASSWORD_DEFAULT);

    $ok = Users::insertUser($_POST['username'], $password);
    if ($ok) {
        $_SESSION['success'] = "L'utilisateur " . $_POST['username'] . " a correctement été ajouté.";
    } else {
        $_SESSION['error'] = "Quelque chose s'est mal passé.";
    }

    header('Location: index.php');
    exit(0);
}

include_once './../fragments/header.php';
?>

<div class="container mt-5">
    <h1>password_hash</h1>
    <?php
    if (isset($_SESSION['success'])) {
        echo '<div class="alert alert-success">' . $_SESSION['success'] . '</div>';
    }
    if (isset($_SESSION['error'])) {
        echo '<div class="alert alert-danger">' . $_SESSION['error'] . '</div>';
    }

    require_once './../fragments/form.php';
    ?>    
</div>

<?php
$_SESSION = array();
include_once './../fragments/header.php';
