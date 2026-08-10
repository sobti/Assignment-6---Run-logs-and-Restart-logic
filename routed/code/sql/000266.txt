Use T_Gufos
SELECT * FROM Categorias order by IdCategoria asc
SELECT * FROM Eventos
SELECT * FROM Usuarios
SELECT * FROM Presencas

SELECT E.* , C.*
FROM Eventos as E
JOIN Categorias AS C
ON E.IdCategorias = C.IdCategoria



SELECT P.* , U.* , E.*
FROM Presencas P
JOIN Usuarios U
ON  P.IdEvento = U.IdUsuario
JOIN Eventos E 
ON P.IdEvento = E.IdEvento

SELECT P.*, U.*, E.*, C.*
FROM Presencas p 
INNER JOIN Usuarios U 
ON P.IdUsuario = U.IdUsuario
INNER JOIN Eventos E
ON p.IdEvento = E.IdEvento
INNER JOIN Categorias C
ON E.IdCategorias = C.IdCategoria