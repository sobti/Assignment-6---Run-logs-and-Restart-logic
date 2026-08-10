module List

fun length x = match x { | [] -> 0 | _:xs -> 1 + length xs }
fun map f x = match x {
    | [] -> []
    | x:xs -> f x : map f xs
}
fun append x y = match x {
    | [] -> y
    | x:xs -> x : append xs y
}
fun reverse x = match x {
    | [] -> []
    | x:xs -> append (reverse xs) [x]
}
fun filter p x = match x {
    | [] -> []
    | x:xs ->
        if p x then
            x : filter p xs
        else
            filter p xs
}

/*
fun length x =
    if x == [] then
        0
    else
        1 + length (tl x)

fun map f x =
    if x == [] then []
    else f (hd x) : map f (tl x)

fun append x y =
    if x == [] then y
    else (hd x) : append (tl x) y

fun reverse x =
    if x == [] then []
    else append (reverse (tl x)) [hd x]

fun filter p x =
    if x == [] then []
    else if p (hd x) then
        (hd x) : filter p (tl x)
    else filter p (tl x)
*/
