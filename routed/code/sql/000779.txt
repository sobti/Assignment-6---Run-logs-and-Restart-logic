CREATE TABLE menu (
kode_makanan_minuman INT PRIMARY KEY AUTO_INCREMENT,
nama_makanan_minuman VARCHAR(60) NOT NULL, 
harga_makanan_minuman INT NOT NULL,
diskon DOUBLE

)ENGINE = INNODB;

CREATE TABLE pesanan (
id_pesanan VARCHAR(11) NOT NULL,
kode_makanan_minuman INT,
nomor_meja INT(2),
jumlah INT(3),

CONSTRAINT fk_kode_makanan_minuman FOREIGN KEY (`kode_makanan_minuman`) REFERENCES `menu`(`kode_makanan_minuman`),
CONSTRAINT fk_nomor_meja FOREIGN KEY (`nomor_meja`) REFERENCES `pelanggan`(`nomor_meja`)

)ENGINE=INNODB;

ALTER TABLE menu ADD jenis_makanan_minuman INT(2) NOT NULL  

CREATE TABLE broadcast_pesanan(
id_broadcast INT PRIMARY KEY AUTO_INCREMENT,
id_pesanan VARCHAR(15),
id INT(11) DEFAULT 0,
`status` INT(2), 

FOREIGN KEY (`id`) REFERENCES users(id)

)ENGINE=INNODB;

ALTER TABLE menu ADD jenis_makanan_minuman INT(2) NOT NULL  

