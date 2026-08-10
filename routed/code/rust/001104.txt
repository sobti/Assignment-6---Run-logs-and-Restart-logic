use hello::HelloMacro;
use hello_macro::HelloMacro;

#[derive(HelloMacro)]
struct Pancakes;

#[test]
fn pancakes() {
    assert_eq!("Hello, Macro! My name is Pancakes", Pancakes::hello_macro());
}
