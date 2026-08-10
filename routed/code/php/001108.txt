<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\BlogController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

Route::get('blog', [BlogController::class, 'index']);
Route::get('blog/{param}', [BlogController::class, 'show']);
Route::get('search/{title}', [BlogController::class, 'search']);
Route::post('blog', [BlogController::class, 'store']);
Route::put('blog/{id}', [BlogController::class, 'update']);
Route::delete('blog/{id}', [BlogController::class, 'destroy']);