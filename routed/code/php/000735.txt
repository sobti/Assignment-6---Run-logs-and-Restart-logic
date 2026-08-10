<?php
namespace App\Models;

use App\Models\Author\Submit;
use Illuminate\Database\Eloquent\Model;

class Category extends Model
{
    public $guarded = [];
    public function sub_categories(){
        return $this->hasMany(Subcategory::class);
    }

    public function submits(){
        return $this->hasMany('App\Models\Author\Submit');
    }
    public function subscribes(){
        return $this->hasMany(Subscribe::class);
    }
    public function editors(){
        return $this->hasMany(Editor::class);
    }
}
