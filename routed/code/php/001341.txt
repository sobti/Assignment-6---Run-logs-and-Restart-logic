<?php

// use Carbon\Carbon;

class Post extends Eloquent
{
    protected $table = 'posts';

    protected $fillable = array('title', 'boday');

    public static $rules = array(
    	'title'    => 'required|min:10|max:100',
    	'body'     => 'required|max:10000',
    	'image'    => 'image'
    );

   

	public function user()
	{
		return $this->belongsTo('User');
	}
}