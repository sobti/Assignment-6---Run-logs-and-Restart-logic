<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateWpngWoocommerceShippingZoneMethodsTable extends Migration
{
    /**
     * Run the migrations.
     *
     * @return void
     */
    public function up()
    {
        Schema::create('wpng_woocommerce_shipping_zone_methods', function (Blueprint $table) {
            $table->unsignedBigInteger('zone_id');
            $table->bigIncrements('instance_id');
            $table->string('method_id', 200)->nullable();
            $table->unsignedBigInteger('method_order');
            $table->boolean('is_enabled')->default(1);
        });
    }

    /**
     * Reverse the migrations.
     *
     * @return void
     */
    public function down()
    {
        Schema::dropIfExists('wpng_woocommerce_shipping_zone_methods');
    }
}
