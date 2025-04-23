
<?php
session_start();
session_unset();  // Removes all session variables
session_destroy(); // Destroys the session
session_regenerate_id(true);  // true ensures the old session is replaced with the new one
header("Location: /");
exit();


?>