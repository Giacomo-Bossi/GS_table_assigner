<?php
session_start();

$error = 0; 
if($_SERVER["REQUEST_METHOD"] == "POST"){
    require_once __ROOT__ . '/functions/db_conn.php';
    $username = $_POST['username'];
    $password = $_POST['password'];
    $stmt = $conn->prepare("SELECT * FROM User WHERE id = ?");
    $stmt->bind_param("s", $username);
    $stmt->execute();
    $result = $stmt->get_result();
    if($result->num_rows == 0){
        $error = 1;
        // This is a security measure to prevent timing attacks
        password_verify("FAKEPASSWD", '$argon2id$v=19$m=65536,t=4,p=1$PjE2w6VJJa8pdB9H1VbgIA$Ost1BwsVA9GcAm0Kijcp7n4ceDSO6LxOL/2aXqK1sBg');
    }else{
        $row = $result->fetch_assoc();
        if(password_verify($password, $row['password'])){

            if(isset($_GET['r']) && isset($_SESSION['next'])){
                $next = $_SESSION['next'];
                if($next == "/login"){
                    $next = "/";
                }
                unset($_SESSION['next']);
                header("Location: $next");
            }else{
                header("Location: /");
            }

            session_unset();  // Removes all session variables
            session_destroy(); // Destroys the session
            session_regenerate_id(true);  // true ensures the old session is replaced with the new one
            session_start(); // 
            $_SESSION['username'] = $row['id'];
            
            exit();
        } else {
           $error = 1;
        }
    }
}

?>
<form  method="post">
    <label for="username">Username:</label><br>
    <input type="text" id="username" name="username"><br><br>
    <label for="password">Password:</label><br>
    <input type="password" id="password" name="password"><br><br>
    <?php if(isset($error) && $error !== 0): ?>
        <p style="color:red;">Invalid username or password</p>
    <?php endif; ?>
    <input type="submit" value="Login">
</form>