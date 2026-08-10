<?php
	include 'plantilla.php';
	require 'conexion.php';
	
	$query = "SELECT r.id as id, r.descripccion as desr, e.descripccion as dese
FROM roles r , estados e
where r.estado=e.id order by desr asc";
	$resultado = $mysqli->query($query);
	
	$pdf = new PDF();
	$pdf->AliasNbPages();
	$pdf->AddPage();
	
	//texto

	$pdf->MultiCell(190,6,'Reporte de Roles',0,'C');
	$pdf->MultiCell(190,6,'',0,'C');
	$pdf->MultiCell(190,6,'',0,'C');
	$pdf->SetFillColor(232,232,232);
	$pdf->SetFont('Arial','B',12);
	$pdf->Cell(40,6,'ID',		1,0,'C',1);
	$pdf->Cell(80,6,'Nombre',	1,0,'C',1);
	$pdf->Cell(70,6,'Estado',		1,1,'C',1);
	

	$pdf->SetFont('Arial','',10);
	
	while($row = $resultado->fetch_assoc())
	{
		$pdf->Cell(40,6,utf8_decode($row['id']),			1,0,'C');
		$pdf->Cell(80,6,$row['desr'],						1,0,'C');
		$pdf->Cell(70,6,utf8_decode($row['dese']),			1,1,'C');
	}
	$pdf->Output();
?>