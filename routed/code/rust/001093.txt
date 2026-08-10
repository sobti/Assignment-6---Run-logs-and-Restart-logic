extern crate quote;
#[macro_use]
extern crate synstructure;

use std::collections::HashMap;

use kg_display::fmt::*;
use kg_utils::collections::SparseSet;
use proc_macro2::{Ident, Span};

decl_derive!([Display, attributes(display)] => display_derive);


fn display_derive(mut s: synstructure::Structure) -> proc_macro2::TokenStream {
    fn err_msg<S: Into<String>>(msg: S, v: &synstructure::VariantInfo) -> String {
        use std::fmt::Write;
        let mut msg = msg.into();
        if let Some(p) = v.prefix {
            write!(msg, " for {}::{}", p, v.ast().ident).expect("write failed")
        } else {
            write!(msg, " for {}", v.ast().ident).expect("write failed")
        }
        msg
    }

    let mut fmts = Vec::with_capacity(s.variants().len());

    for ref mut v in s.variants_mut() {
        v.binding_name(|field, i| {
            field.ident.clone().unwrap_or(Ident::new(&format!("_{}", i), Span::call_site()))
        });

        let disp = match find_display_attr(v.ast().attrs) {
            Some(m) => m,
            None => {
                panic!("{}", err_msg("missing display(...) attribute", v));
            }
        };

        if disp.is_empty() {
            panic!("{}", err_msg("empty display(...) attribute", v));
        }

        let params: Vec<(String, String)> = {
            let mut params = HashMap::new();
            for p in disp.iter() {
                if let &syn::NestedMeta::Meta(syn::Meta::NameValue(syn::MetaNameValue { ref path, lit: syn::Lit::Str(ref s), .. })) = p {
                    if let Some(ident) = path.get_ident() {
                        if ident != "fmt" && ident != "alt" {
                            params.insert(ident.to_string(), s.value());
                        }
                    }
                }
            }
            params.into_iter().collect()
        };

        let fmt = match disp.get(0).unwrap() {
            &syn::NestedMeta::Lit(syn::Lit::Str(ref s)) => s.value(),
            &syn::NestedMeta::Meta(syn::Meta::NameValue(syn::MetaNameValue { ref path, lit: syn::Lit::Str(ref s), .. })) => {
                if let Some(ident) = path.get_ident() {
                    if ident == "fmt" {
                        s.value()
                    } else {
                        panic!("{}", err_msg("invalid display(...) attribute format", v));
                    }
                } else {
                    panic!("{}", err_msg("invalid display(...) attribute format", v));
                }
            }
            _ => panic!("{}", err_msg("invalid display(...) attribute format", v)),
        };

        let mut bindings_set: SparseSet<usize> = SparseSet::with_capacity(v.bindings().len());
        let mut params_set: SparseSet<usize> = SparseSet::with_capacity(params.len());

        let fmt_str = FormatString::parse(&fmt).expect(&err_msg("invalid format string", v));
        fmt_str.each_argument(|arg| {
            match *arg {
                Argument::Next => panic!("{}", err_msg("default positional argument found, only named arguments are supported", v)),
                Argument::Index(_) => panic!("{}", err_msg("positional argument found, only named arguments are supported", v)),
                Argument::Name(ref name) => {
                    if let Some((i, _)) = params.iter().enumerate().find(|(_, p)| &p.0 == name) {
                        params_set.insert(i);
                    } else if let Some((i, _)) = v.bindings().iter().enumerate().find(|(_, bi)| bi.binding == name) {
                        bindings_set.insert(i);
                    } else {
                        panic!("{}", err_msg(format!("unknown argument '{}'", name), v));
                    }
                },
            }
            true
        });

        let alt = {
            let fmt = if let Some(fmt) = disp.get(1) {
                match fmt {
                    &syn::NestedMeta::Lit(syn::Lit::Str(ref s)) => Some(s.value()),
                    &syn::NestedMeta::Meta(syn::Meta::NameValue(syn::MetaNameValue { ref path, lit: syn::Lit::Str(ref s), .. })) => {
                        if let Some(ident) = path.get_ident() {
                            if ident == "alt" {
                                Some(s.value())
                            } else {
                                None
                            }
                        } else {
                            None
                        }
                    },
                    _ => None,
                }
            } else {
                None
            };

            if let Some(fmt) = fmt {
                let mut bindings_set: SparseSet<usize> = SparseSet::with_capacity(v.bindings().len());
                let mut params_set: SparseSet<usize> = SparseSet::with_capacity(params.len());

                let fmt_str = FormatString::parse(&fmt).expect(&err_msg("invalid format string", v));
                fmt_str.each_argument(|arg| {
                    match *arg {
                        Argument::Next => panic!("{}", err_msg("default positional argument found, only named arguments are supported", v)),
                        Argument::Index(_) => panic!("{}", err_msg("positional argument found, only named arguments are supported", v)),
                        Argument::Name(ref name) => {
                            if let Some((i, _)) = params.iter().enumerate().find(|(_, p)| &p.0 == name) {
                                params_set.insert(i);
                            } else if let Some((i, _)) = v.bindings().iter().enumerate().find(|(_, bi)| bi.binding == name) {
                                bindings_set.insert(i);
                            } else {
                                panic!("{}", err_msg(format!("unknown argument '{}'", name), v));
                            }
                        },
                    }
                    true
                });
                Some((fmt, fmt_str, bindings_set, params_set))
            } else {
                None
            }
        };

        fmts.push((params, (fmt, fmt_str, bindings_set, params_set), alt));
    }

    let mut fmt_it = fmts.into_iter();
    let display_body = s.each_variant(|v| {
        let fmt_ = fmt_it.next().unwrap();
        let params = fmt_.0;
        let (fmt, _, bset, pset) = fmt_.1;
        if let Some((fmt_alt, _, bset_alt, pset_alt)) = fmt_.2 {
            let args = v.bindings().iter().enumerate().filter_map(|(index, bi)| {
                if bset.contains(&index) {
                    let ref id = bi.binding;
                    Some(quote! { #id = #id })
                } else {
                    None
                }
            });

            let p_args = params.iter().enumerate().filter_map(|(index, p)| {
                if pset.contains(&index) {
                    let id = Ident::new(&p.0, Span::call_site());
                    let value: syn::Expr = syn::parse_str(&p.1).expect(&format!("cannot parse expression: `{}` for parameter '{}'", &p.1, &p.0));
                    Some(quote! { #id = #value })
                } else {
                    None
                }
            });

            let args_alt = v.bindings().iter().enumerate().filter_map(|(index, bi)| {
                if bset_alt.contains(&index) {
                    let ref id = bi.binding;
                    Some(quote! { #id = #id })
                } else {
                    None
                }
            });

            let p_args_alt = params.iter().enumerate().filter_map(|(index, p)| {
                if pset_alt.contains(&index) {
                    let id = Ident::new(&p.0, Span::call_site());
                    let value: syn::Expr = syn::parse_str(&p.1).expect(&format!("cannot parse expression: `{}` for parameter '{}'", &p.1, &p.0));
                    Some(quote! { #id = #value })
                } else {
                    None
                }
            });

            quote! {
                if f__.alternate() {
                    write!(f__, #fmt_alt #(, #args_alt)* #(, #p_args_alt)*)
                } else {
                    write!(f__, #fmt #(, #args)* #(, #p_args)*)
                }
            }
        } else {
            let args = v.bindings().iter().enumerate().filter_map(|(index, bi)| {
                if bset.contains(&index) {
                    let ref id = bi.binding;
                    Some(quote! { #id = #id })
                } else {
                    None
                }
            });

            let p_args = params.iter().enumerate().filter_map(|(index, p)| {
                if pset.contains(&index) {
                    let id = Ident::new(&p.0, Span::call_site());
                    let value: syn::Expr = syn::parse_str(&p.1).expect(&format!("cannot parse expression: `{}` for parameter '{}'", &p.1, &p.0));
                    Some(quote! { #id = #value })
                } else {
                    None
                }
            });

            quote! {
                write!(f__, #fmt #(, #args)* #(, #p_args)*)
            }
        }
    });

    let p = s.gen_impl(quote! {
        extern crate std;

        gen impl std::fmt::Display for @Self {
            #[allow(unused_variables)]
            fn fmt(&self, f__: &mut std::fmt::Formatter) -> std::fmt::Result {
                match *self {
                    #display_body
                }
            }
        }
    });

    p
}


fn find_display_attr(attrs: &[syn::Attribute]) -> Option<Vec<syn::NestedMeta>> {
    let doc_path: syn::Path = syn::Ident::new("doc", Span::call_site()).into();

    let mut disp = None;
    for attr in attrs {
        if attr.path != doc_path && attr.style == syn::AttrStyle::Outer {
            let disp_meta = {
                let m = attr.parse_meta();
                if let Ok(syn::Meta::List(syn::MetaList { path, nested, .. })) = m {
                    if let Some(ident) = path.get_ident() {
                        if ident == "display" {
                            Some(nested.into_iter().collect())
                        } else {
                            None
                        }
                    } else {
                        None
                    }
                } else {
                    None
                }
            };
            if disp_meta.is_some() & &disp.is_some() {
                panic!("multiple display(...) attributes found")
            } else {
                disp = disp_meta;
            }
        }
    }
    disp
}
