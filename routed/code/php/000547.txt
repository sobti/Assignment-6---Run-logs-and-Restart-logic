<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreatePelanggansTable extends Migration
{
    /**
     * Run the migrations.
     *
     * @return void
     */
    public function up()
    {
        Schema::create('pelanggans', function (Blueprint $table) {
            $table->increments('id');
            $table->string('name');
            $table->bigInteger('code_pelanggan');
            $table->bigInteger('nomor_telepon');
            $table->string('jenis_kelamin');
            $table->bigInteger('nomor_kk');
            $table->integer('id_dusun');
            $table->text('alamat');
            $table->timestamps();
            
        });
    }

    public function down()
    {
        Schema::dropIfExists('pelanggans');
    }
}
