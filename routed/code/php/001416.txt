<?php


namespace App\Services;


class Calculator
{
    public static function variationFromTwoValues(float $valueOld, float $actualValue): float
    {
        $value = (($actualValue * 100) / $valueOld) - 100;
        return round($value, 2);
    }
}
