<?php


namespace App\Models;


use Illuminate\Database\Eloquent\Model;

class UserProfile extends Model
{

    protected $table = 'users_profile';
    protected $hidden = ['id', 'user_id'];
    protected $fillable = [
        'uuid',
        'user_id',
        'member_id',
        'grade',
        'title',
        'marital_status',
        'dob',
        'gender',
        'phone_number',
        'address',
        'city',
        'state',
        'country',
        'postal_address',
        'chapter',
        'sector',
        'sub_sector',
        'occupation',
        'passport'
    ];

    protected $with = ['education', 'experience'];



    public function education()
    {
        return $this->hasOne(Education::class, 'user_id', 'user_id');
    }


    public function experience()
    {
        return $this->hasOne(Experience::class, 'user_id', 'user_id');
    }
}
