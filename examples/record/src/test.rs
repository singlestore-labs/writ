#[prelude_import]
use std::prelude::rust_2018::*;
#[macro_use]
extern crate std;
mod record {
    pub struct Bar {
        pub name: String,
        pub age: i32,
    }
    pub struct DeepBar {
        pub id: i32,
        pub x: Bar,
    }
    impl ::core::clone::Clone for DeepBar {
        #[inline]
        fn clone(&self) -> DeepBar {
            match *self {
                DeepBar {
                    id: ref __self_0_0,
                    x: ref __self_0_1,
                } => DeepBar {
                    id: ::core::clone::Clone::clone(&(*__self_0_0)),
                    x: ::core::clone::Clone::clone(&(*__self_0_1)),
                },
            }
        }
    }
    pub struct Foo {
        pub movies: Vec<String>,
        pub code: Vec<i32>,
        pub bars: Vec<Bar>,
        pub b: Vec<bool>,
    }
    #[automatically_derived]
    #[allow(unused_qualifications)]
    impl ::core::clone::Clone for Foo {
        #[inline]
        fn clone(&self) -> Foo {
            match *self {
                Foo {
                    movies: ref __self_0_0,
                    code: ref __self_0_1,
                    bars: ref __self_0_2,
                    b: ref __self_0_3,
                } => Foo {
                    movies: ::core::clone::Clone::clone(&(*__self_0_0)),
                    code: ::core::clone::Clone::clone(&(*__self_0_1)),
                    bars: ::core::clone::Clone::clone(&(*__self_0_2)),
                    b: ::core::clone::Clone::clone(&(*__self_0_3)),
                },
            }
        }
    }
    impl std::fmt::Debug for Foo {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.debug_struct("Foo")
                .field("movies", &self.movies)
                .field("code", &self.code)
                .field("bars", &self.bars)
                .field("b", &self.b)
                .finish()
        }
    }
}

struct Record;
use crate::record::Bar;
use crate::record::DeepBar;
use crate::record::DeeperBar;
use crate::record::Foo;
impl record::Record for Record {
    fn test_record(a: Bar) -> i32 {
        a.age
    }
    fn test_deep_record(a: DeepBar) -> i32 {
        a.x.age
    }
    fn test_deeper_record(a: DeeperBar) -> i32 {
        a.x.x.age
    }
    fn construct_bar(name: String, age: i32) -> Bar {
        Bar {
            name: name,
            age: age,
        }
    }
    fn bar(a: Bar) -> Bar {
        Bar {
            name: a.name.clone(),
            age: a.age + 10,
        }
    }
    fn deep_bar(a: Bar) -> DeepBar {
        DeepBar {
            id: 1,
            x: Self::bar(a),
        }
    }
    fn deeper_bar(a: Bar) -> DeeperBar {
        DeeperBar {
            id: 2,
            x: Self::deep_bar(a),
        }
    }
    fn rev_deeper_bar(a: DeeperBar) -> DeeperBar {
        DeeperBar {
            id: a.id + 2,
            x: a.x,
        }
    }
    fn foo() -> Foo {
        Foo {
            movies: <[_]>::into_vec(box ["star wars 1".to_string(), "star wars 2".to_string()]),
            code: <[_]>::into_vec(box [99, 98, 97]),
            bars: ::alloc::vec::Vec::new(),
            b: <[_]>::into_vec(box [true, false, true]),
        }
    }
    fn test_foo(a: Foo) -> Foo {
        Foo {
            movies: a.movies.into_iter().rev().collect(),
            code: (&a.code[1..]).to_vec(),
            bars: a.bars.iter().map(|x| Self::bar(x)).collect::<Vec<Bar>>(),
            b: a.b,
        }
    }
}