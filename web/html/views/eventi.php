<?php
session_start();
if (!isset($_SESSION['username'])) {
    $_SESSION['next'] = $_SERVER['REQUEST_URI'];
	header('Location: /login?r');
	exit;
}
?>

<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestione eventi</title>
</head>
<body>
    <button onclick="document.location.href='/eventi/crea'">Crea evento ➕</button>
    <table border="1">
        <thead>
            <tr>
                <th>#</th>
                <th>Nome</th>
                <th>Inizio</th>
                <th>Posti</th>
                <th>Iscritti</th>
                <th>Azioni</th>
            </tr>
        </thead>
        <tbody>
            <?php
            require_once __ROOT__ . '/functions/db_conn.php';
            $stmt = $conn->prepare("SELECT e.*,COALESCE(iscritti,0) as iscritti,COALESCE(posti,0) as posti FROM Evento AS e
            LEFT JOIN (
                SELECT idevento, COALESCE(SUM(persone),0) as iscritti FROM Prenotazione GROUP BY idevento
            ) AS iscritti ON e.id = iscritti.idevento
            LEFT JOIN (
                SELECT tp.id as idtopologia, COALESCE(SUM(t.sR + t.sD + t.sL + t.sU),0) as posti FROM Topologia tp
                    JOIN Assegnato a ON tp.id = a.idtopologia
                    JOIN Tavolo t ON a.idtavolo = t.id
                    GROUP BY tp.id
            ) AS posti ON e.idtopologia = posti.idtopologia 
                                        ");
            $stmt->execute();
            $result = $stmt->get_result();
            while ($row = $result->fetch_assoc()) {
                echo "<tr>";
                echo "<td>" . htmlspecialchars($row['id']) . "</td>";
                echo "<td>" . htmlspecialchars($row['nome']) . "</td>";
                echo "<td>" . htmlspecialchars($row['time']) . "</td>";
                echo "<td>" . htmlspecialchars($row['posti']) . "</td>";
                echo "<td ".($row['posti']<$row['iscritti']? "style=\"color:red\"": "" ).">" . htmlspecialchars($row['iscritti']) . "</td>";
                echo "<td><button onclick=\"document.location.href='/eventi/modifica?id=" . htmlspecialchars($row['id']) . "'\">Modifica</button></td>";
                echo "</tr>";
            }
            ?>
        </tbody>

    </table>
</body>
</html>