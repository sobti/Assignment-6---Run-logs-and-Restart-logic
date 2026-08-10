<?php

namespace App;

use Illuminate\Database\Eloquent\Model;

class Course extends Model
{
  public function school()
  {
      return $this-> belongsTo('App\School');
  }

  public function roster()
  {
      return $this->hasMany('App\Roster');
  }

  public function instructorDay1()
  {
    return $this->belongsTo('App\Instructor', 'instructor_day_1');
  }
  public function instructorDay2()
  {
    return $this->belongsTo('App\Instructor', 'instructor_day_2');
  }
  public function instructorDay3()
  {
    return $this->belongsTo('App\Instructor', 'instructor_day_3');
  }
  public function instructorDay4()
  {
    return $this->belongsTo('App\Instructor', 'instructor_day_4');
  }
}
