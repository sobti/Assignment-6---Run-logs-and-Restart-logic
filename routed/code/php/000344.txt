<?php

namespace Database\Seeders;

use App\Models\Buku;
use Illuminate\Database\Seeder;

class BukuSeeder extends Seeder
{
    public function run()
    {
        (new Buku([
            'kode' => 'B0001',
            'judul' => 'Ten Years Challenge',
            'jml_halaman' => 178,
            'isbn' => '10299293',
            'pengarang' => 'Mutiarini',
            'tahun_terbit' => 2020,
        ]))->save();
        (new Buku([
            'kode' => 'B0002',
            'judul' => 'Kisah Tanah Jawa: Tikungan Maut',
            'jml_halaman' => 200,
            'isbn' => '10092993',
            'pengarang' => 'kisahtanahjawa',
            'tahun_terbit' => 2019,
        ]))->save();
        (new Buku([
            'kode' => 'B0003',
            'judul' => 'Rapijali',
            'jml_halaman' => 257,
            'isbn' => '290399100',
            'pengarang' => 'Dee Lestari',
            'tahun_terbit' => 2021,
        ]))->save();
        (new Buku([
            'kode' => 'B0004',
            'judul' => 'The Pragmatic Programmer: Your Journey to Mastery',
            'jml_halaman' => 560,
            'isbn' => '01929944',
            'pengarang' => 'Andrew Hunt, David Thomas',
            'tahun_terbit' => 2020,
        ]))->save();
        (new Buku([
            'kode' => 'B0005',
            'judul' => 'HTML and CSS: Design and Build Websites',
            'jml_halaman' => 482,
            'isbn' => '1092990393',
            'pengarang' => 'Jon Duckett',
            'tahun_terbit' => 2020,
        ]))->save();
        (new Buku([
            'kode' => 'B0006',
            'judul' => 'Nusantara',
            'jml_halaman' => 671,
            'isbn' => '019929922',
            'pengarang' => 'Bernard H. M. Vlekke',
            'tahun_terbit' => 2020,
        ]))->save();
    }
}
