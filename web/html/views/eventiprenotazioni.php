<?php
session_start();
if (!isset($_SESSION['username'])) {
    $_SESSION['next'] = $_SERVER['REQUEST_URI'];
	header('Location: /login?r');
	exit;
}
?>

<?php
    if (isset($_GET['id'])) {
        $id = $_GET['id'];
        require_once __ROOT__ . '/functions/db_conn.php';
        $stmt = $conn->prepare("SELECT * FROM Evento WHERE id = ?");
        $stmt->bind_param("i", $id);
        $stmt->execute();
        $result = $stmt->get_result();
        if ($result->num_rows > 0) {
            $row = $result->fetch_assoc();
            $nome = htmlspecialchars($row['nome']);
            $inizio = htmlspecialchars($row['time']);
        } else {
            echo "Evento non trovato.";
            exit;
        }
    } else {
        echo "ID evento non specificato.";
        exit;
    }
?>

<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestione prenotazioni</title>
    <script>
        document.addEventListener("DOMContentLoaded", function () {
            Array.from(document.getElementsByClassName('readOnlyCheck')).forEach((i) => {
                i.addEventListener('click', function(e) {
                    e.preventDefault(); // stops the checkbox from toggling
                });
            });
        });
    </script>
</head>
<body>
    <button onclick="document.location.href='/prenotazione?e=<?= $id ?>'">Aggiungi prenotazione ➕</button>
    <table border="1">
        <thead>
            <tr>
                <th>Nome</th>
                <th>Persone</th>
                <th>capotavola?</th>
                <th>Azioni</th>
            </tr>
        </thead>
        <tbody>
            <?php
            require_once __ROOT__ . '/functions/db_conn.php';
            $stmt = $conn->prepare("SELECT * FROM Prenotazione WHERE idevento = ?");
            $stmt->bind_param("i", $id);
            $stmt->execute();
            $result = $stmt->get_result();
            while ($row = $result->fetch_assoc()) {
                echo "<tr>";
                echo "<td>" . htmlspecialchars($row['nominativo']) . "</td>";
                echo "<td>" . htmlspecialchars($row['persone']) . "</td>";
                echo "<td><input type='checkbox' " . ($row['capotavola'] ? 'checked' : '') . " class='readOnlyCheck'></td>";
                echo "<td>
                    <button onclick=\"document.location.href='/eventi/prenotazioni/cancella?id=" . htmlspecialchars($row['id']) . "'\">Elimina</button>
                    
                </td>";
                echo "</tr>";
            }
            ?>
        </tbody>

    </table>
</body>
</html>